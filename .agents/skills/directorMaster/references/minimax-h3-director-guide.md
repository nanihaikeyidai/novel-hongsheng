# MiniMax H3 Director 插件用法指南

> 插件仓库：https://github.com/AIMixer/ComfyUI_MiniMaxH3_Director
> 本指南提炼红绳项目实际用到的 r2v 模式、段间引导、二采精修等核心能力，作为阶段06工作流调用的技术参考。

---

## 一、插件概述

**MiniMaxH3Director** 是面向长视频、多段生成的集成导演台节点，把分段计划、条件编码、采样解码和导出整合在一个节点里。底层走官方 MiniMaxH3ReferenceToVideo + MiniMaxH3SigmaShift + KSampler + AV 分离解码链路，原生输出立体声音频。

### 核心输入输出

| 方向 | 端口 | 说明 |
|---|---|---|
| 输入 | `model` | UNET 模型（r2v 用 ref2va） |
| 输入 | `video_vae` | 视频 VAE |
| 输入 | `audio_vae` | 音频 VAE |
| 输入 | `clip` | CLIP（type 必须选 `minimax` / Qwen3-VL） |
| 可选输入 | `r2v_groups` | 外部多组接线（红绳用 UI 内置，不接外部） |
| 可选输入 | `refine` | 二采/放大精修节点 |
| 输出 | `images` | 最终成片（二采后） |
| 输出 | `audio` | 原生立体声音频 |
| 输出 | `fps` | 帧率 |
| 输出 | `frame_count` | 总帧数 |
| 输出 | `source_images` | 时间轴原片（参考图/故事板） |
| 输出 | `report` | 运行报告（分段计划、每段摘要） |
| 输出 | `images_pre_refine` | 一采画面（二采前，便于对比） |

---

## 二、任务模式

| 模式 | 说明 | UNET | 红绳是否使用 |
|---|---|---|---|
| `t2v` | 文生音视频 | fl2va | 否 |
| `i2v` | 图生视频 | fl2va | 否 |
| `fl2v` | 首尾帧生视频 | fl2va | 否 |
| `r2v` | 参考主体生视频（素材组） | **ref2va** | **是（主流程）** |
| `v2v` | 视频转视频 | ref2va | 否 |
| `rv2v` | 参考素材改视频 | ref2va | 否 |

**红绳项目固定使用 r2v 模式**，因为需要多人物/场景/道具参考图 + 故事板 + 音色参考。

---

## 三、r2v 参考主体模式（红绳核心）

### 3.1 公共参数（全局素材）

- 点击「启用公共参数」展开面板（默认折叠）
- 上传**共用参考图（最多9张）**和**共用参考音频（最多3条）**
- 写**公共提示词**（如角色锁定 `subject_definitions`）
- 启用后公共提示词会与每组提示词自动拼接

**红绳映射**：公共参数 = 全局参考图（图片1-5：人物/场景/道具）+ 全局参考音频（音频1-3：音色）+ 全局素材说明。

### 3.2 素材组（分段）

- 点击「添加素材组」，每个素材组对应一个视频分段
- 每组可再挂**本组独有素材**（图片1-9 / 音频1-3 / 视频1-3），同槽位覆盖公共素材
- 每组写分镜提示词（六段结构）
- 提示词中用 `<Picture N>` / `<Video K>` / `<Audio J>` 或 `@` 引用已上传素材

**红绳映射**：每个素材组 = 一个 15 秒片段，组内追加故事板（图片6+）。

### 3.3 时间轴与连续性

- 时间轴预览各组时长与缩略图
- 「选择运行」与素材组勾选同步，可只跑部分分段
- **段间引导（Motion Context）**：默认关闭，多段时可开启
  - 将上一段生成结果的末尾运动（及音频）钉入下一段采样，再裁掉前缀
  - 上下文帧数：5 / 22 / 39 / 56，**默认推荐 22**
  - 红绳项目通过 `continuityFromPrev=true` 实现段间连续性

---

## 四、二采 / 放大（Refine）

外接 **MiniMax H3 Director Refine** 节点到导演台 `refine` 口。未接线 = 单次采样。

### 4.1 三种模式

| 模式 | 说明 | 适用场景 |
|---|---|---|
| `refine` | 同分辨率再采一遍（精修） | 提升画面细节、减少 artifacts |
| `upscale` | 先放大到目标画布再二采 | 低分辨率生成 → 高分辨率输出 |
| `latent_upscale` | 只放大 H3 latent，不二采 | 快速放大，不增加采样成本 |

### 4.2 关键参数

| 参数 | 说明 |
|---|---|
| `passes` | 精修次数，默认 1，最多 9999。upscale 只在第1次放大，后面都是同分辨率精修 |
| `refine_model` | 可选二采 UNET；不接则用导演台主模型。适合一采挂 Turbo LoRA、二采卸掉 |
| `sigmas` | 二采用 SIGMAS，接 `BasicScheduler` 或 `ManualSigmas` |
| `skip_fl2v` | fl2v 默认跳过二采（保护首尾帧）；关掉才会采 |
| `upscale_method` | upscale 时的放大方法：`h3_latent`（3D权重）/ `lanczos`（插值）/ `nvidia_rtx_vsr` |

### 4.3 输出

- `images`：二采后成片（最终输出）
- `images_pre_refine`：一采、放大前的画面（便于对比）
- 「分段导出」且 `passes>1` 时，每轮另落 `seg_XXXX_pN.mp4`
- 「全部导出」只出一采和终稿

**红绳项目**：使用 `minimax_h3_director_二采_加速.json` 工作流，已外接 Refine 节点。

---

## 五、模型配置（硬约束）

| 用途 | 文件名 | 目录 |
|---|---|---|
| UNET (r2v/v2v/rv2v) | `minimax_h3_ref2va_pruned_int8_convrot.safetensors` | `models/diffusion_models/` |
| UNET (t2v/i2v/fl2v) | `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | `models/diffusion_models/` |
| CLIP | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | `models/text_encoders/` |
| Video VAE | `minimax_h3_video_vae_fp16.safetensors` | `models/vae/` |
| Audio VAE | `minimax_h3_audio_vae_fp32.safetensors` | `models/vae/` |

**硬约束**：
- CLIP Loader 的 `type` **必须**选 `minimax`（Qwen3-VL），不能用默认的 stable diffusion
- r2v 模式**必须**用 ref2va UNET，不能用 fl2va
- 必须同时接 video_vae 和 audio_vae，否则无音频输出

---

## 六、默认采样参数

| 参数 | 默认值 | 红绳项目值 |
|---|---|---|
| 画布 | 0.4MP 16:9 (864×480) | 1056×608 (0.6MP) |
| 时长 | 5秒 / 124帧 @24fps | 15秒 / 362帧 @24fps |
| steps | 25 | 8（加速） |
| sampler | res_multistep | euler |
| scheduler | simple | simple |
| CFG | 1.0 | 1.0 |
| Sigma shift (video) | 12 | 6（工作流预设） |
| Sigma shift (audio) | 3 | 3（工作流预设） |

**红绳项目使用 8 步 euler + TESpeed 加速**，在保证质量的同时大幅缩短生成时间（约6-7分钟/15秒片段）。

---

## 七、timeline_data 结构（API 调用）

通过 API 或脚本调用时，导演台节点的核心输入是 `timeline_data` JSON 字符串：

```json
{
  "version": 5,
  "editMode": "segment",
  "totalFrames": <总帧数>,
  "frameRate": 24,
  "global": {
    "taskType": "r2v — 参考主体生视频(Reference to Video)",
    "prompt": "<全局素材说明>",
    "refs": [ {"index": 0, "imageFile": "xxx.png", "type": "input"} ],
    "refAudios": [ {"index": 0, "audioFile": "xxx.wav", "durationSec": 4.0} ]
  },
  "segments": [
    {
      "id": "msxxxx",
      "start": 0,
      "length": 362,
      "durationSec": 15,
      "prompt": "<六段结构 + negativePrompt + 连续性出点>",
      "refs": [ {"index": 5, "imageFile": "故事板.png"} ],
      "continuityFromPrev": false
    }
  ],
  "batchWorkspaces": {
    "r2v": { "segments": [ <与 segments 同步> ] }
  }
}
```

**关键约束**：
- `global.refs` 最多 5 张（index 0-4），`segments[].refs` 从 index 5 开始
- `global.refAudios` 最多 3 条
- `continuityFromPrev`：第一段 false，后续分段 true
- `batchWorkspaces.r2v.segments` 必须与 `segments` 同步
- 总帧数 = 所有分段 length 之和

---

## 八、常见问题

### Q: 生成的视频没有声音？
A: 检查是否接了 `audio_vae`，以及 CLIP type 是否为 minimax。r2v 模式会原生生成音频。

### Q: 人物脸崩或身份漂移？
A: 检查公共参考图是否清晰、提示词中 `<Subject N>` 是否明确绑定 `<Picture N>`。可增加人物四格人设图的参考权重。

### Q: 分段间不连续？
A: 确保 `continuityFromPrev=true`，且段间引导上下文帧数设为 22。检查上一段末帧与下一段首帧的场景/人物位置是否一致。

### Q: 二采后画面反而变差？
A: 检查 Refine 的 sigmas 设置，二采步数不宜过多（通常4-8步）。`passes>1` 时注意每轮的提示词是否一致。

### Q: RunningHub API 提交后素材不生效？
A: RunningHub 云端环境中，`timeline_data` 的 `imageFile` 需要是已上传到 RH 的 URL，而非本地文件名。需先通过 `/openapi/v2/media/upload/binary` 上传素材获取 URL。
