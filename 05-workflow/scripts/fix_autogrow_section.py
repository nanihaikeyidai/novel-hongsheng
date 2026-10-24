"""就地替换部署说明.md 中的 AUTOGROW 章节（按标题定位，避开脆弱的全文字面匹配）。"""
from pathlib import Path

P = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\EP04_H3金鱼工作流本地部署说明.md")

HEAD = "### ⚠️ AUTOGROW 列表：字典格式 + 序号从 0 开始"
TAIL = "## 七、和 RunningHub 双通道的取舍"

NEW = """### ⚠️ AUTOGROW 列表：API 提交必须用「扁平键名 + 长度 2 列表」

`ref_audios` / `ref_images` / `ref_videos` / `ref_video_audios` 在节点签名里是
`COMFY_AUTOGROW_V3` 动态列表（源码 `io.Autogrow.TemplatePrefix(..., prefix="ref_audio_")`，
前缀依次为 `ref_audio_` / `ref_image_` / `ref_video_` / `ref_video_audio_`，序号从 0 起）。

**但通过 `/prompt` 提交时，不能按前端 JSON 的字典形态写**，必须扁平化：

```python
'ref_audios': [['20', 0]]                       # ✗ 普通列表：静默失效
'ref_audios': {'ref_audio_1': [['20', 0]]}      # ✗ 序号从 1 起：被 sorted_autogrow_items 忽略
'ref_audios': {'ref_audio_0': [['20', 0]]}      # ✗ 多包一层：Bad linked input, must be a length-2 list
'ref_audios.ref_audio_0': [['20', 0]]           # ✗ 同上
'ref_audios.ref_audio_0': ['20', 0]             # ✓ 通过媒体标签校验
```

要点三条：
1. 键名扁平化：`ref_audios.` + 前缀 + 序号，直接挂在 inputs 顶层；
2. 值是**长度 2 的列表** `[节点id, 输出序号]`，不能嵌套；
3. 序号从 **0** 开始（`sorted_autogrow_items` 用 `key.rsplit("_",1)[-1]` 取序号）。

前四种错法**都不报「格式错误」**，节点直接当没接媒体，症状是提示词里明明写了
`<Audio 1>` 却报 `available audio count is 0`。

实测确认：最后一行提交后，节点 `MiniMaxH3AudioConditioningT8` 的报错回包里
`current_inputs` 已出现真实波形（`tensor([[[-3.05e-05, ...]]], sample_rate: 22050`），
说明 LoadAudio 确实执行并绑上了。

### ⚠️ 接了参考媒体 → task_type 必须离开 T2VA

媒体标签校验通过后还有一道任务类型检查：

```
T2VA cannot include reference media; use Auto or Hybrid
```

`task_type` 可选值 `auto / T2VA / I2VA / FL2VA / L2VA / Ref2VA / Hybrid`，默认 `auto`，
但从旧工作流继承的 JSON 里常残留 `T2VA`，此时接 `ref_audios` 必报上面这句。
带音色参考应显式设 `task_type='Ref2VA'`。

### ⚠️ audio_mode=reference_only 强制要求 drive_audio

```
Audio mode reference_only requires drive_audio
```

把参考音频**同时**接到 `ref_audios` 和 `drive_audio` 两个入口即可，互不冲突；
再打开 `add_source_as_reference=True`，该开关的官方说明就是
「Presents drive_audio to Qwen/DiT as an official <Audio N> reference」，
正对本项目的 `<Audio 1>` 音色锁定。

### 其他已实测的本地硬约束

| 项 | 值 | 说明 |
|---|---|---|
| 分辨率 | 宽高须被 **32** 整除 | 768×432 报错；16:9 请用 768×448 或 832×480 |
| LoRA 路径 | Windows 必须**反斜杠** | `h3\\xxx.safetensors`，正斜杠报 value_not_in_list |
| 主模型 | `minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors` | 示例里的 `minimax_h3_fl2va_int8_convrot.safetensors` 本地不存在 |
| 输出节点 | 探针工作流需真正 `output_node: true` | 用 `ModelPassThrough` 会报 `prompt_no_outputs` |
| 音频引用 | 必须是 `ComfyUI/input/` 下的文件名 | 外部路径要先复制进去 |
| USE_TF | 必须设 `USE_TF=0` | 否则 TorchScript 报错 |
| ffmpeg 抽帧 | 输出路径先用 ASCII | ffmpeg 对中文输出路径会报 `Could not open file` |

验证脚本：`scripts/local_h3_ref2va_test.py`（读 ep04 真实提示词 + 老韩.wav 提交本地 8188）。

"""


def main() -> None:
    s = P.read_text(encoding="utf-8")
    i = s.find(HEAD)
    j = s.find(TAIL)
    if i < 0 or j < 0 or j <= i:
        raise SystemExit(f"定位失败 head={i} tail={j}")
    s = s[:i] + NEW + s[j:]
    P.write_text(s, encoding="utf-8")
    print(f"已替换 AUTOGROW 章节，文档共 {len(s)} 字")


if __name__ == "__main__":
    main()
