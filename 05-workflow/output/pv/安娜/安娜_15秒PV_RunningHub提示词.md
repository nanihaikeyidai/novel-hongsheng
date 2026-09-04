# 安娜 15 秒快节奏角色 PV

## 导演卡

- 类型：角色宣传 PV 70%＋快闪编辑排版 30%
- 时长：15 秒
- 画幅：16:9 横屏
- 首帧：`安娜_PV首帧.png`
- 人物锚点：安娜的灰蓝眼睛、深海军蓝长发、白色短袖校服衬衫、深蓝领带与百褶裙、深蓝书包、冷静克制的神情
- 图形锚点：清晰可读的英文 `ANNA`，以及拆分后的 `A`、`N` 字母块
- 主色：深海军蓝、冰蓝、米白、克制的灰紫色
- 节奏：144 BPM 电子碎拍；切点贴合 4 拍、8 拍、12 拍和后续乐句
- 结尾：人物、头发、书包和字母块全部自然收束，最后约 1 秒保持稳定构图
- 禁止：新增人物、武器、红绳、红发绳、色情化机位、乱码英文、字幕、水印、人物换脸、服装改变、画风漂移

## RunningHub / H3 图生视频主提示词

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] A fast-paced commercial character PV begins from the exact subject identity, clothing, cool navy-and-ice-blue palette, horizontal composition, schoolbag position, wind-swept hair direction, and oversized readable background word "ANNA" established by <Picture 1>. Anna remains the only character. The camera pushes in with small amplitude at fast speed as one sharp gust drives her long deep-navy hair toward frame-left. She tightens her right hand slightly on the schoolbag strap without changing her calm expression. The oversized "ANNA" letters separate into clean diagonal graphic layers along the same leftward motion vector, while her face remains unobstructed. [Shot 2] At 00:01.667, the camera cuts to a close three-quarter profile of Anna against a deep-navy field. Large isolated letter blocks "N" and "A" slide from frame-right to frame-left behind her, continuing the previous motion direction. Anna turns her eyes a few degrees toward the moving letters while her head stays nearly still; a strand of hair crosses the lens and becomes the transition interface. [Shot 3] At 00:03.333, the hair strand wipes into a medium full-body side view on an off-white and ice-blue graphic plane. The camera trucks left with large amplitude at fast speed as Anna takes one controlled step toward frame-right, her schoolbag following with natural inertia. A giant hollow "A" remains fixed behind her, and its diagonal stroke aligns briefly with her moving leg before the cut. [Shot 4] At 00:05.000, the camera cuts through the triangular opening of the "A" to a low, non-sexualized waist-up frontal angle. Thin navy letter slices pass once across the foreground without covering Anna's eyes. She stops walking, lifts her chin slightly, and her hair continues forward for a moment before beginning to settle. [Shot 5] At 00:07.500, the shot cuts to a tight eye-and-face portrait. The camera arcs clockwise with small amplitude at fast speed, then decelerates. Ice-blue and white "A" and "N" shapes rotate once in the background and lock into straight horizontal alignment. Anna's gray-blue eyes hold a steady, vigilant gaze; her lips remain completely closed. [Shot 6] At 00:10.000, the shot cuts to a medium-wide composition. Anna pivots her shoulders toward the camera in one restrained motion while the schoolbag swings once and returns against her right side. The background letter fragments converge from both edges, rebuilding the exact readable word "ANNA" behind her. The camera pulls out with small amplitude as the graphic motion rapidly loses speed. [Shot 7] At 00:12.500, the shot changes to the final hero composition: Anna stands slightly right of center, matching her original identity and uniform, with the fully readable oversized word "ANNA" behind her. Her hair and skirt hem complete their final small movement, the schoolbag becomes still, and the camera decelerates to a static shot. From 00:14.000 to 00:15.000, Anna holds a calm frontal gaze in a stable, clean composition; all letter blocks remain fixed, no new action begins, and the final frame is suitable for a clean edit point.

overall_soundscape: Sharp editorial whooshes follow each moving letter layer and hair-wipe transition. Soft hair, fabric, footstep, and schoolbag-strap sounds remain synchronized with Anna's restrained movements, followed by a final low graphic impact as the word "ANNA" locks into place. All physical and design sounds fade into a clean stable tail during the final second; there is no dialogue and no vocalization.

non_diegetic_music: A 144 BPM electronic breakbeat with tight kick and snare hits, clipped bass pulses, and short ice-bright synth stabs drives the cuts. The arrangement reduces to one sustained bass-and-synth hit at 00:14.000, holding beneath the stable final composition and ending cleanly at 00:15.000.
```

## 素材映射

- `Picture 1`：`安娜_PV首帧.png`，作为 0.00 秒完整首帧；锁定安娜身份、校服、书包、配色、横屏构图和背景英文 `ANNA`。
- 不继承：任何人物设定四格边框、标注、其他角色或项目外文字。

## 生成验收

- 画幅为横屏 16:9，时长为 15 秒。
- 全片只出现一个安娜，五官、发型、校服和书包不漂移。
- 可见英文仅为 `ANNA` 或其拆分字母 `A`、`N`，无乱码和多余字幕。
- 人物动作与字母运动方向连续，不出现瞬移、肢体错误或书包消失。
- 00:14.000 后不再开始新动作，最后一秒稳定可剪辑。
