# 《红绳》片段4｜MiniMax H3 官方模板提示词

## 生成设置

- 模式：Ref2VA 多图参考生成；15秒；16:9
- 声音：同步环境音、群体惊叫与动作音；无人物台词；无BGM；无字幕
- 连续性：入点为完整窗户与安静课堂；出点为怪兽已经完全落在教室地面并展翼，学生尚未撤离

## 素材对应

- `<Picture 1>` = `@图片1_黑翼怪兽.png`
- `<Picture 2>` = `@图片2_王老师.png`
- `<Picture 3>` = `@图片3_雨天教室.png`
- `<Picture 4>` = `@图片4_人物座位说明图.png`
- `<Picture 5>` = `@图片5_故事板.png`

## 可直接粘贴的官方六段式提示词

```text
subject_definitions:
<Subject 1> is the adult-sized black-winged creature defined by <Picture 1>, preserving its charcoal-black humanoid body, broad membranous wings, hooked claws, pointed ears, and dark-red eyes without inheriting the reference background or pose.
<Subject 2> is Wang Laoshi, the attractive thirty-year-old female homeroom and Chinese teacher defined by <Picture 2>, preserving her adult face, elegant professional clothing, composed posture, and authoritative presence.
<Subject 3> is the rainy senior-high classroom defined by <Picture 3> and spatially constrained by <Picture 4>, with an intact right-side window wall at the opening, rows of desks facing the podium, twenty-four to thirty ordinary students, cold blue-grey rainy daylight, rain trails on the glass, and no pre-existing damage.
<Picture 5> is the storyboard reference for [Shot 1] through [Shot 5], defining the warning, impact, inward glass burst, creature entry, floor landing, wing spread, shot order, and compositions.

summary:
[reference generation] The target is a fifteen-second 2D anime cinematic sequence in which <Subject 1> breaks through the intact window of <Subject 3>, crashes into an empty desk, lands fully inside the classroom, and spreads its wings while <Subject 2> and the students react. <Picture 5> controls the shot sequence and action causality.

retention_analysis:
<Subject 1> (appears in [Shot 2], [Shot 3], [Shot 4], [Shot 5]): fully_preserved - the creature's adult scale, charcoal body, membrane wings, claws, ears, and red eyes remain stable while its pose changes from a compact dive to an indoor landing and full wing spread.
<Subject 2> (appears in [Shot 1] and [Shot 5]): fully_preserved - Wang Laoshi remains an adult female teacher at the podium and reacts without becoming a student or leaving her position.
<Subject 3> (appears throughout): partially_preserved - the rainy classroom structure, desk orientation, crowd, and cold light remain stable while the right-side window becomes shattered and one empty desk is overturned by the impact.
<Picture 5> ([Shot 1] through [Shot 5] storyboard structure): fully_preserved - the warning-to-entry action order, viewpoints, and final indoor wing-spread state are retained without rendering panel borders, arrows, numbers, or notes.

detailed_description:
The target uses high-detail 2D anime cinema: clean cel-shaded characters, hand-drawn classroom backgrounds, cold blue-grey rainy light, restrained highlights on wet glass and wing membranes, and physically readable action without blood, live-action texture, or 3D rendering.
[Shot 1] A close shot frames the intact rain-covered window of <Subject 3>. The room is initially calm. Steady rain taps the glass; then a low, heavy wingbeat approaches from outside and gradually masks the rain. The pane vibrates, rain trails tremble sideways, and a huge shadow sweeps across it. Several window-side students turn with confused gasps while chalk stops with a dry click in <Subject 2>'s raised hand at the podium.
[Shot 2] At 00:03.200, the camera cuts outside to a fast three-quarter view of <Subject 1> folding its broad wings tightly around its body and driving straight toward the right-side classroom window. Each accelerating wingbeat produces a deep pressure pulse. The creature must still be outside during this approach; the window remains intact until physical contact.
[Shot 3] At 00:06.000, the creature's shoulder and folded wing strike the pane. A single violent impact comes first, followed immediately by the sharp glass explosion. The window fractures outward from the contact point and shards, cold rain, and dust spray inward. Students nearest the window recoil and release the first short, startled screams; chair legs scrape as bodies jerk backward. The camera shakes once with small amplitude, then tracks the creature through the opening.
[Shot 4] At 00:09.000, <Subject 1> passes completely through the broken window plane into the classroom and collides with one unoccupied desk. Wood and metal slam sideways, books jump from the desktop, and wet wing edges sweep droplets into the room. The creature's full body clears the wall before its feet descend; it does not remain perched in the window or outside in the rain.
[Shot 5] At 00:12.000, a low-angle medium-wide shot shows <Subject 1> planting both hooked feet on the classroom floor amid glass fragments. Its claws crunch the shards, its weight settles, and only then do its black wings open to nearly half the classroom height. The creature releases a low guttural roar. A wave of shocked gasps and frightened screams rises from the still-present students, but nobody begins the evacuation yet. <Subject 2> remains by the podium, tense and alert. The final frame holds the creature fully inside the classroom with the shattered window behind it.

overall_soundscape:
Steady rain and quiet classroom room tone open the video before deep approaching wingbeats dominate. Glass vibration escalates into one heavy impact, an inward glass burst, desk-and-chair crashes, falling books, claws grinding fragments, the creature's low roar, and a growing layer of student gasps and startled screams. All sound follows the visible physical cause; no evacuation footsteps occur before the final frame.

non_diegetic_music:
N/A
```

## 禁止项与验收

- 禁止跳过“预警→接触→玻璃爆裂→穿越窗墙→室内落地→展翼”。
- 禁止怪兽从门或黑板方向进入、落地后仍处在窗外、学生提前撤离、王老师离开讲台。
- 禁止男性王老师、血腥、红瞳能力、安娜刀刃、摄影写实、3D、晴天、字幕、水印和故事板标注。
- 音效验收：撞击必须先于玻璃爆裂；学生只在看见破窗和怪兽落地后惊叫；结尾尚无成片撤离脚步。
