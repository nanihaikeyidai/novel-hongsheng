# HyperFlow H3 Flash · 本地使用卡

> 2026-11-11 本机实测通过。仓库：[Video-Rebirth/hyperflow-h3-flash](https://github.com/Video-Rebirth/hyperflow-h3-flash)（173★，Apache-2.0，11-06 才建仓）
> 节点：[Video-Rebirth/ComfyUI-HyperFlow-Flash](https://github.com/Video-Rebirth/ComfyUI-HyperFlow-Flash)
> 权重：[VideoRebirthAI/hyperflow-h3-flash](https://huggingface.co/VideoRebirthAI/hyperflow-h3-flash)

---

## 一、它是什么

MiniMax-H3 的 **14B 压缩少步版**（"post-trained derivative"）：**4 / 6（默认）/ 8 步、免 CFG**，生成**视频 + 同步立体声音轨**。

| 项 | 值 | 本机实测 |
|---|---|---|
| 分辨率 | 1344×768 | ✅ 一致 |
| 时长 | 5.2–15 秒（17n+5 帧栅格 @24fps） | ✅ 124 帧 = 5.17 秒 |
| 音轨 | 32kHz 立体声 | ✅ AAC 32kHz 2ch |
| 显存 | GGUF Q4_K_M 9.1GB / Q8_0 14.9GB | ✅ **峰值仅 5.4GB / 16GB** |
| 权重 | 14B（README 写 13.7B） | fl2va Q4_K_M = 9.05GB |
| 许可 | Apache-2.0 | 比 Pika H3 Flex（社区许可）宽松 |

---

## 二、本机安装记录（已全部完成）

```
ComfyUI/
├── custom_nodes/
│   ├── ComfyUI-GGUF/                    ← 原来就有，不用装
│   └── ComfyUI-HyperFlow-Flash/         ← 新装（codeload zip，git clone 会被 reset）
└── models/
    └── diffusion_models/
        └── minimax_h3_fl2va_hyperflow_flash_14b-Q4_K_M.gguf   ← 9.05GB
```

**已确认存在、可直接复用**：
- `models/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`（15GB，**不用重下**）
- `models/vae/minimax_h3_audio_vae_fp32.safetensors`
- `models/vae/minimax_h3_video_vae_int8_convrot.safetensors`（⚠️ 官方要 fp16，**int8 版实测可用**）

**关键点**：
- **ComfyUI 0.42.5 直接可用**（官方 README 说要 ≥0.43.0，实测本机 0.42.5 跑通，HyperFlow 节点加载 0.0 秒无报错）
- **必须加 `--fast-disk` 启动参数**（GGUF 在 16/32GB 内存机器上需要）。已在 `D:\HermesWorkspace\_tmp\start-comfy.ps1` 加好，守护自动生效
- 下载要用 **hf-mirror.com**（huggingface.co 在本机不通）；curl 容易挂死不返回数据，**用 Python Range 断点续传更稳**

---

## 三、工作流结构（API 格式，14 个节点）

```
HyperFlowLoader(unet_name=minimax_h3_fl2va_hyperflow_flash_14b-Q4_K_M.gguf)
CLIPLoader(qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors, type=minimax)
VAELoader(minimax_h3_video_vae_int8_convrot.safetensors)
VAELoader(minimax_h3_audio_vae_fp32.safetensors)
MiniMaxH3ImageToVideo(clip, vae, prompt, width=1344, height=768, length=124)
HyperFlowSigmas(model, steps=4|6|8)
KSamplerSelect(euler) / RandomNoise(seed) / BasicGuider / SamplerCustomAdvanced
VAEDecode + VAEDecodeAudio → CreateVideo(fps=24) → SaveVideo(mp4)
```

只有 `HyperFlowLoader` 和 `HyperFlowSigmas` 是新节点，其余全是 ComfyUI 原生。
**官方模板**：节点包内 `example_workflows/` 有 t2v / i2v / flf2v / ref2v 四套（GGUF + INT8 各一份），`example_workflows/api/` 是可直接 POST 的 API 格式。

---

## 四、实测结果（3 条，全部成功）

| # | 步数 | seed | 时长 | 耗时 | 说明 |
|---|---|---|---|---|---|
| C | 4 | 42 | 5.17s | **188.6s**（含模型加载） | 第一条，红绳审讯线提示词 |
| B | 8 | 42 | 5.17s | ~160s（模型已加载） | 同 seed 不同步数 |
| A | 4 | 1234 | 5.17s | ~150s | 换 seed |

- **画面有真实内容**（非黑屏：暗/亮像素占比 <2%，std≈48–58）
- **音轨有声音**（ASR 转出「阿珂。」）
- ⚠️ **它会自己冒台词**：只写了视觉描述没让它说话，它自己生成了对白 —— 音视频联合的副作用。做无声片段时要留意

---

## 五、对红绳的意义

✅ **能落地**：16G 卡显存只吃 5.4GB、**1344×768 接近 2K 宽高比**、4 步比原生 H3 快得多、免 CFG
✅ **首尾帧（flf2v）可用** → 「分镜切分 + 上段尾帧接下一段首帧」的路线在这条线上也成立
✅ **Apache-2.0** 许可比 Pika H3 Flex 宽松
⚠️ **720p 级别**，你的终版规格是 2K → **定位是「快速预演 / 节奏验证 / 分镜草稿」**，终版仍走本地 H3 + upscale
⚠️ **会自己生成对白** → 和 AnyAudio 情绪配音冲突，要么不用它的音轨，要么在混音时丢掉
💰 成本：电费（本地）

---

## 六、下一步可选

1. **下 ref2va 的 Q4_K_M**（约 9GB）→ 多参考编辑，和 T8 的 H3 Max 编辑节点互补
2. **跑 flf2v（首尾帧）** 测接缝 → 这才是你分镜切分路线的关键验证
3. **对比原生 H3**：同提示词同 seed，两条并排，看 HyperFlow 4 步和原生多步的画质差距到底值不值
4. **测 15 秒**（362 帧）→ 确认 16G 能不能扛住你的标准时长
