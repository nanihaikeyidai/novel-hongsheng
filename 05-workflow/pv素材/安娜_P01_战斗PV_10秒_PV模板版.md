# 安娜 战斗高燃 PV —— 按《MINIMAX-H3 动漫 PV 专属 I2VA 模板》生成

> 模板：B站-是古手梨花sama《MINIMAX-H3 动漫 PV 专属图生视频（I2VA）提示词生成模板》
> 参考图：pv素材/安娜.png（<Picture 1> 首帧锚定）
> 规格：10 秒 / 16:9 / 主分册：战斗高燃 / 次级：宣传 PV / 禁止 BGM（后期配音）

---

## 内部流程（A-F，按模板执行）

### A. 视觉证据卡（基于参考图 + 红绳原文设定）

```yaml
hard_facts:
  subjects: 单主体，安娜——高冷杀手学生（异常事件调查员伪装学生）
  appearance_locks: 人设图锁定——黑色中长发、冷静锐利眼神、白蓝校服、垂于身侧右手
  pose_and_gaze: 直立站姿、视线冷静锁定前方、右手自然垂落（待凝刃）
  props_and_relations: 右手为技能锚点（凝刃：掌心凝聚冷白刀刃，刀刃由虚转实、边缘冷白寒光——红绳原文片段07）
  environment_topology: 雨天高三教室、后部过道、课桌纵深排列、右侧雨痕玻璃窗、冷蓝灰雨光
  observable_colors: 白蓝校服 × 冷蓝灰雨光 × 冷白刀光
  first_frame_camera: 中景、水平机位、教室纵深透视、右侧窗光
uncertainty:
  hidden_regions: 参考图为设定展示，全身动作细节以最少必要推断补充
  risky_inventions: 不新增武器/变身/换装；黑影对手不做实体细节定义
motion_affordances:
  native_vectors: 右手掌心→刀刃凝聚方向；教室过道纵深→前踏挥斩方向；雨滴→刀光切雨
  plausible_next_actions: 凝刃 / 前踏 / 上挥斩 / 收刃
symbolic_sources: 冷白刀刃、雨痕玻璃、冷蓝灰光、白蓝校服
identity_risk_level: low
crop_expansion: limited
adult_gate: confirmed_adult
```

### B. 风格路由

```yaml
commercial_goal: 动作爽点 + 角色记忆
primary_mode: 战斗高燃（用户明确）
secondary_lens: 宣传PV语法（开场宣传片，余韵收尾）10%
text_policy: no_text（无屏显文字）
```

### C. 三案导演发散

1. **图像内生型（选）**：安娜从首帧站姿直接凝刃→前踏挥斩→黑影溃散收刃。动作链完整可执行，首帧忠实度最高，战斗爽点直给。
2. 概念转化型：雨幕为刃——刀光切开雨幕，雨滴沿刀路悬停碎裂，把雨天环境转化为战斗语言。
3. 形式突破型：玻璃雨痕反射中刀刃成形，闪切至实战（光影临界+反射转场）。

### D. 创意差异闸门

三案开场钩子（掌心凝光 / 雨幕静默 / 反射成形）、叙事几何（直线进击 / 环境拟态 / 反射叠化）、镜头主线（跟刃 / 雨滴特写链 / 反射切）、转场逻辑（动作延续 / 形状匹配 / 遮挡反射）、结尾 payoff（收刃余晖 / 雨幕愈合 / 反射与实体重合）互不相同，通过（≥4/6 项差异）。

### E. 候选选择

图像内生型：适配 35%✅ / 可执行 30%✅ / 商业钩子 20%✅ / 新颖 15%◐ → 总分最高，采用。

### F. 导演台

```yaml
intent: 让观众记住——冷面少女掌中凝刃，一刀斩开雨幕
audience_hook: 前0.8秒掌心冷白寒光初现
emotional_arc: 压抑克制 → 爆发出手 → 余韵收刃
primary_mode: 战斗高燃 | secondary_lens: 宣传PV
creative_fingerprint: 掌中凝刃成形 → 直线进击挥斩 → 黑影溃散收刃余晖
recurring_anchor: 冷白刀光（凝现→挥出→消散）
music_skeleton: 无BGM（用户后期配音）→ non_diegetic_music: N/A
complexity_budget: shot_count 3 / total_primary_events 3 / high_risk_inventions 0 / text_count 0
shot_map:
  - shot 1 (0-3.2s): 首帧=参考图 → 凝刃成形（掌心冷光由虚转实）→ 中景静态
  - shot 2 (3.2-7.1s): 近景 → 前踏上挥斩（白弧刀光、破空声、发丝衣摆掀起）
  - shot 3 (7.1-10s): 中远景 → 黑影溃散、雨滴切裂 → 收刃消散冷光余晖
ending_payoff: 刀刃消散为冷光碎屑，安娜垂手站立眼神冷静——冷刃身份的定格记忆点
```

---

## 最终成稿（I2VA，可直接喂入）

For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Anna, a cold-faced high school girl in a white-and-blue uniform, stands motionless in the rear aisle of a rain-soaked classroom at dusk, her posture, uniform, hair and expression exactly matching the reference image; cold blue-grey window light traces her silhouette through rain-streaked glass, raindrops crawling down the pane. She slowly raises her right hand, fingers tightening, and a white blade condenses from her open palm, materializing edge-first with a faint cold gleam that washes across her knuckles; her gaze stays locked forward, calm and sharp. [Shot 2] At 00:03.200, the camera cuts to a close-up: the blade fully formed, its cold light carving half her face out of shadow; she steps forward with her left foot, shifts her weight onto the front leg, and swings the blade upward in a white arc, the air splitting with a short sharp whoosh; her black hair and the curtain behind her whip in the draft, a few rain beads flung off the blade edge. [Shot 3] At 00:07.100, the camera cuts to a medium-wide shot from the classroom middle aisle: the white blade arc slashes through a blurred dark silhouette near the front of the classroom, which dissolves into the rain without visible gore; raindrops split along the blade path, scattering fine mist and droplets; Anna retracts the blade, which dissolves into cold light fragments drifting down, and stands still in the aisle, her gaze unshaken, the wet floor reflecting her silhouette.

overall_soundscape: Rain tapping steadily on window glass throughout; one short sharp whoosh as the blade swings through the air; fabric rustle of the uniform and a light footstep on the wet floor; a brief burst of scattered water droplets as the rain is cut.

non_diegetic_music: N/A

---

> 质量闸门自查：首帧忠实✅ 主体稳定✅ 时间戳递增(0/3.200/7.100)✅ 一镜一主事件✅ 动作链完整（凝刃→挥斩→结果→余韵）✅ 无对白无文字✅ 无BGM（N/A）✅ 复杂度预算内（3镜3事件）✅
