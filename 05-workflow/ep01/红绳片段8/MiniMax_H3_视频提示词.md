# 《红绳》片段8｜MiniMax H3 Ref2VA 提示词·待重绘复验

## 生成设置

- 模式：Ref2VA 多图与音色参考生成；15秒；16:9
- 视觉基准：`@图片6_故事板.png`（待重绘复验；只保留九格镜头顺序与空间构图，旧版回头画面以本提示词覆盖）
- 对白：全段唯一对白为陆沉第2格对林晓说“站我身后。”；第4格陆沉闭口沉默
- 特效音：第3格双眼完全变红的同一瞬间，一次短促、低沉、贴近胸腔的威压音
- 声音：使用 `@音频1` 只参考陆沉音色；无字幕、无BGM

## 素材对应

- `<Picture 1>` = `@图片1_陆沉.png`
- `<Picture 2>` = `@图片2_林晓.png`
- `<Picture 3>` = `@图片3_安娜.png`
- `<Picture 4>` = `@图片4_黑翼怪兽.png`
- `<Picture 5>` = `@图片5_雨天教室.png`
- `<Picture 6>` = `@图片6_故事板.png`
- `<Picture 7>` = `教室人物座位说明图.png`
- `<Picture 8>` = `@图片8_安娜手掌凝刃技能.png`
- `<Audio 1>` = `@音频1_陆沉.wav`

## 可直接粘贴的官方六段式提示词

```text
subject_definitions:
<Subject 1> is Lin Ming from <Picture 1>, preserving his youthful male face, short tousled black hair, tall teenage build, white school shirt with rolled sleeves, dark trousers, calm temperament, normal dark eyes at the opening, and scarlet eyes only after [Shot 2].
<Subject 2> is Lin Xiao from <Picture 2>, preserving her youthful face, dark-brown high ponytail, long red ribbon, white-and-navy uniform, red cord bracelet, and safe world position immediately behind Lin Ming.
<Subject 3> is Anna from <Picture 3>, preserving her very long straight deep-blue hair, cool grey-blue eyes, white-and-navy uniform, rear-row position, restrained temperament, and exactly three localized black-silver right-hand blades matching <Picture 8>.
<Subject 4> is the adult-sized black-winged creature from <Picture 4>, preserving its charcoal humanoid body, broad black membrane wings, hooked claws, pointed ears, and established dark-red eyes.
<Subject 5> is the evacuated, severely damaged rainy classroom from <Picture 5>, spatially constrained by <Picture 7>, preserving the shattered window, overturned desks, scattered books and paper, broken glass, rainwater, cold blue-grey light, and absence of ordinary students and Wang Laoshi.
<Picture 6> is a stale storyboard reference for [Shot 1] through [Shot 9], defining only the nine compositions and world placement; this prompt overrides its obsolete backward glance. <Picture 8> locks Anna's ability to exactly three separate black-silver blades.
<Audio 1> is the voice-timbre reference for <Subject 1> (S1); it transfers only Lin Ming's youthful male timbre and does not copy source words, timing, emotion, pauses, background noise, or recording artifacts.

summary:
[reference generation + audio reference] Create a fifteen-second high-detail 2D anime cinematic sequence following the nine compositions and world placement of <Picture 6>, with this prompt overriding its obsolete backward glance. Lin Ming already protects Lin Xiao at the opening. He keeps his face and gaze fixed on the creature with a slight brow furrow and never turns back; while still facing forward, he calmly tells Lin Xiao behind him to stand behind him while his eyes remain dark. He silently activates scarlet eyes. A single short, deep pressure sound occurs exactly when both eyes become fully scarlet; Lin Ming speaks no further dialogue. The creature freezes in fright, stumbles backward, and flies through the shattered window. Anna alone faces the escape direction and dissolves exactly three black-silver blades matching <Picture 8>. Lin Xiao alone presses a hand to her chest and exhales to calm her racing heartbeat. <Audio 1> references Lin Ming's timbre only for the single Mandarin line. Rain, dripping frame, window wind, fluorescent hum, and empty-room reverb continue beneath every sound and dialogue without stopping.

retention_analysis:
<Subject 1> (appears in [Shot 1] through [Shot 6]): fully_preserved - preserve Lin Ming's identity, existing protective placement, continuous forward gaze at the creature, slight brow furrow, no backward glance, dark eyes during his only line, later scarlet eyes, silent pressure against the creature, and stationary defense.
<Subject 2> (appears in [Shot 1], [Shot 4], [Shot 6], and [Shot 9]): fully_preserved - Lin Xiao remains safe behind Lin Ming and ends alone with one hand pressing her chest while her fear subsides.
<Subject 3> (appears in [Shot 1], [Shot 4], [Shot 6], and alone in [Shot 8]): fully_preserved - Anna stays in the rear row, faces the creature's escape direction, never attacks, and dissolves exactly three blades matching <Picture 8> only after it escapes.
<Subject 4> (appears in [Shot 1], [Shot 4] through [Shot 7]): fully_preserved - the creature remains inside through the retreat, then continuously crosses the shattered window and flies outside without counterattacking.
<Subject 5> (appears throughout): fully_preserved - the evacuated damaged classroom, rain, debris, and cold lighting never reset.
<Picture 6> ([Shot 1] through [Shot 9] storyboard structure): reference - preserve shot order and compositions while replacing its backward glance with the forward-facing performance specified here; omit panel borders, numbers, and annotations.
<Audio 1>: reference - only Lin Ming's timbre is transferred for the single newly performed target line “站我身后。”.

detailed_description:
The target uses high-detail Japanese 2D anime cinema with delicate cel shading, crisp stable linework, hand-drawn damaged-classroom backgrounds, cold blue-grey rain light, wet restrained reflections, and scarlet eyes as the only strong new color accent. Invisible pressure appears only through physical reactions in loose paper and wing membranes, never as a beam, ring, explosion, or magic circle.

[Shot 1] A medium-wide composition follows panel 1 of <Picture 6>. <Subject 1> is already planted between <Subject 2> and <Subject 4>, broad back protecting Lin Xiao, normal dark eyes, no running or repeated arrival. Lin Xiao remains directly behind him. The creature is fully inside on the wet classroom floor with one claw suspended and a visible air gap. Anna remains in the rear row. Broad exterior rain, droplets on the broken frame, window wind, faint fluorescent hum, and empty-room reverb continue.

[Shot 2] At 00:01.400, panel 2 becomes a side three-quarter close portrait. <Subject 1> (S1) keeps his body shielding Lin Xiao, face and gaze fixed on the creature, and brow very slightly furrowed; he never turns his head or eyes back. His eyes remain normal dark; jaw and voice stay steady. While still facing the creature, he speaks once toward Lin Xiao behind him in low-volume, slow, calm, protective Mandarin: <d>[Chinese] 站我身后。</d> Lip shapes match every syllable and close naturally at the end. Broad rain, droplets on the frame, window wind, faint fluorescent hum, and empty-room reverb remain continuously audible under the line, only ducked by about 3 dB; Lin Xiao gives no spoken reply.

[Shot 3] At 00:03.300, an extreme eye close-up follows panel 3. Lin Ming never breaks his lock on the creature; dark irises turn rapidly scarlet from center outward while the slight brow furrow remains. His face does not distort and his eyelids do not widen theatrically. On the exact frame when both irises become fully scarlet, play one short, deep, heavy pressure sound with a chest-felt sub-bass impact and a very brief downward tail, no longer than 0.6 seconds. It occurs once only and may carry an extremely thin high-frequency ring that resolves immediately. Rain, dripping frame, window wind, fluorescent hum, and empty-room reverb continue beneath it. No thunder, electrical crackle, explosion, or sustained energy drone.

[Shot 4] At 00:04.600, the side confrontation in panel 4 shows Lin Ming motionless before Lin Xiao, scarlet eyes fixed on the creature. His lips remain naturally closed and completely still; he uses no dialogue, whisper, breath-command, or vocalization. Loose paper bends subtly under invisible pressure. The last trace of the Shot 3 pressure sound vanishes immediately after the cut. The creature's growl catches and stops under Lin Ming's silent stare, followed by taut wing-membrane sound.

[Shot 5] At 00:06.200, panel 5 isolates <Subject 4>. Its red pupils contract to points, ears pin backward, aggressive snarl catches in its throat and collapses into a frightened inhale, wings lock rigid then tremble, and its raised claw stops. Add a caught animal inhale, low leather-like membrane tension, paper flutter, and continuous rain bed.

[Shot 6] At 00:07.700, panel 6 widens inside the room. Clearly frightened by the red eyes, the creature loses its attack posture, stumbles backward across wet flooring and glass toward the shattered window, scrabbles once for balance, and flaps its wings in panic but remains fully inside through the end of this shot. Lin Ming does not move; Lin Xiao stays behind him; Anna stays in the rear row. Add one short frightened shriek, claw scrapes, glass crunch, paper movement, disordered wing flaps, and uninterrupted rain ambience.

[Shot 7] At 00:09.800, panel 7 looks outward through the shattered frame. In one continuous motion the creature crosses the window plane, dislodges residual glass, turns away, and becomes fully outside in dense rain, shrinking with distance. No human is visible. Glass falls close to camera; two or three heavy wingbeats move from near interior impact to distant exterior rain.

[Shot 8] At 00:12.000, panel 8 shows <Subject 3> alone in a rear-row side-facing close-up. Her body, shoulders, face, and gaze all aim toward the shattered window and the creature's escape path. The background contains only the empty damaged classroom and rain light—no Lin Ming, Lin Xiao, creature, silhouettes, or blurred people. Her eyes widen moderately, inner brows lift slightly, and lips part by a fraction. Exactly three separate black-silver right-hand blades matching <Picture 8> fragment simultaneously into black-silver particles and sink into her palm with fine metallic decay and fading high resonance; never show a fourth blade.

[Shot 9] At 00:13.500, panel 9 isolates <Subject 2> in a chest-up close-up. No other character is visible. One hand presses clearly over the center-left chest, fingers naturally spreading against uniform fabric. Her shoulders slowly lower, gaze dips, knitted brows release, cheeks retain a faint post-fright flush, and parted lips release one long breath. The emotion combines relief, residual surprise, and an unexplained fluttering heartbeat; no crying, smile, or exaggerated panting. Three restrained subjective heartbeats begin fast and strong, then slow and soften beneath cloth friction, her exhale, and continuous rain. The last 0.3 seconds holds steadier breathing and rain.

overall_soundscape:
Use diegetic sound only. Maintain broad exterior rain, closer droplets striking the shattered frame, broken-window wind, faint fluorescent hum, and long evacuated-classroom reflections continuously across the entire 15 seconds: never mute, stop, or gap this ambience during dialogue or effects. Duck it by only about 3 dB around Lin Ming's single line. That only line is close, calm, protective, spoken toward Lin Xiao behind him while he continues looking at the creature. When both eyes become fully scarlet, add exactly one short, deep, chest-felt pressure impact with a sub-0.6-second downward tail; do not repeat it or turn it into a sustained drone. Lin Ming remains completely silent afterward. Continue with a caught monster growl, frightened inhale, taut trembling membrane, paper flutter, a short creature shriek, wet claw scrapes, glass crunches, falling fragments, and wingbeats traveling from interior near-field to distant exterior rain. Anna's exactly three blades dissolve with fine metallic fragmentation. End with Lin Xiao's restrained subjective heartbeat, uniform friction, long exhale, and rain. No “退后”, crowd, teacher, corridor voices, narration, extra dialogue, whispering, screaming, explosions, or trailer impacts.

non_diegetic_music:
N/A
```

## 关键验收

- 第2格陆沉对林晓说“站我身后。”时双眼仍为普通深色；第3格才完成红瞳。
- 第2格陆沉的脸、视线与身体始终面对怪兽，眉心微皱；不得回头或回看林晓。
- 全段唯一对白是第2格陆沉对林晓说“站我身后。”；第4格陆沉闭口沉默，禁止生成“退后”或任何额外人声。
- 第3格双眼完全转红的准确瞬间只响一次短促低沉威压音，时长不超过0.6秒，不得变成雷声、爆炸或持续能量嗡鸣。
- 第6格怪兽仍在室内，第7格连续穿窗并飞到室外；不得瞬移或反击。
- 第8格只有安娜，第9格只有林晓；林晓手掌必须清楚按在胸口并以呼气平复心跳。
- 第8格安娜右手技能严格为三把黑银刀刃，并与 `<Picture 8>` 一致；全段环境声在对白期间也不得停止。
- 无字幕、无BGM、无群众返场、无可见冲击波。
