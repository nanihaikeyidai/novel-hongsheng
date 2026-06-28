# 04-audiobook - MOSS-TTS 生成方案

本项目最终决定使用 **MOSS-TTS-Local-Transformer-v1.5** 作为多角色有声书合成引擎，配合角色参考音色进行 zero-shot 音色克隆。

## 目录结构

```
04-audiobook/
├── ch01_红绳伞/                     # 章节目录
│   ├── 红绳_第01章_有声小说.json    # 有声剧本（narration + dialogue）
│   ├── 红绳_第01章_moss_tts.wav     # 完整合成音频（生成后）
│   ├── 红绳_第01章_moss_tts.mp3
│   ├── 红绳_第01章_moss_tts_meta.json
│   └── 红绳_第01章_moss_tts_segments/  # 单段 WAV
├── 参考音色/                         # 角色参考音频
├── scripts/
│   └── generate_moss_tts_audiobook.py  # 主生成脚本
├── README_moss_tts.md                # 本文档
└── scripts/old/                      # 旧版测试脚本归档
```

## 运行环境

- Python 3.12
- 激活 `D:\HermesWorkspace\MOSS-TTS\.venv`
- 依赖已随 MOSS-TTS 仓库安装（transformers==5.0.0、torchaudio 等）
- 需要 NVIDIA GPU，推荐显存 ≥ 12 GB
- 如果 huggingface.co 访问不畅，运行前设置：

```cmd
set HF_ENDPOINT=https://hf-mirror.com
```

## 快速开始

### 1. 生成完整第一章

```cmd
cd D:\HermesWorkspace\ai小说\红绳\04-audiobook
D:\HermesWorkspace\MOSS-TTS\.venv\Scripts\python.exe scripts\generate_moss_tts_audiobook.py
```

输出到 `ch01_红绳伞/`：
- `红绳_第01章_moss_tts.wav`
- `红绳_第01章_moss_tts.mp3`
- `红绳_第01章_moss_tts_meta.json`
- `红绳_第01章_moss_tts_segments/`

### 2. 只生成 Demo（例如前 5 行）

```cmd
python scripts\generate_moss_tts_audiobook.py --indices "0-4"
```

### 3. 指定输出目录/文件名

```cmd
python scripts\generate_moss_tts_audiobook.py --output-dir D:\tmp --output-name 红绳_ch01_demo
```

## 角色音色配置

在 `scripts/generate_moss_tts_audiobook.py` 中修改 `DEFAULT_VOICE_MAP`：

```python
DEFAULT_VOICE_MAP = {
    "旁白":   "旁白.wav",
    "林明":   "青年林明.wav",   # 高中时代
    "林晓":   "青年林晓.wav",
    "李想":   "李想.wav",
    "王老师": "王老师.wav",
    # ... 其他角色
}
```

- 第一章（高中时代）使用 `青年林明`、`青年林晓`。
- 后续章节如涉及小学回忆，可切换到 `小学林明`、`小学林晓`。
- 未配置的角色会自动 fallback 到 `旁白`。

## 参考音频要求

- 格式：WAV（单声道/立体声均可）
- 脚本会自动：
  - 重采样到模型采样率（48 kHz）
  - 转为单声道计算后输入
  - 裁剪到前 `max-ref-sec` 秒（默认 12 秒）
- 推荐每个参考音频 5–12 秒，音质干净、无背景音乐。

## 脚本主要参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--chapter-dir` | `ch01_红绳伞` | 章节目录 |
| `--json` | 自动查找 `*_有声小说.json` | 剧本文件 |
| `--model-dir` | `D:\HermesWorkspace\models\MOSS-TTS-Local-Transformer-v1.5` | TTS 模型 |
| `--ref-dir` | `参考音色` | 参考音频目录 |
| `--indices` | `all` | 行号范围，如 `0,5-10` |
| `--max-ref-sec` | `12` | 参考音频裁剪秒数 |
| `--max-group-chars` | `180` | 同角色连续台词合并上限 |
| `--no-mp3` | 否 | 不转换 MP3 |

## 常见问题

### 生成卡住或极慢

1. 检查是否有之前的 Python 进程占用显存：
   ```cmd
   nvidia-smi
   ```
2. 若发现 lingering python.exe，结束它后再运行。
3. 关闭其他占用显存的大型程序（如游戏、浏览器硬件加速视频）。

### 角色说话不像

- 检查参考音频是否与角色性别、年龄匹配。
- 缩短参考音频到最像角色的 5–10 秒片段。
- 确保参考音频无背景音乐、噪声。

## 旧脚本说明

根目录下的 `run_*.py`、`test_*.py`、`trim_refs.py` 等是早期调试脚本，路径和方案已过时，已归档到 `scripts/old/`。

## 下一步

- 为其他章节复制 `scripts/generate_moss_tts_audiobook.py`，修改 `--chapter-dir` 和 `--output-name` 即可。
- 如需批量处理整本书，可再写一个 `batch_generate.py` 调用本脚本。
