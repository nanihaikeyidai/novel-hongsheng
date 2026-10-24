"""修订 EP04_H3金鱼工作流本地部署说明.md 的 AUTOGROW / task_type 章节。

依据本地 8188 实测（task ac5bdab5-a2aa-486e-b374-05804b5fe4e0 等 6 次提交），
原文把 ref_audios 写成字典嵌套值，与实际可用的 API 格式不符，本脚本就地改正。
"""
from pathlib import Path

P = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\EP04_H3金鱼工作流本地部署说明.md")

OLD_AUDIO = """```python
{'20': {'class_type': 'LoadAudio', 'inputs': {'audio': '老韩.wav'}}}
{'6':  {'class_type': 'MiniMaxH3AudioConditioningT8',
        'inputs': {'ref_audios': {'ref_audio_0': [['20', 0]]},   # ← 注意是字典、且序号从 0 开始
                   'strict_prompt_tags': True,
                   'prompt_primary_audio_ordinal': 1, ...}}}
```"""

NEW_AUDIO = """```python
{'20': {'class_type': 'LoadAudio', 'inputs': {'audio': '老韩.wav'}}}
{'6':  {'class_type': 'MiniMaxH3AudioConditioningT8',
        'inputs': {'ref_audios.ref_audio_0': ['20', 0],   # ← 扁平键名 + 长度 2 列表，不嵌套
                   'task_type': 'Ref2VA',                  # ← 接了参考媒体就必须切 Ref2VA/Hybrid
                   'audio_mode': 'reference_only',
                   'strict_prompt_tags': True,
                   'prompt_primary_audio_ordinal': 1, ...}}}
```"""

OLD_AUTOGROW = """### ⚠️ AUTOGROW 列表：字典格式 + 序号从 0 开始

`ref_audios` / `ref_images` / `ref_videos` / `ref_video_audios` 都是
`COMFY_AUTOGROW_V3` 类型，**必须写成字典**，且**序号从 0 开始**：

```python
'ref_audios': [['20', 0]]                      # ✗ 普通列表，静默失效
'ref_audios': {'ref_audio_1': [['20', 0]]}     # ✗ 序号从 1 开始，会被忽略
'ref_audios': {'ref_audio_0': [['20', 0]]}     # ✓ 官方示例写法
```

前缀要照源码 `nodes.py` 的 `io.Autogrow.TemplatePrefix(..., prefix="ref_audio_")` 抄
（`ref_audio_` / `ref_image_` / `ref_videos` / `ref_video_audios`），键名是**前缀 + 从 0 起的序号**。

**这类错误不报错**，节点直接当没接媒体，症状是提示词里明明写了 `<Audio 1>` 却报
`available audio count is 0`。排查办法：直接看官方示例工作流里的
`ref_audios.ref_audio_0` 字样，别猜。"""

NEW_AUTOGROW = """### ⚠️ AUTOGROW 列表：API 提交必须用「扁平键名 + 长度 2 列表」

`ref_audios` / `ref_images` / `ref_videos` / `ref_video_audios` 在节点签名里是
`COMFY_AUTOGROW_V3` 动态列表（源码 `io.Autogrow.TemplatePrefix(..., prefix="ref_audio_")`，
前缀依次为 `ref_audio_` / `ref_image_` / `ref_video_` / `ref_video_audio_`，序号从 0 起）。

**但通过 `/prompt` 提交时，不能按前端 JSON 的字典形态写**，必须是扁平键名：

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
`<Audio 1>` 却报 `available audio count is 0`。排查时直接看官方示例工作流里的
`ref_audios.ref_audio_0` 字样，别猜。

### ⚠️ 接了参考媒体 → task_type 必须离开 T2VA

媒体标签校验通过后还有一道任务类型检查：

```
T2VA cannot include reference media; use Auto or Hybrid
```

`MiniMaxH3AudioConditioningT8.task_type` 的可选值是
`auto / T2VA / I2VA / FL2VA / L2VA / Ref2VA / Hybrid`，默认值是 `auto`，
但从旧工作流继承下来的 JSON 里可能残留 `T2VA`，此时接 `ref_audios` 必报上面这句。

带音色参考（等价于金鱼的 Ref2VA 能力）应显式设：

```python
'task_type': 'Ref2VA',
'audio_mode': 'reference_only',   # 只当音色参考，不锁定源音频 latent
'prompt_primary_audio_ordinal': 1 # 与提示词里 <Audio 1> 对齐
```

### 其他已实测的本地硬约束

| 项 | 值 | 说明 |
|---|---|---|
| 分辨率 | 宽高须被 **32** 整除 | 768×432 报错；16:9 请用 768×448 或 832×480 |
| LoRA 路径 | Windows 必须**反斜杠** | `h3\\xxx.safetensors`，正斜杠报 value_not_in_list |
| 主模型 | `minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors` | 示例里的 `minimax_h3_fl2va_int8_convrot.safetensors` 本地不存在 |
| 输出节点 | 探针工作流需真正 `output_node: true` | 用 `ModelPassThrough` 会报 `prompt_no_outputs` |
| 音频引用 | 必须是 input/ 目录下的文件名 | 外部路径要先复制进 `ComfyUI/input/` |
| USE_TF | 必须设 `USE_TF=0` | 否则 TorchScript 报错 |

验证脚本：`scripts/local_h3_ref2va_test.py`（读 ep04 真实提示词 + 老韩.wav 提交本地 8188）。"""


def main() -> None:
    s = P.read_text(encoding="utf-8")
    for old, new in ((OLD_AUDIO, NEW_AUDIO), (OLD_AUTOGROW, NEW_AUTOGROW)):
        if old not in s:
            raise SystemExit(f"未命中待替换片段：{old[:40]}…")
        s = s.replace(old, new)
    P.write_text(s, encoding="utf-8")
    print(f"已更新 {P}（{len(s)} 字）")


if __name__ == "__main__":
    main()
