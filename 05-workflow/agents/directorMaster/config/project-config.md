# 红绳项目全局配置

> Director Master 所有阶段的配置基准。修改项目设置只改这个文件。
>
> **文件查找入口**：所有项目文件的位置和用途请查阅 `05-workflow/文件索引.md`。skill 在查找任何文件前应先读文件索引。

---

## 基础信息

| 项 | 值 |
|---|---|
| 项目名 | 红绳漫剧 |
| 类型 | 玄幻校园 / 悬疑调查 / 青春情感 |
| 画幅 | **16:9 横屏**（强制，不可改竖屏） |
| 单段时长 | 10–15 秒（H3 单元，硬上限 15 秒） |
| 生成平台 | **MiniMax H3**（Ref2VA 模式） |
| 视觉风格 | 高精度日漫电影感（新海诚式通透光影、赛璐璐人物、手绘动画背景） |
| 成片要求 | 无字幕、无 BGM、无水印、无 Logo |

---

## 目录路径

所有路径相对于项目根 `D:\HermesWorkspace\ai小说\红绳\`。
**完整文件索引见 `05-workflow/文件索引.md`**，以下为常用路径速查。

| 用途 | 路径 |
|---|---|
| 项目根 | `D:\HermesWorkspace\ai小说\红绳\` |
| 文件索引 | `05-workflow\文件索引.md`（查找文件先读这个） |
| **世界观&人物设定** | `05-workflow\《赤瞳契约》世界观&人物设定.md`（剧情/剧本/提示词的设定基准） |
| 正式剧本 | `02-manuscript\screenplays\红绳_第XX集_*.md` |
| 工作流根 | `05-workflow\` |
| 集数制作目录 | `05-workflow\epXX\`（含该集所有片段和素材） |
| 片段制作目录 | `05-workflow\epXX\红绳片段NN\` |
| 生成产出（中间产物） | `05-workflow\output\` |
| 待剪辑视频 | `05-workflow\video\` |
| 人物参考图 | `05-images\人物\` |
| 场景参考图 | `05-images\场景\` |
| 道具参考图 | `05-images\道具\` |
| 角色音色 | `人物参考音色\` |
| 全局文档 | `05-workflow\全局文档\` |
| H3提示词规范（必读） | `05-workflow\全局文档\工作流规范\H3提示词生成前必读与标签门禁.md` |
| Agents 目录 | `05-workflow\agents\` |
| screenwriter skill | `05-workflow\agents\screenwriter\` |
| shotlist-builder skill | `05-workflow\agents\shotlist-builder\` |
| directorMaster skill | `05-workflow\agents\directorMaster\` |
| ComfyUI 工作流模板 | `05-workflow\agents\【MINIMAX-H3】八月最强文戏-高配版_api.json` |

---

## MiniMax H3 提示词规范（强制）

### 六段结构

每个 H3 提示词必须严格包含以下六个字段，顺序不可变：

```
subject_definitions:   ← <Subject N>、<Picture N>、<Audio N>、<Video N> 定义
summary:               ← 一段式总览（首帧补全/参考生成/音色参考 + 时长 + 风格）
retention_analysis:    ← 每个 Subject/Picture/Audio 的保留级别（fully_preserved / reference）
detailed_description:  ← 逐 Shot 描写，含 [Shot N] At 时间码、动作、对白、口型
overall_soundscape:    ← 环境音、音效、对白混响描述
non_diegetic_music:    ← 固定写 N/A
```

### 标签体系（不可省略）

| 标签 | 用途 | 规则 |
|---|---|---|
| `<Subject N>` | 人物/场景/道具主体定义 | N 从 1 开始，每个单元内独立编号 |
| `<Picture N>` | 参考图绑定 | 与 `<Subject N>` 关联，写明继承项与不继承项 |
| `<Audio N>` | 音色参考 | 写明只参考音色不复制原台词 |
| `<Video N>` | 参考视频（可选） | 用于动作延续或运镜参考 |
| `(Sx)` | 说话人标记 | 紧跟在 `<Subject N>` 后，**必须直接接 `<d>`**，中间不能有任何文字 |
| `<d>[Chinese] ...</d>` | 对白载荷 | 原文台词，标点不可改；口型必须同步 |
| `[Shot N]` | 镜头标记 | 配合 `At 00:05.200` 时间码 |
| `<scenetrans>` | 内部转场（可选） | 用于连续 VO 跨镜头 |

### 标签门禁（进入渲染前必须检查）

- [ ] 每个 `(Sx)` 后面**直接**跟 `<d>`，中间无中文、无标点、无空格
- [ ] 所有对白都在 `<d>[Chinese] ...</d>` 内，原文原标点
- [ ] `subject_definitions` 中定义的每个 `<Subject N>` 都有对应的 `<Picture N>` 或描述
- [ ] `non_diegetic_music` 写完整句子：`None. No BGM, no score, no theme music, no musical sting, and no non-diegetic audio.`（导演台工作流格式）
- [ ] `detailed_description` 中每个 `[Shot N]` 有时间码 `At 00:XX.XXX`
- [ ] 总时长不超过 15 秒
- [ ] 画面禁止项已写入：字幕、台词文字、标题、角标、水印、Logo
- [ ] 每个说话人有完整的音色描述（或 `<Audio N>` 绑定）

---

## 文戏 / 武戏判定规则

| 类型 | 特征 | 提示词侧重 |
|---|---|---|
| **文戏** | 对话为主、情绪推进、人物关系变化、静态或缓慢运镜 | 对白精度、微表情、眼神、停顿、音色质感、口型同步 |
| **武戏** | 动作场面、战斗、追逐、特效、快速剪辑 | 动作连贯性、运镜速度、VFX 特效、空间调度、冲击力 |

判定优先级：
1. 片段中对白占比 > 50% → 文戏
2. 片段中有明确战斗/追逐/特效动作 → 武戏
3. 混合片段按主导元素判定，在分段表中标注 `文戏为主` 或 `武戏为主`

---

## ComfyUI / RunningHub 工作流

| 项 | 值 |
|---|---|
| 默认通道 | **本地 ComfyUI 导演台**（优先） |
| **ComfyUI 安装路径** | `F:\Work-Fisher纯净包2026.8.7\ComfyUI` |
| ComfyUI 服务地址 | `http://127.0.0.1:8188` |
| ComfyUI input 目录 | `F:\Work-Fisher纯净包2026.8.7\ComfyUI\input`（参考图/音频上传到此） |
| ComfyUI output 目录 | `F:\Work-Fisher纯净包2026.8.7\ComfyUI\output`（生成视频输出到此） |
| ComfyUI models 目录 | `F:\Work-Fisher纯净包2026.8.7\ComfyUI\models` |
| **主工作流（导演台）** | `05-workflow\agents\minimax_h3_director_二采_加速.json` |
| 备用工作流（文戏高配） | `05-workflow\agents\【MINIMAX-H3】八月最强文戏-高配版_api.json` |
| RunningHub 工作流 ID | `2090984765787820034`（线上备选） |
| RunningHub URL | `https://www.runninghub.cn/workflow/2090984765787820034?source=workspace` |

### ComfyUI 目录说明

```
F:\Work-Fisher纯净包2026.8.7\ComfyUI\
├── input\          ← 参考图、参考音频上传到此目录，timeline_data 中用文件名引用
├── output\         ← 生成的视频、图片输出到此目录
├── models\
│   ├── unet\       ← MiniMax H3 模型
│   ├── clip\       ← Qwen3-VL CLIP
│   ├── vae\        ← Video VAE / Audio VAE
│   ├── loras\      ← h3\minimax_h3_fl2v_turbo_8step...
│   └── ...
└── custom_nodes\   ← MiniMaxH3Director 等自定义节点
```

**素材上传规则**：提交工作流前，将全局参考图（人物人设图、场景图）和参考音频复制到 `ComfyUI\input\` 目录，timeline_data 中的 `imageFile` / `audioFile` 只写文件名（不含路径）。

### 主工作流：MiniMaxH3Director 导演台（二采加速版）

核心节点 `MiniMaxH3Director`，支持多片段时间线拼接、全局素材共享、跨片段连续性。

| 参数 | 值 |
|---|---|
| task_type | `r2v — 参考主体生视频(Reference to Video)` |
| width / height | `1056 x 608`（16:9） |
| ref_max_size | `1056` |
| frame_rate | `24` |
| steps | `8` |
| sampler | `euler` |
| scheduler | `simple` |
| shift_video | `6` |
| shift_audio | `3` |
| cfg | `1` |
| 加速节点 | `TESpeedMiniMaxH3`（8-step LoRA 模式，mcs=2） |
| LoRA | `h3\minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors`（strength=1） |
| 模型 | MiniMax H3 UNET（节点1） |
| CLIP | Qwen3-VL minimax（节点2） |
| 分段间连续性 | `continuityFromPrev=true`，重叠 22 帧 |
| 分段间清显存 | `clear_vram_between_segments=true` |

#### 时间线数据结构（timeline_data）

工作流通过 `timeline_data` JSON 管理全部片段和素材：

```
timeline_data
├── global                    ← 全局设置
│   ├── prompt                ← 全局素材说明（图片1-N、音频1-N）
│   ├── refs[]                ← 全局参考图（最多5张：人物+场景）
│   ├── refAudios[]           ← 全局参考音频（最多3条）
│   └── output                ← 输出设置（16:9, 0.6mp, continuityEnabled）
├── segments[]                ← 分段数组（每个15秒）
│   ├── prompt                ← 该分段完整提示词（六段结构 + negativePrompt + 连续性出点）
│   ├── negativePrompt        ← 反向提示词
│   ├── refs[]                ← 该分段追加参考图（故事板、首帧等，index从5开始）
│   ├── refAudios[]           ← 该分段追加音频
│   ├── continuityFromPrev    ← 是否承接上一段（true/false）
│   └── refImageSize          ← "match"
└── batchWorkspaces.r2v.segments[]  ← R2V 批量工作区（与 segments 同步）
```

#### 素材编号规则

- **全局参考图**：`图片1`-`图片5`（人物人设图 + 场景图，所有分段共享）
- **分段追加图**：`图片6`+（故事板、首帧、上一段出点图等，仅当前分段）
- **全局音频**：`音频1`-`音频3`（角色音色，所有分段共享）
- **分段追加音频**：分段级 refAudios（较少用）

#### 提示词格式（分段级）

每个分段的 `prompt` 字段包含：

```
【参考素材说明】
图片6：故事板素材
（其他分段级素材说明）

subject_definitions:
<Subject 1> is ... <Picture 1> ...
...

summary:
...

retention_analysis:
...

detailed_description:
Shot 1, 00:00.000–00:02.700 ...
...

overall_soundscape:
...

non_diegetic_music:
None. No BGM...

## negativePrompt
subtitles, captions, ...

## 连续性出点
- 怪兽已完全离场...
```

**注意**：导演台工作流的 `non_diegetic_music` 写 `None. No BGM, no score...`（完整句子），而非简写 `N/A`。

---

## 世界观与人物设定（基准）

**完整文件**：`05-workflow\《赤瞳契约》世界观&人物设定.md`
**使用规则**：剧情探索、剧本生成、提示词生成阶段必须读取此文件，所有人物、机构、能力设定以此为准。

### 核心设定摘要

| 项 | 内容 |
|---|---|
| 题材 | 都市校园 / 悬疑 / 异能智斗 |
| 表层故事 | 校园怪兽袭击事件 |
| 深层主线 | ND 研究所人体实验阴谋 + 地下组织翠羽社的博弈 |

### 核心机构

| 机构 | 对外身份 | 内部真相 |
|---|---|---|
| **ND（自然灾害研究所）** | 官方正义科研机构，研究畸变生物、处理灾害 | 高层掩盖人体实验，追求异能力量，掌握异能移植技术 |
| **翠羽社** | （隐藏）地下反抗组织 | 被 ND 迫害的实验体幸存者组成，目标揭露 ND 黑幕 |

### 关键人物

| 角色 | 身份 | 关键设定 |
|---|---|---|
| **陆沉** | 男主，普通高中生 | 异能"赤瞳"（眼睛变红时发动），母亲陈玥被 ND 灭口，幼年靠 Dark-blood 救活 |
| **林晓** | 女主 | 畸变体袭击目标，陆沉的同班同学 |
| **安娜** | 翠羽社潜伏成员 | 冰山美人，伪装成在校高中生，任务是监视林晓 |
| **王老师** | 30岁女性班主任 | 高三班主任兼语文教师，知性优雅 |
| **陆定天** | 陆沉父亲 | 前特种兵，主动注射 Dark-blood 觉醒异能，翠羽社创建者之一，暗处行动 |
| **陈玥** | 陆沉母亲（已故） | 原 ND 核心研究员，Dark-blood 技术奠基人，被 ND 灭口 |
| **雷斯特** | 翠羽社社长 | 前 ND 高层，被构陷为实验体，获救后建立翠羽社 |

### 关键道具

| 道具 | 说明 |
|---|---|
| **Dark-blood（暗血）** | 陈玥研发的畸变体血液处理物，注入人体可移植/觉醒异能 |
| **赤瞳** | 陆沉的异能，眼睛变红时发动，EP01 救下林晓时能力外泄被 ND 盯上 |

### 叙事规则

- 翠羽社在校园阶段完全隐藏幕后，只派遣潜伏人员（安娜）活动
- 陆沉对自身能力来源和母亲死亡真相一无所知
- 陆定天前期不和陆沉相认，在暗处行动
- ND 对外口径统一为"极端天气/外来生物入侵"，内部知晓畸变体与异能者真相

---

## 视觉风格规范（全局强制）

- 全项目统一**高精度日漫电影感**，禁止摄影写实、真人照片、欧美漫画、低幼卡通、厚涂油画、3D 渲染
- "新海诚风格"转写为可操作特征：细腻赛璐璐人物、手绘动画背景、通透空气透视、电影级雨光、玻璃雨痕、湿地反射、蓝灰环境光、克制高光辉光
- 人物身份基准：`05-images\人物\陆沉_人设四格.png`、`05-images\人物\林晓_人设四格.png`
- 王老师固定为女性：30 岁漂亮高三班主任兼语文教师，使用 `05-images\人物\王老师_30岁美女教师_日漫四格_v3.png`
- 教室标准场景：`05-images\场景\场景_雨天教室含同学_日漫电影感.png`
- 故事板用"叙事画面黑白灰 + 彩色制作标注"；最终视频和正式场景图用彩色日漫电影感

---

## 已完成集数状态

| 集数 | 状态 | 备注 |
|---|---|---|
| EP01 | 已完成 | 不再作为默认处理对象 |
| EP02 | 已完成主体 | 片段 07–10 需用新版剧本重新生成 |
| EP03 | 剧本完成 | 待制作 |
| EP04 | 剧本完成 | 待制作 |
| EP05 | 剧本完成 | 待制作 |

---

## 关联 Skills 调用方式

| Skill | 调用方式 | 用途 |
|---|---|---|
| `screenwriter` | 读取 `agents\screenwriter\SKILL.md` 后按其方法论执行 | 剧本编写、场景开发、对白打磨、结构审计 |
| `shotlist-builder` | 读取 `agents\shotlist-builder\SKILL.md` 后按其 Phase 流程执行 | 提示词校验、分镜拆解、H3 单元蓝图、lint 检查 |

**注意**：这两个 skill 是本地文件型 skill，不是可调用工具。Director Master 的执行方式是读取它们的 SKILL.md 和参考文档，然后在对话中按其方法论指导 AI 执行对应阶段的工作。
