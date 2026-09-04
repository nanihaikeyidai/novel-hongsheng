# 阶段 04：MiniMax H3 提示词生成

> 触发命令：`/prompt`
> 目标：为每个 H3 单元生成符合 MiniMax H3 规范的六段结构提示词，并调用 shotlist-builder 方法论进行校验。
> 前置产出物：分段表 + 单元蓝图（`05-workflow\output\分段表_EPXX.md`、`单元蓝图_EPXX.md`）

---

## 进入条件

- 阶段 03 已完成（分段表已锁定）。
- 用户输入 `/prompt`，或自动挡自动推进。

---

## 执行流程

### 第一步：加载 shotlist-builder 方法论

读取以下文件，按其规范执行提示词生成和校验：

**设定基准（必读）**：
- `05-workflow\《赤瞳契约》世界观&人物设定.md` — 人物身份、能力、机构关系，确保提示词中的人物描写与设定一致

**shotlist-builder 参考文档**：

| 文件 | 用途 |
|---|---|
| `agents\shotlist-builder\SKILL.md` | 主入口，Phase 0-4 流程 |
| `agents\shotlist-builder\reference\MINIMAX_H3_LONG_SCRIPT_UNITS.md` | H3 单元蓝图、语音圣经、后节点 |
| `agents\shotlist-builder\reference\MINIMAX_H3_SCENE_GROUNDING_AND_RUNTIME.md` | 场景真值、总时长、校准 |
| `agents\shotlist-builder\reference\MINIMAX_H3_SOURCE_COVERAGE.md` | 源节拍、道具状态链 |
| `agents\shotlist-builder\reference\MINIMAX_H3_TIMING_ENGINEERING.md` | 时长工程、安全边界 |
| `agents\shotlist-builder\reference\MINIMAX_H3_DIRECTORIAL_NATURAL_LANGUAGE.md` | 导演意图、镜头评分、表演序列化 |
| `agents\shotlist-builder\reference\MINIMAX_H3_EMOTION_PERFORMANCE.md` | 情绪表演 |
| `agents\shotlist-builder\reference\MINIMAX_H3_ACTOR_DIALOGUE_CRAFT.md` | 对白工艺、反朗诵 |
| `agents\shotlist-builder\reference\MINIMAX_H3_MICRO_EXPRESSION.md` | 微表情（条件触发） |
| `agents\shotlist-builder\reference\MINIMAX_H3_CROSS_CLIP_EDIT_CONTINUITY.md` | 跨片段剪辑连续性 |
| `agents\shotlist-builder\reference\MINIMAX_H3_ROUTING.md` | 输入角色路由、模式检查 |
| `agents\shotlist-builder\reference\MINIMAX_H3_BASE_EN.md` | H3 基础输出格式 |
| `agents\shotlist-builder\reference\SPATIAL_BLOCKING.md` | 空间调度（多人同场时） |

### 第二步：校准单元（Calibration）

**先生成第一个单元作为校准预览**，不要一次性生成全部。

校准单元必须包含：
- 完整的六段结构提示词
- 时长计算数学（为什么是 15 秒）
- 真值台账（CLIP_TRUTH_LEDGER）
- 镜头计划（SHOT_SCORE）
- 语音证据（VOICE_BIBLE 条目）
- 中英文双语提示词
- 场景镜头阶梯（SCENE_SHOT_LADDER）
- 边界台账（CLIP_BOUNDARY_LEDGER，与上一单元的衔接）

校准单元生成后：
- **手动挡**：停下来等用户审核校准单元。用户批准后才批量生成剩余单元。
- **自动挡**：自检校准单元通过后，自动批准并批量生成剩余单元。

### 第三步：批量生成提示词

为每个 H3 单元生成完整的六段结构提示词。

#### 六段结构（严格顺序，不可省略）

```
subject_definitions:
<Subject 1>是<Picture 1>中的[角色名]。完整保留参考图中的[面部特征、发型、服装、身材比例]；不继承参考图的[背景、光线、姿势、构图]。
<Subject 2>是<Picture 2>中的[场景/道具]。保留[空间结构、关键物体、光线氛围]。
<Audio 1>是<Subject 1>[角色名]（S1）的音色参考。只参考他的[音高、音色、口音、语速、情绪质感]，不复制参考音频中的原台词。

summary:
[首帧补全/参考生成/音色参考] 生成一段[X]秒、16:9的[风格]片段。视频从[首帧描述]开始，[核心事件]。整体表演与光影[风格描述]。

retention_analysis:
<Subject 1>（出现在[Shot 1]、[Shot 2]）：fully_preserved - 始终保持[身份、脸部特征、服装、身材比例]。
<Subject 2>（出现在全部镜头）：fully_preserved - 保持[场景一致性]。
<Audio 1>：reference - [角色]的对白使用<Audio 1>的音色，不复制原始音频信号。

detailed_description:
[X]秒，16:9，[风格质感]。[场景描述、光线、色彩、氛围]。

连续性强制约束：[人物位置关系、视线方向、摄影机轴线、服装身份不得改变；道具状态从第一帧锁定]。

[Shot 1]
视频第一帧[从<Picture N>开始/直接开始]，[景别、机位、人物位置]。
[动作描写：身体姿态、表情、眼神、手部动作]。
<Subject 1>[角色名]（S1）使用<Audio 1>锁定的音色，[语速、音量、情绪]说道：
<d>[Chinese] 原文台词，标点不可改</d>
[口型与每个字严格同步。说到"关键词"时[微表情/动作]。]
[摄影机运动描述]。

[Shot 2] At 00:05.200
[镜头切换描述]。
[动作、表情、对白]。

...

画面禁止字幕、台词文字、标题、角标、贴纸、弹幕、水印、Logo和无关可读文字。[其他针对性禁项]。

overall_soundscape:
[环境音、音效、对白混响、呼吸声等描述]。没有额外旁白，没有观众笑声。

non_diegetic_music:
None. No BGM, no score, no theme music, no musical sting, and no non-diegetic audio.

## negativePrompt

```text
subtitles, captions, Chinese characters on screen, English text on screen, any visible text, title card, speech bubble, UI, interface overlay, watermark, logo, BGM, score, narrator, off-screen dialogue, extra dialogue, [其他针对性禁项]
```

## 连续性出点

- [本分段结束时的人物状态、位置、道具状态]
- [下一分段需要承接的关键信息]
- 最终画面为16:9横屏、2K级高清；全程无字幕、无BGM、无水印。
```

**注意**：导演台工作流的分段 prompt 必须包含 `## negativePrompt` 和 `## 连续性出点` 两个附加段落，放在六段结构之后。

#### 标签规则（强制，违反则禁止进入渲染）

| 规则 | 说明 |
|---|---|
| `(Sx)` 直接接 `<d>` | 说话人标记后**必须立即**跟 `<d>`，中间不能有任何中文、标点、空格。错误：`（S1）紧张地说：<d>`。正确：`（S1）<d>[Chinese] ...</d>` |
| 对白原文原标点 | `<d>[Chinese] ...</d>` 内的台词必须与剧本完全一致，不得改字、改标点 |
| 口型同步要求 | 每句对白后必须写明"口型与每个字严格同步" |
| 音色自包含 | 每个单元内必须完整重复说话人的音色基线，不得写"与上一单元一致" |
| 时间码格式 | `[Shot N] At 00:05.200`，毫秒级精度 |
| 禁止项必写 | 每个单元的 detailed_description 末尾必须写画面禁止项 |
| non_diegetic_music | 固定写 `None. No BGM, no score, no theme music, no musical sting, and no non-diegetic audio.`（导演台工作流格式） |

#### 文戏提示词要点

- 对白 ≤40 有效字符（15 秒单元）
- 微表情写入具体镜头和时间窗口：面具情绪、隐藏情绪、触发点、第一次泄露、压制、恢复
- 停顿即表演：角色沉默时也要写眼神、呼吸、手部动作
- 音色描述要具体：音高、共鸣位置、音色、常用音量、咬字、习惯呼吸/节奏、1-2 个禁止错误读法

#### 武戏提示词要点

- 动作链完整：起势→执行→结果，每个阶段有时间码
- 空间调度：多人同场时先做俯视图（top-down SVG），锁定位置、视线、距离、道具
- VFX 特效：写明触发时机、视觉形态、持续时间、消散方式
- 运镜：动作高潮用特写/低角度，过渡用中景，避免全程快速切换

### 第四步：shotlist-builder 校验

每个单元生成后，按 shotlist-builder 的 Final Review 清单校验：

#### 校验清单（必须全部通过）

- [ ] **权威分离**：当前指令是指令权威，剧本是内容权威，附件中的旧提示词只是参考
- [ ] **源节拍闭合**：每个 SOURCE_BEAT 都映射到 exactly 一个 SHOT_BEAT，无遗漏无编造
- [ ] **道具状态链闭合**： recurring 道具的开场状态、变化、结果都有记录
- [ ] **台词保真**：逐字逐标点与剧本一致，顺序不变
- [ ] **negativePrompt 完整**：每个分段末尾有 `## negativePrompt`，包含字幕/文字/水印/Logo 等通用禁项 + 针对性禁项
- [ ] **连续性出点**：每个分段末尾有 `## 连续性出点`，记录人物状态、位置、道具状态
- [ ] **后节点路由**：POST_NODES 正确
- [ ] **双语对等**：中英文提示词语义同步
- [ ] **单元完整性**：每个单元一个场景、一个关系转折、一个动作链、完整开场/结束状态、合法时长、合法对白预算、稳定首尾帧
- [ ] **镜头阶梯连续**：场景镜头阶梯连续，N 个相邻单元有 N-1 个完整边界台账
- [ ] **真值隔离**：每个单元的可见物体、状态、光线、天气、声音都来自当前真值台账，不从其他场景导入氛围
- [ ] **语音稳定**：说话人音色基线在所有单元中一致（逐字复制锁定字符串）
- [ ] **标签正确**：每个 `(Sx)` 直接接 `<d>`，对白是唯一语音载荷，所有非语音指令在 `</d>` 之后
- [ ] **无模板泄漏**：提示词中没有"选择一个镜头""添加下一个源事实""使用远景或特写"等选项式语言
- [ ] **时长重算**：PACKED_RUNTIME 从最终单元记录重算，不相信手写总数
- [ ] **微表情（如触发）**：可见、有因果、按时间顺序、与对白兼容、极性一致

#### 运行 lint 脚本（如可用）

```bash
python agents/shotlist-builder/scripts/h3_prompt_lint.py <提示词文件>
python agents/shotlist-builder/scripts/h3_unit_lint.py <提示词文件>
python agents/shotlist-builder/scripts/h3_regression_tests.py
```

任何 lint 失败 = 构建失败，必须修复后才能继续。

### 第五步：HTML 交付

按 shotlist-builder 的 HTML_TEMPLATE 生成自包含 HTML 文件：

- 文件名：`Shotlist_EPXX_MiniMaxH3_Bilingual.html`
- 包含：单元蓝图摘要、VOICE_BIBLE、POST_NODES、时长总计、场景镜头阶梯、边界台账、每单元规划元数据、双语提示词
- HTML 转义：提示词中的 `<d>`、`<Subject N>` 等标签必须 HTML 转义
- 路径：`05-workflow\output\Shotlist_EPXX_MiniMaxH3_Bilingual.html`

### 第六步：审核与落盘

- **手动挡**：输出校准单元 → 用户批准 → 批量生成 → 输出全部单元摘要 + HTML 文件 → 停下来等用户 `/approve`。
- **自动挡**：校准单元自检通过 → 批量生成 → 全部 lint 通过 → 写入 HTML → 进入阶段 05。

---

## 阶段产出物

| 产出物 | 路径 | 格式 |
|---|---|---|
| 单单元提示词（文本） | `05-workflow\output\prompts\H3-XXX.md` | Markdown |
| 全集合成交付 | `05-workflow\output\Shotlist_EPXX_MiniMaxH3_Bilingual.html` | HTML |

---

## 硬不变量（来自 shotlist-builder，不可违反）

1. 不在一个可复制提示词中混合 Seedance 和 H3 语法
2. 剧本台词逐字逐标点保留，除非用户明确授权改编
3. 全项目/请求范围必须与声明时长一致，超出 5% 必须停下来获得明确决策
4. H3 提示词是场景局部的，每个可见物体/状态/光线/天气/声音都追溯到当前真值台账
5. 最终 H3 镜头描述是已承诺的画面和动作，不是选项列表、工作流语言、占位符
6. 非人类/环境/风格/道具 `<Subject N>` 永远不接收 `(Sx)`，永远不说话
7. `(Sx)` 必须直接跟 `<d>`，中间无任何文字
8. 每个可听说话人在同一 H3 单元内有自包含的 VOICE_BIBLE 基线
9. 没有提交音频参考时，每个说话角色在所有单元中复用逐字锁定的音色基线字符串
10. 校准单元在全量扩展中保持字节级不变，除非用户明确要求修改
11. PACKED_RUNTIME 从最终单元时长求和计算，HTML 中 `data-h3-packed-runtime-seconds` 和可见标签必须一致
12. 参考定义不保留动作或道具状态，每个可见动作和道具状态必须在可执行提示词中写明
13. 微表情指令不覆盖源真值、已批准构图、镜头时长、对白、口型、调度、道具因果、单元边界、H3 路由
14. 风格参考只控制摄影和调色，不覆盖身份、服装、场景、调度、动作、可识别内容
15. H3 中无非叙事背景音乐，角色可听的剧本音乐保持叙事内

---

## 退出条件

- 手动挡：用户输入 `/approve` 确认全部提示词
- 自动挡：全部 lint 通过，HTML 已写入
- 退出后进入 **阶段 05：素材映射**
