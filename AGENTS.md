# 《红绳》项目 — AI 协作规范

> 仓库：[nanihaikeyidai/novel-hongsheng](https://github.com/nanihaikeyidai/novel-hongsheng)

## 项目路径

| 项 | 路径 |
|---|---|
| 项目根 | `D:\HermesWorkspace\ai小说\红绳` |
| 成稿 | `02-manuscript/chapters/` |
| 有声书 | `04-audiobook/` |
| MOSS-TTS | `D:\HermesWorkspace\MOSS-TTS\.venv\Scripts\python.exe` |
| TTS 模型 | `D:\HermesWorkspace\models\MOSS-TTS-Local-Transformer-v1.5` |
| 通用 Skills | `D:\HermesWorkspace\ai小说\skills\` |

## 目录约定

| 目录 | 用途 |
|---|---|
| `00-source/` | 原始素材，只读参考 |
| `01-docs/` | 大纲、人设、计划 |
| `02-manuscript/` | 章节成稿（Markdown / PDF / HTML） |
| `03-intermediate/` | 早期草稿，勿直接当最终稿 |
| `04-audiobook/` | 有声剧本 JSON + MOSS-TTS 生成脚本 |
| `05-images/` | 人物立绘生成脚本（本地，未入库） |

## 有声书工作流

1. 章节 Markdown → `scripts/convert_chapter_to_audiobook_json.py` → `*_有声小说.json`
2. 人工 review → `scripts/fix_chapter1_json.py`（按需）
3. 生成音频：

```cmd
cd D:\HermesWorkspace\ai小说\红绳\04-audiobook
scripts\generate_ch01.bat
```

或 Demo（前 5 行）：

```cmd
D:\HermesWorkspace\MOSS-TTS\.venv\Scripts\python.exe scripts\generate_moss_tts_audiobook.py --indices "0-4"
```

## 环境要求

- Python 3.12（MOSS-TTS venv）
- NVIDIA GPU，显存 ≥ 12 GB
- HuggingFace 镜像（可选）：`set HF_ENDPOINT=https://hf-mirror.com`

环境自检：`D:\HermesWorkspace\MOSS-TTS\.venv\Scripts\python.exe scripts/setup.py`

## AI 协作规则

- 修改章节正文 → 只动 `02-manuscript/chapters/`
- 修改有声剧本 → 对应 `04-audiobook/chXX_*/` 下的 JSON
- 角色音色映射 → `04-audiobook/scripts/generate_moss_tts_audiobook.py` 的 `DEFAULT_VOICE_MAP`
- 生成的大音频（wav/mp3）已在 `.gitignore`，勿提交
- 中文交流；代码注释可用中文

## 关联 Skills

- `../skills/chinese-novelist-skill/` — 小说创作流程
- `../skills/novel-to-audiobook-skill/` — 文本转有声剧本（旧版 VoxCPM 流程参考）
