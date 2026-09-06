# 阶段 06：工作流调用（本地 ComfyUI / RunningHub 云端）

> 触发命令：`/render`（默认本地）、`/rh` 或 `/render rh`（云端 RunningHub）
> 目标：将已通过校验的 H3 提示词和绑定素材组装为 `timeline_data`，提交到 MiniMaxH3Director 导演台工作流，批量生成视频片段。
> 前置产出物：提示词 + 素材映射表
> 云端操作详细指南：`references/runninghub-guide.md`
> 插件技术参考：`references/minimax-h3-director-guide.md`

---

## 导演台插件核心能力（速查）

本项目使用 **MiniMax H3 Director** 插件（[AIMixer/ComfyUI_MiniMaxH3_Director](https://github.com/AIMixer/ComfyUI_MiniMaxH3_Director)），核心能力：

| 能力 | 红绳项目用法 |
|---|---|
| **r2v 参考主体模式** | 固定使用，公共参数=全局素材，素材组=分段 |
| **公共参数** | 全局参考图≤5张 + 全局音频≤3条 + 全局素材说明 |
| **素材组** | 每个15秒片段=一个素材组，追加故事板为图片6+ |
| **段间引导** | `continuityFromPrev=true`，上下文22帧，实现分段连续性 |
| **二采 Refine** | 工作流已外接，8步一采 + 精修，输出 `images`（终稿）和 `images_pre_refine`（一采） |
| **原生音频** | 同时接 video_vae + audio_vae，自动生成立体声音频 |
| **选择运行** | 可只跑勾选的分段，便于调试 |

**模型硬约束**：CLIP type 必须选 `minimax`；r2v 必须用 `ref2va` UNET；必须同时接 video_vae 和 audio_vae。

---

## 进入条件

- 阶段 05 已完成（所有素材已绑定，映射表已确认）。
- 用户输入 `/render`，或自动挡自动推进。

---

## 执行流程

### 第一步：渲染前最终检查

提交前必须完成以下检查，任何一项不通过则禁止提交：

#### 提示词检查

- [ ] 每个分段的六段结构完整（subject_definitions / summary / retention_analysis / detailed_description / overall_soundscape / non_diegetic_music）
- [ ] 所有 `(Sx)` 直接接 `<d>`，中间无文字
- [ ] 所有对白在 `<d>[Chinese] ...</d>` 内，原文原标点
- [ ] `non_diegetic_music` 写完整句子：`None. No BGM, no score, no theme music, no musical sting, and no non-diegetic audio.`
- [ ] 每个分段时长 10-15 秒，Shot 时间码连续
- [ ] 每个分段末尾有 `## negativePrompt` 和 `## 连续性出点`
- [ ] 画面禁止项已写入 negativePrompt（字幕、文字、水印、Logo 等）

#### 素材检查

- [ ] 全局参考图（图片1-5）已确认：人物人设图 + 场景图
- [ ] 全局参考音频（音频1-3）已确认：主要角色音色
- [ ] 分段追加参考图（图片6+）已确认：故事板、首帧、上一段出点图
- [ ] 每个 `<Picture N>` 在提示词中有对应的素材说明
- [ ] 每个 `<Audio N>` 在提示词中有对应的音色说明
- [ ] 全局参考图 ≤5 张，全局参考音频 ≤3 条

#### 工作流参数检查

- [ ] task_type = `r2v — 参考主体生视频(Reference to Video)`
- [ ] 分辨率 1056x608（16:9）
- [ ] 帧率 24fps
- [ ] steps=8, sampler=euler, scheduler=simple
- [ ] 分段间 continuityFromPrev 设置正确（第一段 false，后续 true）
- [ ] 总帧数 = 各分段帧数之和（15秒=362帧，5秒=124帧）

### 第二步：组装 timeline_data

这是导演台工作流的核心输入。将所有分段和素材组装为一个 JSON 对象。

#### 结构总览

```json
{
  "version": 5,
  "editMode": "segment",
  "totalFrames": <总帧数>,
  "frameRate": 24,
  "video": { ... },
  "global": {
    "taskType": "r2v — 参考主体生视频(Reference to Video)",
    "prompt": "<全局素材说明>",
    "refs": [ <全局参考图数组，最多5张> ],
    "refAudios": [ <全局参考音频数组，最多3条> ],
    "commonEnabled": true,
    "output": {
      "mode": "fixed",
      "aspectRatio": "16:9 (宽屏)",
      "megapixels": 0.6,
      "multiple": 32,
      "longEdge": 1056,
      "width": 1056,
      "height": 608,
      "continuityEnabled": true,
      "continuityOverlapFrames": 22,
      "refImageSize": "match"
    }
  },
  "segments": [ <分段数组> ],
  "timelineMode": "prompt_batch",
  "width": 1056,
  "height": 608,
  "refMaxSize": 1056,
  "batchWorkspaces": {
    "r2v": {
      "segments": [ <与 segments 同步的 R2V 工作区分段> ]
    }
  }
}
```

#### 全局素材说明（global.prompt）

```
subject_definitions:
图片1：[角色A]角色人设图，[外貌、服装描述]。
图片2：[角色B]角色人设图，[外貌、服装描述]。
图片3：[角色C]角色人设图，[外貌、服装描述]。
图片4：[角色D]角色人设图，[外貌、服装描述]。
图片5：[场景名]场景图，[空间结构、光线、天气描述]。

音频1：[角色A]
音频2：[角色B]
音频3：[角色C]
```

#### 全局参考图（global.refs）

```json
[
  {"index": 0, "imageFile": "林晓_人设.png", "type": "input", "subfolder": ""},
  {"index": 1, "imageFile": "陆沉_人设.png", "type": "input", "subfolder": ""},
  {"index": 2, "imageFile": "安娜_人设.png", "type": "input", "subfolder": ""},
  {"index": 3, "imageFile": "王老师_人设.png", "type": "input", "subfolder": ""},
  {"index": 4, "imageFile": "场景_雨天教室.png", "type": "input", "subfolder": ""}
]
```

#### 全局参考音频（global.refAudios）

```json
[
  {"index": 0, "audioFile": "林晓.wav", "durationSec": 4.0},
  {"index": 1, "audioFile": "陆沉.wav", "durationSec": 3.7},
  {"index": 2, "audioFile": "王老师.wav", "durationSec": 3.5}
]
```

#### 分段结构（segments[]）

每个分段对应一个 15 秒视频单元：

```json
{
  "id": "msmp44em3oasd",
  "start": 0,
  "length": 362,
  "frameCount": 362,
  "durationSec": 15,
  "prompt": "【参考素材说明】\n图片6：故事板素材\n\n\nsubject_definitions:\n...\n\n## negativePrompt\n\n```text\n...\n```\n\n## 连续性出点\n\n- ...",
  "negativePrompt": "",
  "taskType": "",
  "refs": [
    {"index": 5, "imageFile": "故事板.png", "type": "input", "subfolder": ""}
  ],
  "refAudios": [],
  "refVideos": [],
  "genImage": {"imageFile": "", "fileName": ""},
  "continuityFromPrev": false,
  "refImageSize": "match"
}
```

**分段关键字段**：
- `start`：起始帧（累计）
- `length` / `frameCount`：帧数（15秒=362帧，24fps）
- `durationSec`：时长秒数
- `prompt`：完整提示词（六段结构 + negativePrompt + 连续性出点）
- `refs`：分段追加参考图（index 从 5 开始，因为 0-4 是全局图）
- `continuityFromPrev`：第一段 `false`，后续分段 `true`

#### 帧数计算

- 15 秒 @ 24fps = 360 帧，工作流实际使用 362 帧（含 2 帧余量）
- 5 秒 @ 24fps = 120 帧，工作流实际使用 124 帧
- 总帧数 = 所有分段 length 之和

### 第三步：选择渲染通道并提交

根据用户指定的渲染通道选择本地或云端。**用户未指定时默认本地 ComfyUI**；用户输入 `/rh`、`/runninghub`、`/cloud` 或说"用 RH/云端生成"时使用 RunningHub。

#### 通道 A：本地 ComfyUI（默认）

1. 确认 ComfyUI 已启动：`http://127.0.0.1:8188`（安装路径：`F:\Work-Fisher纯净包2026.8.7\ComfyUI`，Python 环境：`F:\Work-Fisher纯净包2026.8.7\python\python.exe`）
2. 将全局参考图和参考音频复制到 `F:\Work-Fisher纯净包2026.8.7\ComfyUI\input\` 目录
3. 加载工作流：`agents/minimax_h3_director_二采_加速.json`
4. 将组装好的 `timeline_data` JSON 填入 `MiniMaxH3Director` 节点（节点12）的 `timeline_data` 输入
5. 确认 timeline_data 中的 `imageFile` / `audioFile` 只写文件名（与 input 目录中的文件名一致）
6. 通过 API 提交：`POST http://127.0.0.1:8188/prompt`，body 为 `{"prompt": <工作流JSON>}`
7. 轮询 `GET /history/{prompt_id}` 等待完成
8. 从 output 目录获取视频：`GET /view?filename=<文件名>&subfolder=video&type=output`，或直接从 `F:\Work-Fisher纯净包2026.8.7\ComfyUI\output\video\` 读取

#### 通道 B：RunningHub 云端（用户指定 RH 时）

详细操作流程见 `references/runninghub-guide.md`，核心步骤：

1. 加载 `browser-use-automation` skill，用 `computer_use_tool(plane="bu")` 打开浏览器
2. 导航到工作流：`https://www.runninghub.cn/workflow/2096059277453643778`
3. 检查登录状态，未登录则调用 `interaction.request_action` 请用户手动登录
4. 上传全局参考图（≤5张）和参考音频（≤3条）到工作流对应节点
5. 将 timeline_data JSON 粘贴到 MiniMaxH3Director 节点的 timeline_data 输入框
6. 确认工作流参数（分辨率、帧率、采样步数等）
7. 点击"运行"提交，记录任务 ID
8. 轮询页面状态等待生成完成（每60秒检查一次）
9. 生成完成后下载视频（8bit + 10bit 两个版本），保存到 `05-workflow/epXX/`

**RunningHub 注意事项**：
- 上传素材失败时，调用 `interaction.request_action` 请用户手动上传
- timeline_data 粘贴失败时，检查 JSON 语法或用 `bu.js()` 注入
- 队列等待超过30分钟时，告知用户并询问是否切换本地
- 平台内部错误时，记录错误信息并切换到本地 ComfyUI

#### 批量提交策略

导演台工作流支持**一次性提交全部分段**，工作流内部会按顺序生成，分段间自动做连续性衔接（22帧重叠）。

- **自动挡**：一次性组装全部分段的 timeline_data，提交整个工作流，等待全部完成。
- **手动挡**：可以先提交前 2-3 个分段做校准，用户确认质量后再提交剩余分段。

**注意**：如果分段数量多（>8个），建议分批提交，避免显存不足或生成时间过长。

### 第四步：输出视频管理

生成的视频按以下规则存放：

| 类型 | 路径 | 命名 |
|---|---|---|
| 原始生成视频 | `output/epXX/H3-XXX_raw.mp4` | `H3-XXX_raw.mp4` |
| 审核通过的片段 | `ep0X/视频片段/红绳片段NN.mp4` | `红绳片段NN.mp4` |
| 待剪辑视频 | `video/红绳片段NN.mp4` | `红绳片段NN.mp4` |
| 本地运行记录 | `ep0X/local_runs/` | 按时间戳 |
| timeline_data 备份 | `output/epXX/timeline_data_EPXX.json` | `timeline_data_EPXX.json` |

### 第五步：分段质量检查

每个视频生成后，检查：

- [ ] 时长正确（10-15 秒，误差 ≤0.5 秒）
- [ ] 画面无字幕、无文字、无水印、无 Logo
- [ ] 人物身份与全局参考图一致（无脸崩、无服装漂移）
- [ ] 口型与对白同步（文戏）
- [ ] 动作连贯无瞬移（武戏）
- [ ] 场景与全局参考图一致
- [ ] 音色与全局音频参考一致
- [ ] 分段间连续性：上一段末帧与下一段首帧衔接自然
- [ ] 首尾帧稳定（可用于剪辑衔接）

**不合格处理**：
1. 记录问题类型（提示词问题 / 素材问题 / 模型生成问题 / 连续性问题）
2. 修正对应分段的 prompt 或素材
3. 重新提交该分段（最多 2 次重试）
4. 2 次仍不合格，停下来报告用户

---

## 导演台工作流 vs 文戏高配版

| 维度 | MiniMaxH3Director 导演台（主） | 文戏高配版（备） |
|---|---|---|
| 核心节点 | MiniMaxH3Director（单节点集成） | 分散的 Conditioning+Sampler 节点 |
| 多片段支持 | 时间线拼接，一次提交全部分段 | 每次只能生成一个片段 |
| 全局素材 | 5张图 + 3条音频，全分段共享 | 每片段独立绑定 3图+2音频 |
| 连续性 | 内置 continuityFromPrev + 22帧重叠 | 需手动处理首尾帧 |
| 分辨率 | 1056x608 | 736x416 → 1280x704（二采） |
| 采样 | 8步 euler + TESpeed 加速 | 8+4+4步双pass |
| 适用场景 | 多片段连续制作（红绳主流程） | 单片段高质量精修 |

**默认使用导演台工作流**。文戏高配版仅在单片段需要更高分辨率精修时使用。

---

## 阶段产出物

| 产出物 | 路径 |
|---|---|
| timeline_data JSON | `output/epXX/timeline_data_EPXX.json` |
| 生成的视频片段 | `output/epXX/H3-XXX_raw.mp4` |
| 审核通过的片段 | `ep0X/视频片段/红绳片段NN.mp4` |
| 渲染日志 | `output/epXX/渲染日志_EPXX.md` |

渲染日志记录每个分段的：提交时间、帧数、重试次数、问题记录、最终状态。

---

## 退出条件

- 所有分段渲染完成并通过基础检查
- 手动挡：用户确认全部片段合格
- 自动挡：全部分段渲染完成，自动进入总结
- 退出后进入 **阶段 07：生成总结**
