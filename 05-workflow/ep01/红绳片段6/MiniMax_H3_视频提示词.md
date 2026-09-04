# 《红绳》片段6｜MiniMax H3 Ref2VA 提示词

## 生成设置

- 模式：Ref2VA 多图参考生成
- 时长：15秒
- 画幅：16:9
- 画面：高精度彩色日漫电影感
- 声音：同步环境音与动作音；无对白、无BGM、无字幕
- 正式视觉基准：`@图片6_故事板.png`，已经用户确认

## 素材对应

- `<Picture 1>` = `@图片1_林晓.png`
- `<Picture 2>` = `@图片2_安娜.png`
- `<Picture 3>` = `@图片3_黑翼怪兽.png`
- `<Picture 4>` = `@图片4_雨天教室.png`
- `<Picture 5>` = `@图片5_人物座位说明图.png`
- `<Picture 6>` = `@图片6_故事板.png`

## 可直接粘贴的官方六段式提示词

```text
subject_definitions:
<Subject 1> is Lin Xiao from <Picture 1>, preserving her face, high dark-brown ponytail tied with a long red ribbon, white short-sleeve school shirt with navy trim, navy tie, navy pleated skirt, red cord bracelet, and teenage proportions.
<Subject 2> is Anna from <Picture 2>, preserving her face, very long deep-blue hair, cool grey-blue eyes, restrained expression, and rear-row identity; in the final reaction shot she wears the light grey-blue school blazer visible in panel 9 of <Picture 6>.
<Subject 3> is the black-winged creature from <Picture 3>, preserving its near-adult-human scale, charcoal humanoid body, black membrane wings, tall pointed ears, dark-red eyes, sharp teeth, and hooked claws.
<Subject 4> is the severely damaged rainy classroom from <Picture 4>, spatially constrained by <Picture 5>, preserving the shattered window, overturned desks, scattered books, broken glass, cold blue-grey rain light, and fixed window-side topology.
<Picture 6> is the user-approved storyboard reference for [Shot 1] through [Shot 5]. Its nine panels define the shot order, composition, framing, character placement, progressive threat distance, Lin Xiao's body-action insert, the suspended claw, and Anna's final seated reaction.

summary:
[reference generation] The target is a fifteen-second 2D anime cinematic sequence that follows all nine panels of <Picture 6>. Inside <Subject 4>, <Subject 3> turns and locks onto <Subject 1>, advances step by step across broken glass, corners her against the desks, and suspends one claw above her without contact. <Subject 2> remains seated in the rear row and prepares to intervene. Character identities come from <Picture 1>, <Picture 2>, and <Picture 3>, while composition and action timing come from <Picture 6>.

retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2], [Shot 3], [Shot 4], and the background of [Shot 5]): fully_preserved - Lin Xiao's identity, red-ribbon ponytail, uniform, trapped window-side position, defensive retreat, and uninjured condition remain stable.
<Subject 2> (appears in [Shot 5]): partially_preserved - Anna's face, deep-blue hair, eyes, calm temperament, and seated rear-row position are preserved, while the light grey-blue blazer shown in <Picture 6> is used as the shot-specific outer layer.
<Subject 3> (appears throughout): fully_preserved - the creature's design, scale, floor contact, gradual approach, wing silhouette, and suspended hooked claw are retained without teleportation or attack contact.
<Subject 4> (appears throughout): fully_preserved - the shattered rainy classroom, debris, overturned desks, cold light, and empty post-evacuation occupancy remain consistent.
<Picture 6> ([Shot 1] through [Shot 5] storyboard structure): fully_preserved - all nine panel compositions and their order are used as the visual plan, while panel borders, numbers, and annotations are omitted from the moving video.

detailed_description:
The target uses high-detail Japanese 2D anime cinema with delicate cel shading, crisp stable linework, hand-painted classroom backgrounds, cold blue-grey rain light, wet reflections, and restrained supernatural tension. The classroom remains severely damaged and visually empty; Wang Laoshi and ordinary students are never visible, and Lin Ming remains off-camera.

[Shot 1] A medium rear-side view follows panels 1 and 2 of <Picture 6>. <Subject 3> is already fully inside <Subject 4>, standing on the classroom floor near the shattered window. Its broad wing crosses the frame and drags over a wet desktop, nudging loose glass fragments. <Subject 1> is the only visible human, small in the distant window-side desk zone. The creature turns its head and shoulders toward her. The camera then matches to a lower frontal medium close-up: <Subject 3> crouches, half-opens its wings, fixes its dark-red eyes on Lin Xiao, and shifts its weight forward. Rain and a leathery scrape remain audible.

[Shot 2] At 00:03.000, the view follows panels 3 and 4. A low camera retreats through the narrow desk aisle as <Subject 3> plants one clawed foot among broken glass and steps past an overturned desk. Glass crunches and slides outward. <Subject 1> retreats at frame right and reaches the desk behind her. A frontal medium-wide continuation shows the creature advancing without a jump cut, its wings partly folded to fit between desks. It stops outside Lin Xiao's desk pocket, still on the classroom floor and still between her and the shattered window.

[Shot 3] At 00:06.000, the view follows panels 5 and 6. The camera cuts to the torso-to-knee body-action insert used by <Picture 6>: <Subject 1>'s backward leg hits the desk edge, abruptly stopping her. Both arms extend behind her and her hands catch the neighboring desktop edges. The framing clearly communicates the impact and balance recovery without changing her uniform proportions or exposing underwear. A frontal close-up then reveals her tense face and both hands spread hard against the wet desktop. She breathes rapidly, remains silent, and stays uninjured.

[Shot 4] At 00:09.000, the view follows panels 7 and 8. From behind Lin Xiao's shoulder and red-ribbon ponytail, the camera slowly pushes toward <Subject 3>. The creature leans down, bares its teeth, and spreads its wings enough to block the rainy window light. It raises one hooked claw into the top of frame. The claw stops above and in front of Lin Xiao with a clearly visible air gap; it never touches, scratches, or grabs her. The creature remains grounded inside the classroom.

[Shot 5] At 00:13.000, the camera cuts to panel 9 of <Picture 6>, a fixed rear-row medium-wide composition. <Subject 2> sits in the foreground wearing the light grey-blue school blazer shown in the storyboard, her long deep-blue hair falling over her shoulders. She looks sideways toward the distant <Subject 3> and <Subject 1>, lowers her right shoulder, presses one hand against the seat or desk, and shifts her weight forward while her hips remain on the chair. In the background, the creature's claw remains suspended over Lin Xiao. The shot ends before Anna stands or manifests any power.

overall_soundscape:
Steady rain and hollow post-evacuation classroom resonance continue throughout. During the opening, the last off-screen evacuation footsteps fade down the hallway. Synchronized physical sounds include wing membrane scraping a desk, glass fragments sliding and crunching under hooked feet, heavy grounded steps, Lin Xiao's leg striking the desk, a brief desk scrape, palms pressing wet wood, rapid breathing, the creature's low growl and heavy breath, and a faint clothing rustle as Anna shifts her seated weight.

non_diegetic_music:
N/A
```

## 禁止项与验收

- `@图片6` 的九格顺序、景别和构图必须保留；成片不得显示宫格边框、编号或标注。
- 普通学生、王老师和陆沉均不得入镜；撤离脚步只能来自画外走廊。
- 怪兽全段在教室地面，不得瞬移、飞行、返回窗外或直接扑击。
- 利爪只抬起并悬停，不得接触林晓，不得出现伤口、血液或衣物破损。
- 第5格必须是撞桌与双手撑桌的动作插入镜头；第9格安娜保持坐姿和浅灰蓝外套，不得提前站起或凝刃。
- 身份验收：林晓红发带高马尾、安娜深蓝长发、怪兽暗红眼与黑膜翼跨镜头稳定。

