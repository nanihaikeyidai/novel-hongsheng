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
│   ├── voice_shaper.py       第四轮声线整形：保时长降调 + 加速 + 笑意/厚度 EQ
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

# 3.6) 第四轮：更低沉 / 更快 / 带戏谑笑意（降调+加速+笑意 EQ 一次做完）
python voice_shaper.py --input ../cases/P09_晚安/候选音频/M_smirk_text.wav \
  --output ../cases/P09_晚安/候选音频/X_r4_deep.wav \
  --semitones -2.2 --tempo 1.20 --smile 0.70 --depth 1.2 \
  --breath 0.34 --soft 0.42

# 4) 选一版贴回成片（自动检测真实起音点；--level-offset-db 才是「变轻」的开关）
python replace_line.py --case cases/P09_晚安/case_round4.json \
  --line-audio 候选音频/X_r4_deep.wav \
  --out 成片/P09_晚安_低沉轻快戏谑_主推.mp4 \
  --preset dry --level-offset-db -8.0 --bed 0.02
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
| `whisperize.py --soft` | 谐波软化 0–1，越高越不像正常发声；要保住笑意咬字就降到 0.40 |
| `voice_shaper.py --semitones` | 保时长降调半音数（负值）；**少年音下限 -2.5st**，再低就成年化 |
| `voice_shaper.py --tempo` | 语速倍数 >1 加快，与降调互不干扰 |
| `voice_shaper.py --smile` | 戏谑笑意 EQ：抬 2.6/4.8kHz 共振峰区，0=无笑意 |
| `voice_shaper.py --depth` | 低沉厚度 EQ：抬 140Hz、压 700Hz，不改 F0 |

## 音频层规则（沿用 David 技巧文档）

1. **沈默是 14 岁少年音**：P09 的「低沉带进攻性」指的是**音量/语速/气声**，不是把音高降成成年男声。情绪描述必须同时写「保持少年音色」，且只挂 `沈默.wav`。第四轮用户要「更低沉」后才引入降调，也只降到 **F0 100–105Hz**（-1.5~-2.2 半音），**90Hz 以下一律不用**。
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

## 「更低沉 / 更快 / 更轻 / 带笑」四轴怎么拆（第四轮经验）

四个诉求会互相抵消，必须分层，且**顺序固定**：模型底子 → 降调加速 → 气声层 → 笑意/厚度 EQ → 贴回压电平。笑意 EQ 必须在 `whisperize.py` **之后**叠，否则会被它的近讲 EQ（2.5kHz -1dB）抵消。

| 诉求 | 唯一有效的层 | 实测参数 / 效果 |
|---|---|---|
| 更低沉 | `voice_shaper.py --semitones` | 保时长降调 `asetrate=SR*R → aresample=SR → atempo=1/R`；-2.2st 把 F0 113.9→**100.5Hz**，再用 `--depth` 抬 140Hz 加厚度 |
| 语速加快 | `--tempo` + case 的 `duration_factor < 1` | 模型侧 0.92 + 后期 1.20；有效发声 **0.74→0.45s**（2.7→4.4 字/秒） |
| 更轻 | `replace_line.py --level-offset-db` | -5.5→**-8.0dB**；台词窗 RMS -21.1→**-23.1dB**（原片 -14.9dB）；ASR 仍能识别，可懂度没丢 |
| 戏谑笑意 | 模型 text 情绪 + `--smile` | 嘴角带笑的轻蔑玩味；2.6/4.8kHz 微抬模拟 F2 上移 |

**「戏谑」不是「开心」**：情绪文本写「嘴角挂着一点戏谑的笑、像猫逗弄已经跑不掉的老鼠、轻蔑玩味、稳操胜券；不是开心，没有笑出声，不甜不软糯」，`strength` 压到 **0.55**（0.9 会把 F0 抬到 200Hz）。另出向量版 `happy .22 + angry .18 + disgusted .12 + calm .48` 作对照。

**窗口要跟着语速收**：第三轮慢吐把窗放宽到 5.50s；第四轮有效发声只剩 0.45s，收回 5.08s 后窗后能量从 -71.5dB 回到 -68.3dB（与窗前一致），上轮那点「真空感」消失。台词 0.48s 落在 4.29–4.77s，比原片口型（到 4.92s）早收 0.15s，是「语速加快」的必然结果。

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
- **窗口不是越宽越好**：台词变快后仍沿用慢吐的 5.50s 宽窗，会把 5.08s 之后的原片环境音一起挖空（窗后 -71.5dB，比窗前轻 3dB），听出真空感。按有效发声长度回收窗口。
- 降调用 `asetrate → aresample → atempo=1/R` 才能**保时长**；只做 `asetrate` 会让整句变长，叠上 `--tempo` 后语速就算不准了。
- `--smile` 是音色 EQ，不是情绪开关；模型侧没给笑意底子时，单靠 EQ 只有「亮一点」，听不出戏谑。

## 案例

| 案例 | 台词 | 原片时间窗 | 状态 |
|---|---|---|---|
| `cases/P09_晚安` | 沈默「晚安。」 | ASR 4.07–4.77s；**实测起音 4.29–4.95s** | ✅ 四轮 22 候选；当前主推 `低沉轻快戏谑_主推`（F0 100.5Hz / 4.4字每秒 / -8dB / 戏谑笑），备选 `低沉轻快戏谑_备选`；见 `复盘.md` |

### P09 结论速记

- **当前主推 `X_r4_deep`**＝`M_smirk_text`（戏谑文本情绪 strength 0.55 + duration_factor 0.92）→ `-2.2st / tempo 1.20 / smile 0.70 / depth 1.2 / breath 0.34 / soft 0.42` → 电平 -8.0dB。F0 **100.5Hz**、有效 **0.45s**（4.4 字/秒）、气声 -10.4dB、音色相关 0.955、台词窗 RMS -23.1dB。
- **备选 `X_r4_main`**＝同底子但 -1.5st / smile 0.85 / -6.5dB，F0 104.9Hz，少年音更稳、笑意更明显、也更响一点。
- 第三轮 `W_L_whisper`（气声慢吐耳语，F0 114Hz / 0.74s / -5.5dB）保留作对照，成片 `P09_晚安_耳语死亡宣告_主推.mp4`；更早的 `H_origvoice_cold` 见 `P09_晚安_威胁版_H.mp4`。
- **`text` 情绪模式 `strength 0.9` 会抬 F0**（A 212Hz / E 199Hz），降到 0.6 才安全；要气声别指望模型。
- 对齐必须走能量包络，ASR 时间戳在本片偏 **+0.22s**。
