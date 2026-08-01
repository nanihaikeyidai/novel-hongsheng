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

## 短剧视觉风格（全局强制）

- 本工程后续所有图片修改均直接覆盖原图片文件，保持原路径与原文件名；不得另建 `_v2`、`_v3`、`修正版` 等版本图片。覆盖前须确认目标路径准确，版本回溯依赖 Git 历史或既有外部备份。
- 王老师固定为女性：30岁的漂亮高三班主任兼语文教师，年轻知性、优雅端庄，保持成年教师的可信度与威严。所有人设、分镜和视频生成统一使用 `05-images/人物/王老师_30岁美女教师_日漫四格_v3.png` 锁定身份，严禁生成男性、学生形象或男性化体态。

处理 `05-workflow/`、`05-images/` 及所有短剧故事板、场景图、道具图、视频Prompt时，必须先读取 `01-docs/短剧视觉风格规范.md`，并遵守以下不可变规则：

- 全项目统一为高精度日漫电影感，不得生成摄影写实、真人照片、欧美漫画、低幼卡通、厚涂油画或3D渲染质感。
- 用户口头所称“新海诚风格”，执行时统一转写为可操作特征：细腻赛璐璐人物、手绘动画背景、通透空气透视、电影级雨光、玻璃雨痕、湿地反射、蓝灰环境光和克制的高光辉光；不依赖作者姓名维持风格。
- 人物身份与画风以 `05-images/人物/林明_人设四格.png`、`05-images/人物/林晓_人设四格.png` 为首要基准；不得自行改变五官、发型、体型、校服版型和年龄感。
- 教室标准场景为 `05-images/场景/场景_雨天教室含同学_日漫电影感.png`；不得退回晴天空教室或摄影写实版本。
- 第一章教室段必须保持阴雨天气、冷蓝灰漫射光、窗面雨滴、城市雨雾及普通同学群像；除剧情明确变化外，不得改成晴天、暖阳或空教室。
- 普通同学使用同一套日漫赛璐璐语言，但不得复刻主角脸、红发绳、红绳或其他身份标志。
- 故事板仍遵循“叙事画面黑白灰＋彩色制作标注”；最终视频与正式场景图则使用本节规定的彩色日漫电影感。两者不得混淆。
- 每次生图前在Prompt中明确写出风格基准和禁止项；生成后检查人物身份、天气、群演密度、空间结构与画风，任一项跑偏必须主动报告。

## 关联 Skills

- `../skills/chinese-novelist-skill/` — 小说创作流程
- `../skills/novel-to-audiobook-skill/` — 文本转有声剧本（旧版 VoxCPM 流程参考）
