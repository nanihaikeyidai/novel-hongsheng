"""在部署说明.md 追加「本地 Ref2VA 实测通过」章节。

在 fix_deploy_doc.py 跑过之后执行；幂等，重复运行不会重复追加。
"""
from pathlib import Path

P = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\EP04_H3金鱼工作流本地部署说明.md")
MARK = "## 八、本地 Ref2VA 实测通过（2026-10-18）"

SECTION = MARK + """

结论：金鱼工作流的 **Ref2VA（音色参考 + 中文台词）能力已在本地跑通**，
红绳项目的 H3 六段提示词协议可以原样在本地 8188 执行，不需要任何改写。

实测参数与结果：

| 项 | 值 |
|---|---|
| 输入 | ep04/红绳片段09c 的真实提示词 6395 字 + 老韩.wav 音色参考 |
| task_type | `Ref2VA` |
| audio_mode | `reference_only` + `add_source_as_reference=True` + `drive_audio` 接参考音频 |
| 分辨率 / 时长 | 768×448（32 整除）/ 121 帧 |
| 加速 | turbo 4 步 LoRA + `MiniMaxH3MultiRateSamplerEXPT8`（video 4 / audio 10） |
| 耗时 | **120 秒**（对照 RH 同段 430–585 秒） |
| 产出 | 768×448@24fps h264 + aac 32kHz 立体声，5.17 秒 |
| 画面验收 | 赛璐璐平涂、灰蓝冷调、陆沉在左老韩在右、桌面温水准偏左汉堡偏右 —— 全部符合 |

关键的三处接线（缺一不可）：

```python
cond['task_type']        = 'Ref2VA'        # 否则 T2VA 拒绝参考媒体
cond['ref_audios.ref_audio_0'] = ['20', 0]  # AUTOGROW 扁平键名 + 长度 2 列表
cond['drive_audio']      = ['20', 0]       # reference_only 模式下必填
cond['add_source_as_reference'] = True      # 把 drive_audio 作为官方 <Audio N> 参考
cond['audio_mode']       = 'reference_only' # 只锁音色，不锁定源音频 latent
cond['prompt_primary_audio_ordinal'] = 1    # 对齐提示词里的 <Audio 1>
```

`audio_mode=reference_only` 会强制要求 `drive_audio`（否则报
`Audio mode reference_only requires drive_audio`）—— 这是本轮最后一个卡点，
把参考音频同时接到 `ref_audios` 和 `drive_audio` 即可，两个入口互不冲突。

可复现脚本：`scripts/local_h3_ref2va_test.py`（读真实项目提示词 → 提交本地 8188 → 轮询出片）。

### 性能结论：本地已可承担成片重渲

同段对比：

- RunningHub 金鱼：430–585 秒/段（约 8 分钟）
- 本地 Ref2VA：**120 秒/段**，免费、素材不出本机

按 15 秒/段算，本地渲一集 26 段约 52 分钟，RH 约 3.5 小时且要 2400+ 币。
**双通道分工可以明确下来**：RH 只用于改一版就出结果的分镜验证，
正式成片全部走本地。
"""


def main() -> None:
    s = P.read_text(encoding="utf-8")
    if MARK in s:
        print("章节已存在，跳过")
        return
    s = s.rstrip() + "\n\n" + SECTION
    P.write_text(s, encoding="utf-8")
    print(f"已追加实测章节，文档共 {len(s)} 字")


if __name__ == "__main__":
    main()
