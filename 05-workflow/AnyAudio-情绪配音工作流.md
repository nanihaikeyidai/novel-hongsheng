# 红绳 · 人物语气情绪配音工作流（AnyAudio）

> 目标：同一段审讯线台词，能按角色/情绪逐句换语气，而不是整段一个调子。
> 依赖：`dsh-any-audio`（已装）+ **MiMo-V2.5-TTS key**（当前缺）。

---

## 一、为什么必须用 MiMo

AnyAudio 的 TTS 工具支持两种引擎：

| 引擎 | 能改什么 | 能否改情绪 |
|---|---|---|
| Edge（默认） | `rate` 语速 / `pitch` 音高 / `volume` | ❌ 只是快慢高低 |
| **MiMo-V2.5-TTS** | `style` 自然语言情绪指令 | ✅ 真改语气 |

源码证据（`dsh-any-audio/src/tools/tts.js`）：
- `items: [{text, provider, voice, rate, pitch, volume, style, output}]` —— **逐句**独立
- MiMo 时把 `全局style + 逐句style + rate/pitch` 拼成一条指令发给模型
- `buildMimoRequest()` 把 style 作为 user message，`style` **不会被念出来**

⚠️ Edge 在你这台机器上实测超时（微软非官方端点限流），所以 MiMo 不是可选项，是必须。

---

## 二、配置（已完成，2026-11-06 实测通过）

- [x] MiMo key 已存进 DSH 凭据 `MIMO_API_KEY`
- [x] Settings → AnyAudio 里 provider 切到 `mimo`
- [x] **坑**：`mimo.proxy` 曾被误填成邮箱地址，`HttpsProxyAgent` 拿它 `new URL()` → 报 `Invalid URL`。已清空。**代理必须是 `http://127.0.0.1:7890` 这种 URL；不用代理就留空。**
- 配置文件：`C:\Users\Administrator\.dsh\anyaudio\config.json`（已备份 `.bak-20261106`）

> key 存进 DSH 凭据，不写进任何文件/记忆。

---

## 三、逐句情绪配置（红绳 ep04 审讯线示例）

一段戏里，每句台词单独一个 item，各带自己的 `style`：

```json
{
  "items": [
    {
      "text": "你父亲陆定天，最后一次见他是什么时候？",
      "provider": "mimo",
      "style": "审讯官的语气，平稳、克制、不带威胁，像在念一份档案；语速偏慢，句尾不下压",
      "output": "C:/Users/Administrator/.dsh/im/anyaudio/ep04/11d_q1.wav"
    },
    {
      "text": "你们为什么知道我父亲的事？",
      "provider": "mimo",
      "style": "陆沉，短发女生，先是防备，尾音微微发紧；压着情绪问，不要哭腔",
      "output": "C:/Users/Administrator/.dsh/im/anyaudio/ep04/11d_a1.wav"
    },
    {
      "text": "我们是官方机构，查一个人的档案，不难。",
      "provider": "mimo",
      "style": "老韩，中年男声，疲惫、公事公办，句尾略沉；不要演成反派",
      "output": "C:/Users/Administrator/.dsh/im/anyaudio/ep04/11d_q2.wav"
    },
    {
      "text": "他失踪十二年，官方记录是因公殉职。你们却在找他。",
      "provider": "mimo",
      "style": "从陈述转为逼问，前两句平，最后'你们却在找他'突然压低、放慢，带一点危险的耐心",
      "output": "C:/Users/Administrator/.dsh/im/anyaudio/ep04/11d_q3.wav"
    }
  ]
}
```

**写法要点**（决定效果好坏）：
1. `style` 写**导演提示**，不写形容词堆砌 —— "压低、放慢、带危险的耐心" 比 "很生气" 好用
2. 一句话里可以有**转折**（"前两句平，最后突然压低"），MiMo 能吃到
3. 角色身份写进 style（"陆沉，短发女生"），比只换 `voice` 稳
4. 别写"不要有 AI 味"这种废话，写具体的声学动作
5. 每句单独 output → 后面 `anyaudio_mix` 按分镜时间轴精确摆放

---

## 四、情绪档位速查（复制到 style 里）

| 情绪 | style 模板 |
|---|---|
| 克制的审问 | 平稳、克制、不带威胁，语速偏慢，句尾不下压 |
| 压抑的愤怒 | 音量不高但咬字重，句间停顿变长，尾音收住不扬 |
| 慌乱 / 防备 | 语速略快、气声偏多，尾音发紧，偶尔吞字 |
| 疲惫 / 公事公办 | 中低音区，句尾略沉，少起伏，不演情绪 |
| 危险的耐心 | 放慢、压低，每句之间留半拍，像在等对方自己说漏 |
| 崩溃边缘 | 前半句还稳，某个字突然抖一下，之后收住不哭出来 |
| 温柔回忆 | 气声多、语速慢、句尾轻轻落下，像怕吵醒谁 |

---

## 五、完整链路（有了 key 之后）

```
剧本台词 → 按情绪拆 items → anyaudio_tts(逐句 style) → 每句一个 WAV
        → anyaudio_mix(按分镜时间轴摆放 + ducking) → 成片音频
        → 可选 anyaudio_music / sfx 补配乐音效
```

混音示例（ducking 保证台词不被音乐盖住）：

```json
{
  "tracks": [
    {"role":"narration","path":".anyaudio/out/11d_q1.wav","gainDb":0},
    {"role":"narration","path":".anyaudio/out/11d_a1.wav","gainDb":0},
    {"role":"music","path":".anyaudio/out/score.wav","gainDb":-8}
  ],
  "durationSec": 15,
  "ducking": {"targetDb": -9, "thresholdDb": -42}
}
```

---

## 六、与 RunningHub 配音的分工

- **RunningHub / IndexTTS 2.5**：音色克隆，锁住"陆沉的声音长什么样"
- **AnyAudio + MiMo style**：同一音色下，逐句改"这句话怎么说"
- 两者不冲突：克隆产出参考音色 → 若 MiMo 支持自定义 voice id，可把克隆音色接进来用 style 驱动（**待实测**，README 说 MiMo 接受 custom/cloned voice ids）

---

## 状态

- [x] dsh-any-audio 已装
- [x] 逐句 style 机制已核实（源码级）
- [x] Edge 实测在本机超时（改用 MiMo 的依据）
- [x] **MiMo key 已配置，proxy 误填已修**
- [x] **实测通过**：ep04 四句逐句情绪台词 + 同文本三档情绪对照，共 7 个 WAV
  - 硬证据：同一句「你们为什么知道我父亲的事？」→ 平静 2.08s / 惊慌 2.24s / 冰冷反问 **3.52s**（比平静长 69%）
  - 产出目录 `C:\Users\Administrator\.dsh\im\anyaudio\ep04\`
- [ ] 与红绳音色克隆链路接通
- [ ] 接进 `anyaudio_mix` 按分镜时间轴摆放 + ducking
