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

## 成片画幅规范（强制）

- **最终视频统一 16:9 横屏**：提示词【画面质感】写 `16:9横屏，2K级高清`；竖版参考图转横屏用两侧模糊延伸填充版，不裁主体。
- 分镜/九宫格固定 16:9 横版；成片无字幕（后期统一添加）、无BGM、无水印。
- 每次新建、续写或修改 MiniMax H3 提示词前，必须完整读取 `05-workflow/全局文档/工作流规范/H3提示词生成前必读与标签门禁.md` 列出的全部规范和当前片段资料。Ref2VA 主提示词强制使用六段结构及 `<Subject N>`、`<Picture N>`、`<Audio N>`、`<Video N>`、`(Sx)`、`<d>[Chinese] ...</d>` 标签；标签缺失、冲突或未解析时禁止写入 RunningHub。
- 工作流：后续《红绳》视频生产默认调用 RunningHub 线上 MiniMax H3 工作流 `2096059277453643778`（`https://www.runninghub.cn/workflow/2096059277453643778`）。线上不可用或调用失败时停止并报告，禁止自动退回本地；只有用户明确说明使用本地时，才允许调用本地 ComfyUI（8188）。线上任务以该工作流的最新线上版本为准，本地 `F:\ComfyUI_V6.0\MiniMax H3 导演台全能工作流红绳_api.json` 只作结构核对，不得自行作为回退任务运行。每次重新绑定图片、故事板、首尾帧、音频或视频素材时，必须重新读取实际素材并按工作流当前顺序重建素材描述、唯一用途、继承项与不继承项，同步全局与片段提示词；禁止复用上一片段或旧绑定的素材描述、标签和编号。每个片段的 `negativePrompt` 是必填规则字段，禁止为空；固定禁止字幕、画面文字、中文字符、标题卡、气泡、UI、水印和 Logo，并按当前片段重新生成其他针对性禁项，同时同步两个片段数组。该工作流使用多素材时间线拼接：新素材必须作为新片段追加，保留已有片段及其素材、描述和提示词，不得覆盖；后续片段启用 `continuityFromPrev=true`，并同步追加到 `timeline_data.segments` 与 `timeline_data.batchWorkspaces.r2v.segments`，利用相邻片段的帧间过渡。实际生成仍强制执行每段 15 秒、16:9 横屏、2K级高清、无字幕、无BGM、无水印；turbo 4STEPS LoRA 与 pruned 模型不匹配时默认关闭 LoRA。
- 中文交流；代码注释可用中文

## 短剧剧本定位规则

- EP01–EP03 的正式剧情正文唯一来源为 `02-manuscript/screenplays/红绳_第XX集_*.md`；片段目录内的旧 `本片段剧本.md` 只作历史参考，不得作为后续修改的权威来源。
- 使用 `05-workflow/剧本片段关联总表.md`、各集 `剧本片段索引.md` 和片段目录内 `剧本定位.md` 从制作片段定位正式剧本。
- 正式剧本增删段落后运行 `05-workflow/scripts/update_script_segment_links.ps1`，刷新行号和40个定位卡。
- 修改剧情中的动作、台词、人物、场景、道具、入点或出点后，依次复核镜头表、片段划分、视频提示词、故事板/首帧、素材描述与 `negativePrompt`；若改变片段出点，所有受影响的后续片段连续性重新验证。
## 短剧片段归档规则

- 整集跨片段连续性统一由 `05-workflow/output/ep01_v2/分镜连续性总控.md` 和 `分镜连续性总表.json` 管控；任何片段分镜、状态台账和视频提示词都不得自行重定义上一片段出点。上一片段未登记审核状态、正式故事板路径和哈希时，不得生成下一片段正式故事板。多主体同场还必须通过固定世界坐标、占位半径、支撑面、移动原因、碰撞和轴向顺序校验。
- 后续所有已经用户审核通过的短剧文件，统一存入 `05-workflow/output/ep01_v2/片段归档/红绳片段N/` 对应片段目录。
- 审核通过的文件包括但不限于：剧本、故事板、人物/场景/道具参考图、视频提示词、参考音色和最终交付文件。
- 工作过程中的原始文件、草稿和既有目录保持原位，不得因归档而移动或删除；归档目录保存审核通过的交付副本。
- 新增归档文件时同步更新对应片段的 `素材清单.md`，保证提示词中的 `@图片N`、`@音频N` 与目录内文件一一对应。

## 短剧视觉风格（全局强制）

- 本工程后续所有图片修改均直接覆盖原图片文件，保持原路径与原文件名；不得另建 `_v2`、`_v3`、`修正版` 等版本图片。覆盖前须确认目标路径准确，版本回溯依赖 Git 历史或既有外部备份。
- 王老师固定为女性：30岁的漂亮高三班主任兼语文教师，年轻知性、优雅端庄，保持成年教师的可信度与威严。所有人设、分镜和视频生成统一使用 `05-images/人物/王老师_30岁美女教师_日漫四格_v3.png` 锁定身份，严禁生成男性、学生形象或男性化体态。

处理 `05-workflow/`、`05-images/` 及所有短剧故事板、场景图、道具图、视频Prompt时，必须先读取 `01-docs/短剧视觉风格规范.md`，并遵守以下不可变规则：

- 全项目统一为高精度日漫电影感，不得生成摄影写实、真人照片、欧美漫画、低幼卡通、厚涂油画或3D渲染质感。
- 用户口头所称“新海诚风格”，执行时统一转写为可操作特征：细腻赛璐璐人物、手绘动画背景、通透空气透视、电影级雨光、玻璃雨痕、湿地反射、蓝灰环境光和克制的高光辉光；不依赖作者姓名维持风格。
- 人物身份与画风以 `05-images/人物/陆沉_人设四格.png`、`05-images/人物/林晓_人设四格.png` 为首要基准；不得自行改变五官、发型、体型、校服版型和年龄感。
- 教室标准场景为 `05-images/场景/场景_雨天教室含同学_日漫电影感.png`；不得退回晴天空教室或摄影写实版本。
- 后续生成故事板、九宫格或单格分镜图时，必须加载当前剧情地点对应的场景参考图；建筑结构、空间布局、天气、光线、破坏状态和整体色彩以场景图为准。若缺少必需场景图，先生成并确认场景素材，再制作正式分镜。
- 第一章教室段必须保持阴雨天气、冷蓝灰漫射光、窗面雨滴、城市雨雾及普通同学群像；除剧情明确变化外，不得改成晴天、暖阳或空教室。
- 普通同学使用同一套日漫赛璐璐语言，但不得复刻主角脸、红发绳、红绳或其他身份标志。
- 故事板仍遵循“叙事画面黑白灰＋彩色制作标注”；最终视频与正式场景图则使用本节规定的彩色日漫电影感。两者不得混淆。
- 每次生图前在Prompt中明确写出风格基准和禁止项；生成后检查人物身份、天气、群演密度、空间结构与画风，任一项跑偏必须主动报告。

## 关联 Skills

- `../skills/chinese-novelist-skill/` — 小说创作流程
- `../skills/novel-to-audiobook-skill/` — 文本转有声剧本（旧版 VoxCPM 流程参考）
- `$storyboard-continuity`（`C:/Users/Administrator/.codex/skills/storyboard-continuity/`）— 分镜生成、修改和审核前后，逐格记录并校验人物、主体、位置、动作与环境状态；跨片段首格必须承接上一片段末格。
- `$redstring-minimax-drama-prompt`（`.agents/skills/redstring-minimax-drama-prompt/`）— 将《红绳》文戏拆成 MiniMax 10–15 秒视频单元，并校验对白预算、口型、声线、参考素材与跨片段连续性。
