# 本地重配音实验室（IndexTTS 2.5）

把已归档成片里**某一句台词**单独重配，只换声音、不动画面、不重跑视频模型、**0 币耗**。

- 引擎：本机 ComfyUI 的 `comfyui-indextts25-T8` 节点 + `models/TTS/IndexTTS-2.5`（7.7 GiB 全套已在位）。
- ComfyUI **由 David 自己用整合包启动器启动**；本实验室只通过 `http://127.0.0.1:8188` 排队，绝不启动/重启服务。
- 与视频生成闸门无关：这里不消耗 RunningHub 金币，可以多次试不同情绪参数。

## 目录

```
重配音实验室/
├── README.md                 本文件
├── config/voice_profiles.json 角色 → 正式参考音色映射
├── scripts/
│   ├── tts_lab.py            ComfyUI API 客户端：按 case.json 批量生成候选
│   ├── analyze_candidates.py 候选对比：时长/F0/响度/音色相关 + 气声三指标
│   ├── whisperize.py         气声化后期层：谐波软化 + 气流噪声 + 近讲 EQ
│   ├── plot_candidates.py    把对比结果画成 PNG（只需 Pillow）
│   └── replace_line.py       时间窗替换：自动对齐真实起音点，支持电平偏移
├── workflows/                每个候选的 API prompt JSON（可复现/可在 UI 里改）
└── cases/<案例>/
    ├── case.json             台词、音色、情绪候选、时间窗
    ├── 参考音频/              正式音色 + 原片切出的原声
    ├── 候选音频/              各版 TTS 输出（48k 单声道 PCM wav）
    ├── 成片/                  替换后视频 + 独立试听音轨
    └── 验收/                  ASR、响度、频谱、对照拼图
```

## 三步跑法

```bash
cd 05-workflow/重配音实验室/scripts

# 0) 确认服务在跑、队列空闲（不启动服务）
curl -s http://127.0.0.1:8188/system_stats | head -c 200

# 1) 参考音频放 ComfyUI/input/，文件名必须 ASCII
cp ../../../归档素材/人物参考音色/沈默.wav \
   "F:/Work-Fisher纯净包2026.8.7/ComfyUI/input/voicelab_shenmo_ref.wav"

# 2) 只打印节点图 / 批量生成候选
python tts_lab.py --case cases/P09_晚安/case.json --check
python tts_lab.py --case cases/P09_晚安/case.json
python tts_lab.py --case cases/P09_晚安/case.json --only A_text_threat

# 3) 客观对比（必要时出图）
python analyze_candidates.py --dir cases/P09_晚安/候选音频 \
  --ref cases/P09_晚安/参考音频/P09原片_晚安_3.90-5.10s.wav \
  --out cases/P09_晚安/验收/候选声学对比.json
python plot_candidates.py --data cases/P09_晚安/验收/候选声学对比.json \
  --out cases/P09_晚安/验收/候选声学对比.png

# 3.5) 需要「更轻 / 气声耳语」时，先给候选加一层气流噪声
python whisperize.py --input ../cases/P09_晚安/候选音频/L_flat_death.wav \
  --output ../cases/P09_晚安/候选音频/W_L_whisper.wav --breath 0.38 --soft 0.55

# 4) 选一版贴回成片（自动检测真实起音点；--level-offset-db 才是「变轻」的开关）
python replace_line.py --case cases/P09_晚安/case_round3.json \
  --line-audio 候选音频/W_L_whisper.wav \
  --out 成片/P09_晚安_耳语死亡宣告_主推.mp4 \
  --preset dry --level-offset-db -5.5 --bed 0.02
```

## case.json 字段

| 字段 | 说明 |
|---|---|
| `source_video` | 原成片绝对路径；画面直接 `-c:v copy` |
| `line` | 要重配的台词原文（含标点，标点影响停顿） |
| `voice_ref` | ComfyUI/input 里的**正式音色**文件名（ASCII） |
| `emotion_ref` | 可选，原片切出的原声，用于 `reference_audio` 情绪模式 |
| `window` | 替换窗口 `[起, 止]` 秒，比 ASR 台词窗略放宽，留出气口 |
| `hard_end` | 可选，下一句台词的硬边界；窗口可以向后放宽到慢吐够用，但绝不越过它 |
| `original_line_asr` | 原片台词实测时间窗，用于**响度对齐**和起音点搜索中心 |
| `candidates[].text` | 可选，覆盖全局 `line`（试停顿/断句用） |
| `candidates[].emotion.mode` | `text`（Qwen 中文情绪描述）/ `vector`（八维）/ `reference_audio` / `speaker` / 不填=无情绪 |
| `candidates[].sampling` | 可选，生成 `T8_IndexTTS25_SamplingConfig` 节点：`pause_preset` / `inference_cfg_rate` / `cfm_temperature` 等 |
| `candidates[].duration_factor` | 0.8–1.25；略 >1 会变慢，适合威胁语气，但别超出窗口 |
| `replace_line.py --preset` | `dry` 保持 TTS 原貌；`phone` 加 260–3500Hz 带通（耳机/电话画外音用） |
| `replace_line.py --level-offset-db` | **轻声开关**，负值让新台词比原片台词窗更轻；P09 耳语用 -5.5，保守版 -3.5 |
| `replace_line.py --bed` | 窗口内保留的原环境底噪比例，默认 0.06；轻声台词建议 0.02–0.04 |
| `whisperize.py --breath` | 气声层 RMS 相对原声的比例：0.25 轻 / 0.38 适中 / 0.5 明显 |
| `whisperize.py --soft` | 谐波软化 0–1，越高越不像正常发声 |

## 音频层规则（沿用 David 技巧文档）

1. **沈默是 14 岁少年音**：P09 的「低沉带进攻性」指的是**音量/语速/气声**，不是把音高降成成年男声。情绪描述必须同时写「保持少年音色」，且只挂 `沈默.wav`。
2. 威胁语气靠 `low cold aggressive` / `predatory quiet threat` 一类描述，避免 `demonic / devil / soft / cute`。
3. 响度不能凭感觉：脚本把新台词 RMS 对齐到原片台词窗，峰值限到 0.92，输出 48kHz AAC + `faststart`。
4. 验收必做：重跑 ASR 确认台词内容/次数、核对是否落在正确镜头、口型窗内无溢出。
5. 只改音频，不改视频提示词；若画面本身要改，走正常的「复盘 → 等确认 → 一次性生成」流程。

## 「更轻 / 气声 / 耳语」怎么做（第三轮经验）

**单靠模型做不出气声。** IndexTTS 2.5 没有 whisper 开关，耳语文本情感、`[breath]` 标记、采样参数调整，气声比都还在 -26dB 左右（原片水平）。有效组合是三步：

1. **模型侧只负责底子**：原片切片作音色（锁住 F0/音色）＋极冷向量 `calm 0.9`（毫无起伏＝死亡宣告）或低强度耳语文本 `strength 0.6`；
2. **后期层 `whisperize.py` 造气声**：谐波软化（3.4kHz 低通混合）＋包络调制的 500–7000Hz 着色气流噪声＋近讲 EQ。气声比从 -26.8dB 拉到 **-9.7dB**、周期性 0.498→0.436、谱平坦度 0.018→0.062，且**起音点/有效时长不变**；
3. **贴回时压电平**：`--level-offset-db -5.5 --bed 0.02`。只改后期不压电平是没用的——`replace_line.py` 的 RMS 对齐会把「轻」重新拉回原片响度。

需要慢吐就再 `atempo=0.92`；P09 下一句 5.95s 才起，窗口可从 5.05 放宽到 5.50s（台词可用 1.2s）。

## 已踩过的坑

- `SaveAudio` 实际输出 **`.flac`**，`tts_lab.py` 下载后统一转成 48k 单声道 PCM wav，否则 `wave` 模块读不了。
- `LoadAudio` 的文件名/输出 `filename_prefix` 一律 ASCII；中文名在 ComfyUI 侧易出问题。
- 情绪控制是 ComfyUI V3 动态组合输入，API 里必须写扁平路径：`mode` + `mode.emotion_text` / `mode.angry` / `mode.emotion_audio`，照抄 `example_workflows/api/` 下的 03/04/05。
- 不要在后台启动 ComfyUI（Manager 的 `/manager/reboot` 会让服务静默消失）。
- **ASR 时间戳有 0.2–0.3s 偏移**：P09 实测 ASR 4.07s / 真实起音 4.29s。`replace_line.py` 用 20ms 帧能量包络自动定位，别手填 ASR 起点，否则口型会漂。
- 合成的 ffmpeg 命令**不要加 `-shortest`**：音轨短十几毫秒就会截掉最后一帧画面（视频流 md5 会变）。
- **`[breath]` / `[quick_breath]` 标记在中文文本里会被念成英文**：实测 ASR 得到「One Bree 安。」「One quick breath 安。」，I/K 两个候选直接作废。它们是 Qwen tokenizer 的 special token，本节点中文前端没有过滤。
- `text` 情绪模式不是完全不能用：把 `strength` 从 0.9 降到 **0.6**，F0 就不会飙到 200Hz（J 实测 113.4Hz、音色相关 0.998）。
- 想让台词「变轻」，**必须在 `replace_line.py` 里给电平偏移**；只在 TTS 或 DSP 阶段压音量会被 RMS 对齐抵消。
- 别把气声层做成前置吸气声：`trim_silence` 会把它当成起音点，导致台词整体前移、口型漂。

## 案例

| 案例 | 台词 | 原片时间窗 | 状态 |
|---|---|---|---|
| `cases/P09_晚安` | 沈默「晚安。」 | ASR 4.07–4.77s；**实测起音 4.29–4.95s** | ✅ 三轮 16 候选；当前主推 `耳语死亡宣告_主推`（气声＋-5.5dB），备选 `耳语死亡宣告_备选`；见 `复盘.md` |

### P09 结论速记

- **当前主推 `W_L_whisper`**＝`L_flat_death`（原片切片音色＋`calm 0.9` 极冷向量，F0 111Hz）→ 气声层 0.38 → `atempo 0.92` 慢吐 → 电平 -5.5dB。F0 114Hz、气声比 -9.7dB、有效 0.74s、台词窗 RMS -20.2dB（原片 -15.5dB）。
- **备选 `W_J_whisper`**＝耳语文本情感（strength 0.6）＋气声 0.30＋电平 -3.5dB，更保守、可懂度更高。
- 上一轮 `H_origvoice_cold`（低沉威胁）保留作对照，成片 `P09_晚安_威胁版_H.mp4`。
- **`text` 情绪模式 `strength 0.9` 会抬 F0**（A 212Hz / E 199Hz），降到 0.6 才安全；要气声别指望模型。
- 对齐必须走能量包络，ASR 时间戳在本片偏 **+0.22s**。
