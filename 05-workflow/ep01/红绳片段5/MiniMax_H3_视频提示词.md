# 《红绳》片段5｜MiniMax H3 官方模板提示词

## 生成设置

- 模式：Ref2VA 多图与音色参考生成；15秒；16:9
- 声音：学生尖叫、撤离脚步、桌椅碰撞、物品坠落＋王老师一句可见对白；无BGM；无字幕
- 连续性：直接承接片段4末格；怪兽已在教室地面展翼，学生随后才开始撤离

## 素材对应

- `<Picture 1>` = `@图片1_陆沉.png`
- `<Picture 2>` = `@图片2_林晓.png`
- `<Picture 3>` = `@图片3_王老师.png`
- `<Picture 4>` = `@图片4_雨天教室.png`
- `<Picture 5>` = `@图片5_人物座位说明图.png`
- `<Picture 6>` = `@图片6_故事板.png`
- `<Audio 1>` = `@音频1_王老师.wav`

## 可直接粘贴的官方六段式提示词

```text
subject_definitions:
<Subject 1> is Lin Ming from <Picture 1>, preserving his short black hair, youthful male face, tall build, white school shirt, dark trousers, and rear window-row identity.
<Subject 2> is Lin Xiao from <Picture 2>, preserving her long dark hair, youthful female face, white-and-blue school uniform, and seat directly in front of Lin Ming near the window.
<Subject 3> is Wang Laoshi from <Picture 3>, an attractive thirty-year-old female teacher with an adult face, elegant professional clothes, a clear authoritative presence, and no masculine traits.
<Subject 4> is the rainy classroom from <Picture 4>, spatially constrained by <Picture 5>, now preserving the shattered right-side window, overturned desk, broken glass, rain intrusion, middle aisle, and rear-door evacuation route inherited from the preceding segment.
<Subject 5> is the adult-sized black-winged creature already standing on the classroom floor in the right-side window zone, with charcoal skin, broad membrane wings, hooked claws, pointed ears, and dark-red eyes.
<Picture 6> is the storyboard reference for [Shot 1] through [Shot 4], defining the panic onset, Wang Laoshi's guidance, one-way evacuation, Lin Xiao's entrapment, and Lin Ming's final sightline.
<Audio 1> is the voice-timbre reference for <Subject 3> (S1); it supplies only her mature female teacher timbre and does not supply words, timing, emotion, pauses, or background noise.

summary:
[reference generation + audio reference] The target is a fifteen-second 2D anime cinematic evacuation sequence. Students panic only after seeing <Subject 5>, <Subject 3> directs them toward the rear door using <Audio 1> as a timbre reference, <Subject 2> becomes trapped among desks, and <Subject 1> notices that she has not escaped. <Picture 6> controls the shot flow.

retention_analysis:
<Subject 1> (appears in [Shot 4]): fully_preserved - Lin Ming's identity and rear-row position remain stable; he only stops and looks, without beginning the rescue.
<Subject 2> (appears in [Shot 3] and [Shot 4]): fully_preserved - Lin Xiao's identity and window-side position remain stable as the desk layout and moving crowd block her route.
<Subject 3> (appears in [Shot 2]): fully_preserved - Wang Laoshi remains a thirty-year-old female teacher and stands beside, not inside, the evacuation path.
<Subject 4> (appears throughout): fully_preserved - the rainy damaged classroom, shattered window, desks, middle aisle, rear door, and cold blue-grey lighting remain spatially consistent.
<Subject 5> (appears in [Shot 1] and background views): fully_preserved - the creature remains on the classroom floor near the shattered window and does not teleport, attack, or block the rear door.
<Picture 6> ([Shot 1] through [Shot 4] storyboard structure): fully_preserved - the panic, guidance, entrapment, and recognition beats remain in order without storyboard borders or annotations.
<Audio 1>: reference - Wang Laoshi's dialogue uses its mature female teacher timbre without copying the source signal or source words.

detailed_description:
The target uses high-detail 2D anime cinema with clean cel shading, hand-drawn classroom backgrounds, cold rainy light, wet reflections, and clear crowd motion. It begins from the exact aftermath of Segment 4: the window is shattered, <Subject 5> is already fully inside on the floor with wings spread, and all students are still present.
[Shot 1] A medium-wide shot shows students finally registering the creature. A sharp collective intake of breath breaks into overlapping frightened screams. Students spring from their seats; chair legs scrape and knock together, desks rattle, pencil cases and books fall, and the students closest to the rear door enter the middle aisle first. The camera pans toward the rear door with large amplitude at fast speed. Everyone runs away from <Subject 5>; nobody runs toward it, falls underfoot, fights, or begins moving before the screams.
[Shot 2] At 00:03.800, the camera cuts to <Subject 3> (S1) stepping to the side of the aisle and raising one arm to channel the flow without blocking the door. Her adult female teacher voice uses the timbre referenced from <Audio 1>, louder than the panic, firm, urgent, and clearly articulated at a slightly fast pace. She says once, with accurate Mandarin lip sync, <d>[Chinese] 从后门出去！不要挤！</d> The nearest screams and impacts briefly lower in level during the line while rapid footsteps continue underneath. As she closes her mouth, the crowd obeys and keeps a single direction toward the rear exit.
[Shot 3] At 00:07.300, a tracking medium shot follows <Subject 2> rising from her window-side seat. A fallen desk blocks one side and the reverse-moving evacuation stream closes the aisle. She takes one step, checks both directions, then retreats between the desks without falling or being touched by the creature. A book lands beside her shoe, a desk edge knocks another chair, and her breath becomes short and audible.
[Shot 4] At 00:11.300, the camera cuts to the rear-row edge where <Subject 1> stops while the last dense cluster of running students passes in front of him. Their footsteps and screams move toward the hallway and begin to recede. A sightline match reveals <Subject 2> still trapped near the broken window, then returns to Lin Ming's fixed, alarmed gaze. He remains in place and does not run yet. The final state holds most students outside, Wang Laoshi still directing the final flow, Lin Xiao trapped, Lin Ming aware, and the creature still inside the right-side classroom zone.

overall_soundscape:
The sound begins with layered shocked gasps and student screams, followed by rapidly multiplying chair scrapes, desk impacts, dropped books, pencil cases, and dense running footsteps aimed toward the rear door. Rain and the creature's low growl remain underneath. The crowd noise briefly ducks around Wang Laoshi's visible line, then the screams and footsteps move into the hallway and recede by the final shot.

non_diegetic_music:
N/A
```

## 禁止项与验收

- 王老师台词只能出现一次，必须由画面中的王老师说出，使用 `<Audio 1>` 仅迁移音色；禁止复述源音频原台词或噪声。
- 禁止学生朝怪兽奔跑、堵死后门、互相踩踏；禁止林晓受伤、陆沉提前冲刺、安娜能力或红瞳出现。
- 声音验收：先看见怪兽并惊叫，再起身逃跑；尖叫、椅响、脚步和物品掉落具有远近变化；对白必须清晰压过现场声但不能像旁白。
