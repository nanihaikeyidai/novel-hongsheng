---
name: "tudou-ai-short-drama"
description: "把剧本分步做成 AI 短剧：可选参考视频或参考图片拆美学，审剧本算时长，出人物三视图设定图与场景道具 Seedream 提示词，根据剧本动作与空间动态推导导演分镜与表演设计，用 tudou-single-h3 规则出中英双版 MiniMax H3 视频提示词。"
---

# 土豆 AI 短剧导演流程（剧本 → 资产 → 分镜表演 → H3 视频提示词）

用户给一个剧本（可附参考视频或参考图片），本流程带用户一步一步做出 AI 短剧：图片资产用 Seedream（默认 Seedream 5.0 pro），视频用 MiniMax H3。本流程只写提示词与导演方案，不替用户生成图片或视频、不消耗生成额度。

## 总原则（全程有效）

1. **分步推进，每步等用户回传。** 每一步结束时说清楚「请把什么发给我」，等用户回传生成好的图片或确认后再进入下一步。不要一口气输出全部步骤。
2. **台词一字不改。** 用户剧本里的每一句台词，文字、顺序、说话人都不得改动、删减或合并；只有用户明确同意时才可删改。数字等容易念错的写法不改原文，只在声音说明里注明读法（例：「28」读作「二十八」）。台词在三处核对：第 2 步建台词表、第 5 步分段、第 6 步交付前。
3. **每条资产提示词都必须加美学提示词。** 用户没有提供参考视频或参考图片时：人物设定图把第 1 步 B 的「固定美学·人物资产版」放在提示词**开头**，不加画幅词；场景、道具、修图在**末尾**加「固定美学提示词」，其后再加画幅词。两者都一字不改、不得省略。用户提供了参考视频或参考图片时，改用第 1 步 A 提取出的人物资产版或镜头版锚定词，位置规则相同。
4. **只要美学风格，人物不化妆。** 男女老少共用同一套美学；人物的粉嫩通透感只来自曝光、调色、柔光与肤质（见第 1 步 B），任何提示词里都不写眼影、腮红、红晕、唇色、妆容。
5. **提示词只写画面指令。** 所有交给 Seedream 和 H3 的提示词，只写要画什么、怎么画：不写标题或分节名（如「整体画布与背景」）、不写铺垫语（如「具体解析如下」）、不写目的说明（如「以此突出主体」「形成规范的视觉基准」）。用户提供的版式或模板若是说明文档，先改写成连贯的画面指令再使用，不原样粘贴。
6. **空间由剧本原生驱动，锁定卡为全片唯一来源。** 坚决拒绝无脑套用“柜台/桌子/固定正反打”模板。全片的人物站位、动态走位、机位视点、画面左右、视线关系、地标与光线方向，必须根据剧本的实际空间形态（对峙、运动、开放场域或独角戏）进行专业场面调度推导，并完全固化在第 5 步定稿的「空间锁定卡」中；每段视频提示词原文复制同一份卡片文字，不得改写、缩写或按单段重新描述。
7. **不做表情集**，除非用户主动要求；表情写进每个镜头的视频提示词。
8. **用户可见的说明一律用中文**；视频提示词按第 6 步要求给中英两版。
9. **第 5、6 步必须遵守本文件末尾「附录：tudou-single-h3 原文（不得修改）」的全部规则。** 本流程要求的多段输出、导演说明、中英双版、空间锁定卡，视为用户明确提出的要求；除此之外，每段视频提示词的格式、六个标题、`<d>` 写法、时间轴、听者反应、语速预算、禁止项等，一律按附录原文执行。
10. 当前对话里可用 `AskUserQuestion` 时，用它提选择题；不可用时用一句话文字提问。

---

## 第 0 步：开工确认（只问一次）

拿到剧本后，先用一句话说明接下来要做什么，然后一次性确认下面几项，每项给出默认值，用户可直接确认或修改：

| 项目 | 默认值 |
| --- | --- |
| 画幅 | 16:9 横屏 |
| 视频模型与单段时长上限 | MiniMax H3，单段最长 15 秒 |
| 图片模型 | Seedream 5.0 pro |
| 台词规则 | 一字不改 |
| 目标时长 | 以剧本标注为准，第 2 步核算后再由用户决定取舍 |
| 参考视频或参考图片 | 有则走第 1 步 A，没有则走第 1 步 B（固定美学） |

画幅以用户确认的为准，即使剧本里写的是另一种画幅。确认后进入第 1 步。

**画幅词**（后续场景、道具、修图、视频全局视觉锁定使用）：16:9 写「横屏16:9电影构图」，9:16 写「竖屏9:16构图」，其他画幅同理。

---

## 第 1 步：美学风格

### A. 用户提供了参考视频或参考图片：提取美学

参考图片（剧照、截图、风格图）与参考视频走同一套拆解：**只有图片时跳过第 1、2 条**，直接用 Read 逐张查看，图片少于 3 张时提醒用户「样本少，提取的美学可能不稳定」；视频和图片都有时一起看，冲突处以用户指定的为准，未指定时问用户。

1. 参考视频：用 ffprobe 查看时长、分辨率、帧率；只分析前 30 秒（视频不足 30 秒则全部）。
2. 参考视频抽帧（每秒一帧拼成联系表，再取几张全分辨率截图看细节）：
   ```bash
   OUT=<scratchpad>/frames; mkdir -p "$OUT"
   ffmpeg -v error -i <视频> -t 30 -vf "fps=1,scale=480:-1,tile=3x5" -frames:v 2 "$OUT/sheet_%02d.jpg"
   ffmpeg -v error -ss 10 -i <视频> -frames:v 1 "$OUT/f10.png"
   ffmpeg -v error -ss 21 -i <视频> -frames:v 1 "$OUT/f21.png"
   ```
   用 Read 逐张查看联系表与截图。
3. 按六个维度出拆解表，每项写「原片怎么做」和「搬到本剧场景怎么用」：光线、色彩、镜头（焦段、景深、前景遮挡、机位高度、构图规律）、质感（柔焦、颗粒、皮肤）、环境细节、文字与字幕样式。
4. 另出一张「导演语言拆解表」（只用于第 5 步分镜与表演设计参考，不提取成锚定词、不进任何提示词）：每镜运镜方式（固定/推/拉/摇/移/跟/手持）与机位动静；剪辑节奏（总镜头数、平均镜头时长、节奏最快与最慢处）；景别序列（镜头如何从全景递进到特写、每镜承担什么信息）；表演调度（人物走位、视线方向、听者反应的给法）。
5. 产出两版风格锚定词（人物一律不化妆，只提取调色、光与肤质；即使参考视频里的人带妆，也不提取眼影、腮红、唇色）：
   - **镜头版**：完整风格，用于场景、道具、修图与视频全局视觉锁定，末尾接画幅词。镜头版里的「人物肤质句」必须与人物资产版逐字相同，保证设定图与成片里的人是同一种质感。
   - **人物资产版**：用于人物设定图，按第 1 步 B「固定美学·人物资产版」的结构改写（人物肤质句与镜头版逐字相同）：保留高调平光、低对比、柔焦但五官清楚、中性浅灰背景这一套，只把曝光亮度、调色倾向、肤质与颗粒换成参考视频里人物近景的样子；不得沿用镜头版的逆光、浅景深与环境冷暖色。放在人物设定图提示词开头，不加画幅词。

### B. 用户没有提供参考视频或参考图片：使用固定美学（必须）

不再分析。向用户简要展示下面的拆解表与固定美学提示词后进入第 2 步。

**固定美学（2026-10-26 v2 更新，修复过曝/过柔/颗粒过重问题）**：国产青春偶像剧质感，暖桃粉色调胶片调色为基底，叠加梦幻电影氛围（光影层次）；不绑定具体时间与光线方向（夜戏用室内暖灯、日戏用自然光，光源由各场景空间设计决定）。已移除：高调过曝描述、薄雾空气感、bokeh光斑、美颜滤镜感。

**固定美学提示词（一字不改，所有资产必须加入）**
```
国产青春偶像剧质感的写实摄影，梦幻电影氛围，光影层次丰富细腻，画面干净清透，整体是柔和的暖桃粉色调胶片调色，粉彩，柔焦但不失细节，平光、低对比，暗部轻微抬起、不死黑，细腻胶片颗粒，哑光质感，85mm浅景深
```

**两套美学如何统一**：人物设定图只负责「这个人长什么样」，成片的光与色由场景图和视频决定，它们都用固定美学。两套美学共用同一层质感（柔焦、暖桃粉色调胶片调色、细腻胶片颗粒、低对比、暗部抬起、哑光质感），只有光不同：人物设定图是均匀正面漫射光棚拍，场景与视频是按场景空间设计的照明（夜戏用室内暖灯、日戏用自然光）。改动任何一套美学里的调色或质感词时，另一套同步修改，保持两边一致。

**只要美学风格，不化妆。** 男女老少共用同一套美学。人物的粉嫩通透感只来自曝光、调色、柔光溢出与肤质，任何提示词里都不写眼影、腮红、红晕、唇色、妆容。

**固定美学·人物资产版（人物设定图专用，一字不改）**
```
国产青春偶像剧质感的写实人像摄影，画面干净清透，整体是柔和的暖桃粉色调胶片调色，粉彩，柔焦但五官清楚，细节柔和不锐利，柔和均匀的正面漫射光，平光、低对比，暗部轻微抬起，头发保留深色，细腻胶片颗粒，哑光质感
```
人物资产版按《不烧心奶茶店》实测的三视图样图校准（2026-10，经三轮测试定稿），和场景用的固定美学分开：人物设定图要求中性高调平光，暖金逆光、青绿冷色、薄雾与浅景深留给场景图与视频去做，以免光被画死在人物身上。人物设定图如果直接加完整的固定美学，背景会被画成虚化的户外场景，人物带逆光光晕，版式被破坏。

修改人物资产版或写人物字段时避开以下词（实测会跑偏）：

| 词 | 会导致 |
| --- | --- |
| 暖琥珀、米灰、暖灰、奶油白为主色调 | 画面整体发黄 |
| 冷暖对比、青灰 | 背景发冷 |
| 单独写「粉调」（不带「暖桃」、不说明是调色） | 背景偏紫 |
| 发丝金边、逆光 | 明显光晕，头发出橙金色高光 |
| 冷白、瓷白、水润唇、眼睛明亮有神 | 冷白锐利的韩系脸 |
| 真实皮肤肌理 | 素颜路人脸 |
| 眼影、腮红、红晕、唇色、甜美美颜感（脸上的颜色写成妆） | 画出妆容，男性尤其明显 |
| 全部视图清晰对焦 | 画面太锐，与柔焦冲突 |
| 人物区域提亮、四边压暗 | 聚光与暗角 |
| 宽度不超过四分之一、肩部下缘淡出 | 特写缩成飘在半空的小头像 |
| 空气感强、柔光镜拍摄、柔光溢出光晕、极低对比、暗部与头发偏灰 | 整体过曝发白、蒙一层灰雾，深肤色与深色衣物被压成奶白灰（男性尤其明显） |
| 人物某侧轮廓的暖色柔光 | 变相逆光，发丝一侧发橙发亮 |
| 正常曝光、面部保留明暗层次 | 变成普通摄影，失去高调粉嫩的偶像剧感 |

**加法（无参考视频或参考图片时一律如此）**

| 提示词类型 | 加什么、加在哪 |
| --- | --- |
| 人物三视图设定图 | 固定美学·人物资产版，放在提示词开头，不加画幅词 |
| 场景、道具特写、修图 | 固定美学提示词，＋「，」＋画幅词，放在末尾 |
| 视频提示词的全局视觉锁定 | 固定美学提示词，＋「，」＋画幅词，放在末尾 |

**固定美学拆解（供说明与 HTML 文档使用）**

| 维度 | 做法 |
| --- | --- |
| 光线 | 柔和曝光，不过曝；夜戏场景用室内暖色灯光照明，日戏用自然光漫射，明暗过渡细腻、光影层次丰富 |
| 色彩 | 暖桃粉色调胶片调色：粉彩；场景陈设保留色彩层次（奶白墙面、浅米/浅蓝家具、原木色茶几与地板、绿植点缀），暗部轻微抬起、不死黑，低对比；不要求强冷暖对比，窗外夜色仅作微弱层次 |
| 镜头 | 85mm 左右人像焦段，浅景深；前景清晰、背景柔化；常用单人近景/特写承载表情、正反打对话、过肩双人镜头 |
| 质感 | 梦幻电影氛围：柔焦但不失细节、细腻胶片颗粒、哑光质感；人物不化妆，粉嫩通透感来自整体调色与柔光 |
| 环境 | 生活化细节密集写实（沙发、茶几、包、拖鞋、冰箱、绿植等居家物件），背景虚化 |
| 文字 | 对白字幕为白色无衬线、底部居中（后期添加） |

---

## 第 2 步：审剧本

1. **建台词表**：把剧本所有台词逐句编号（序号、说话人、原文、剧本里的表演标注如「惊讶」「严肃」「递奶茶」）。这张表是全流程的台词唯一来源。
2. **人物清单**：每个有台词或出镜的角色，记下剧本给出的年龄、外形、性格、语速与表演要求，以及**服装是否在某处发生变化**（换装的位置与新服装；会在第 3 步多出换装设定图）。
3. **时长核算**：
   - 把剧本标注的单镜时长加总，与剧本声称的总时长对比；
   - 按字数核算实际需要的时长（正常约 4 字/秒，激动 5–6 字/秒，克制 2.5–3 字/秒，再加停顿、反应与余波），给出「实际约需多少秒」；
   - 找出说不完的单句（例：2 秒要念 20 个字）。
4. **叙事结构核验**（短片成败核心，只提示不擅改台词）：
   - 钩子：第一个镜头/第一句台词能否在 3 秒内让观众知道「发生了什么有意思的事」；无钩子时给出建议方向（如用冲突最激烈的一句开场、或用一个反常动作开场）；
   - 冲突与升级：中段是否有明确的目标—阻力，压力是否逐级上升而非原地重复；
   - 反转/落点：结尾是否有情绪落点（反转、余韵或决定），能否一句话说清「这片子讲了一个什么变化」。
   结论写进问题清单，每项给「现状→建议方向」，不改动台词原文。
5. **查穿帮**：前后镜头动作、道具状态矛盾（例：上一镜已放下擦杯布，下一镜仍在擦杯）；也查剧本里的空间矛盾（例：人物前一镜在柜台内、后一镜无交代地出现在柜台外）。
   同时按场景记录空间与动作节拍：地点边界和可见地标、人物初始位置、每次入画/出画与移动的起终点、交互对象、视线目标、道具状态变化。剧本未写明的方向先标为待设计，不把示例里的柜台或正反打代入剧情。
6. **道具清单**：台词与动作里提到的每个道具（菜单、海报、容器、器具等），以及道具上必须出现或不能出现的文字。
7. **道具文字与台词冲突检查**：例：台词说「我这 28」，菜单就不能写 12 元；台词说「别人家用奶精」，配方纸就不能写奶精。
8. 输出：台词表摘要、问题清单（含叙事结构核验结论）、空间动作节拍表、道具清单、时长结论。时长与目标不符时，把选择交给用户（接受更长成片 / 由用户指定删改哪些台词），用户未明确同意前不删任何台词。

---

## 第 3 步：人物三视图设定图（Seedream）

1. 按剧本人物清单，每个角色一条设定图提示词。版式：横向宽幅，整幅为同一块无缝背景；左侧三分之一宽为正面头胸特写，占满画面整个高度（头顶接近上缘、截至胸口、下缘到底边）；右侧三分之二宽为全身正面、正侧面、背面三视图，人物高度约为画面的九成；**正面全身视图的脸用浅灰色平涂遮盖**，让 H3 只从左侧特写一个来源取脸，正侧面保留清晰侧脸。美学提示词放在开头（无参考视频或参考图片：固定美学·人物资产版；有参考视频或参考图片：第 1 步 A 的人物资产版）。模板（只写画面指令，按总原则第 5 条，不加标题与解释）：
   ```
   <美学提示词>。横向宽幅角色三视图设定图，整幅画面是同一块无缝连续的背景：均匀的浅灰色，灰中带一点点藕粉色，几乎无渐变，墙面与地面无缝过渡，看不到墙地交界线，没有地平线，无聚光、无暗角，背景干净无任何场景、道具、植物、纹理或光斑。画面左侧三分之一宽是人物正面头胸特写，占满画面整个高度：头顶接近画面上缘，向下截至胸口，下缘直接到画面底边，脸部大而清楚，呈现五官、发丝走向与上衣领口材质，特写右缘柔和融入背景，同样柔焦不锐利；画面右侧三分之二宽是同一人物的全身正面、正侧面、背面三视图，每个全身视图的人物高度约为画面高度的九成，头顶紧贴画面上缘下方，脚底紧贴画面下缘上方，三个视图在右侧区域内均匀分布，间距一致且留有空隙，脚底踩在同一条水平线上，头顶高度一致，脚下只有很淡的柔和接地阴影；正侧面视图身体朝向画面左侧。特写与三视图共用同一块背景，之间没有分隔线、色块边界或独立的底色区域。正面全身视图的面部用浅灰色平涂完全遮盖，不显示五官；正侧面视图保留清晰侧脸。三个全身视图都是自然站姿，双臂自然垂放于身体两侧，双手空着，不拿任何物品。<国籍><性别>，<年龄>，<身份>，<身材与头身比>，<发型发色>，<脸型五官>，<表情基调>；<上装>，<下装>，<鞋>，<配饰及其位于角色自身哪一侧，或「无配饰」>。特写与三视图为同一人物，发型、服装完全一致，真实人体比例。无文字，无水印，无边框分格线。
   ```
   - 有参考视频或参考图片时，只替换开头的美学提示词，背景一句保持不变。
   - **锁定满意的脸**：用户喜欢某张已生成图里的脸时，把那张图（最好裁成左侧特写）作为 Seedream 参考图上传，并在人物字段前加一句「人物与参考图中的<女性/男性>为同一人，脸型、五官、发型完全一致，只采用参考图的人物长相，不采用参考图的光线、调色与背景。」；其余字段照写。
   - **换装**：剧本里同一角色换了服装（隔天、换工作服、变装等），为每一套服装各出一张设定图，脸、发型、体型的字段逐字不变，只改服装字段；编号 ①（第一套）、①-B、①-C……，并在人物锁定卡里写明每套用于哪些镜头（第 5 步分段后补写到哪些段）。
   - 人物一律不化妆，男女同一套美学；肤色、肤质由美学决定，人物字段不写肤色、妆容、唇色、腮红等。只有剧情需要特殊肤色（如晒黑的体育生）时才在 <脸型五官> 后补写。
   - <身份> 只写身份（如「大学生」「奶茶店老板」），不写正在做的事（如「来奶茶店买奶茶的顾客」），否则人物手里会凭空出现道具；道具留到视频提示词里再给。
   - 不写「全部视图清晰对焦」，它会与美学里的柔焦冲突，让画面变锐。
2. 外形以剧本为准，剧本没写的用贴合人物性格、职业与美学的设定补全；配饰要写清在角色自身哪一侧。容易出错又不影响剧情的小配饰宁可不加，写「无配饰」。每个角色都写身材与头身比（例：纤细修长，约七头半身比例，腿长；或敦实微胖，约六头半身），不写时三视图容易被画矮。
3. **表情基调写平常神情**：设定图里的表情会被 H3 当成默认表情。即使角色性格开朗，也写「自然放松的平常神情，不微笑」或「平静淡定」，表演全部交给视频提示词。
4. 角色之间用服装颜色做区分，并尽量呼应美学的冷暖关系（例：一人奶油白、一人墨绿）。
5. **用户回传设定图后检查**：
   - 版式：左侧特写是否约三分之一宽、占满整个高度、脸大而清楚（不能缩成小头像）；右侧三视图人物是否约九成画面高、等距、脚底对齐、头顶等高；有无接缝、独立底色块、墙地交界线、文字、边框或分格线。
   - 遮脸：是否只遮了正面全身的脸；正侧面侧脸是否被误遮（误遮时修图恢复，或重跑）。
   - 背景与光：背景是否为带一点藕粉的均匀浅灰，不偏黄、不偏紫，无场景；整体是否平光、低对比、柔焦；有没有逆光光晕、橙金色发丝高光或聚光暗角。
   - 脸：是否没有妆（无眼影、腮红、彩色唇），粉嫩通透感来自整体高调曝光、暖桃粉调色和柔光；皮肤是否白皙通透、细腻光洁；有没有变成冷白锐利的韩系脸或粗糙的素颜路人脸。出现妆容时，检查人物字段里有没有妆容或脸部颜色词。
   - 手：双手是否空着；手里多出道具时，检查 <身份> 是否写成了正在做的事。
   - 一致性：特写的脸与侧脸是否同一人；发型、服装颜色、配饰与系带位置是否一致，配饰左右是否一致。
   - 小问题不必重跑：以特写、正面全身和侧面为准，写成「人物锁定卡」（例：包挂在她自身左侧腰旁、围裙系带在腰前打结、电子表戴在左手腕），后续所有提示词照此写死。
   - 特写与侧脸明显不像同一人、背景变成场景、或人物成了剪影时，建议重跑。

---

## 第 4 步：场景与道具（Seedream · 剧本驱动型空间生成）

1. **先问用户：是否需要道具资产提示词？**（选项：需要道具特写 / 省略道具，只出场景）。
   - 选择省略：不出单独的道具特写提示词，但剧情必需的道具仍写进场景提示词里，保证场景图中存在。
2. **剧本空间解构（写场景提示词之前必做）**：根据第 2 步的动作节拍，判断每场戏的主要空间形态及连续性依据：
   - 点状对峙空间（谈判、就餐、隔物交谈）：以人物关系确定对话动作轴线，并按 180 度法则检查正反打。
   - 线状运动空间（走廊、并肩散步、街头追击、车内同行）：以行进方向建立运动矢量轴线，保持跨镜头的运动方向。
   - 场域开放空间（废墟、广场、旷野、天台）：先确定太阳角度、核心建筑等全片固定地标，再推导各机位的方向。
   - 封闭独角空间（单人密室、操作台独白）：根据人物与目标物的关系选择客观视点或主观视点（POV）。
   一场戏可以同时具有多种形态；按剧本实际动作切换，不把柜台、桌子或 A/B 正反打套到没有这些关系的场景。
3. **从核心戏剧动作推导场景视点矩阵**：先列出剧本是否有环境交代、纵深走位、面对面对话、眼神交锋、拥抱或接吻、并肩同行、递物、肢体冲突、道具搜寻、宏大奇观等，再选择必须生成的空镜底图；把视点编号、剧本依据及用途列给用户。通常按需选择 1–4 张；若剧情同时需要多类视点，以叙事需要为准。
   - **M-全景环境底图（Master）**：有大环境交代、天地奇观、走位纵深或首尾大拉远时，生成一张能读懂空间与地标的全景空镜。
   - **A/B-正反打交互底图（Reverse Angles）**：有面对面对峙、眼神交锋或对白攻防时，生成双方对应的视点图；按实际轴线推导视线方向。
   - **C-侧面双人底图（Profile Two-Shot）**：有拥抱、接吻、并肩、递物或肢体冲突时，生成能同时读清两人动作关系的侧面视点图；拥抱、接吻镜头须让双方五官及接触线可辨，不能让过肩前景遮住关键动作。
   - **D-运动路径底图（Motion Path）**：有线状走位时，沿行进方向生成纵深透视底图，明确起点、终点与运动方向。
   - **POV/道具视点**：剧本的主观观察或搜寻动作需要时补充，视点须与人物位置和视线目标对应。
4. **先定布局，再写各视点提示词**：用文字说明加俯视图（ASCII）或空间坐标系标出边界、固定地标、主光、人物起终点、进出路线与道具位置，向用户展示确认。只有剧情里确有障碍时才标分隔线。每个视点的画面左右、地标及主光方向必须从布局和摄影机朝向推导，不能把相反视点简单做成无条件镜像。先出一个基准视点，后续视点用已确认的场景图作参考，保持建筑、材质、颜色与陈设一致。每条提示词写清前中后景、可见地标及画面位置、主光方向与冷暖色对比，标注「空镜无人」，末尾加美学提示词（无参考视频或参考图片：固定美学提示词；有参考视频或参考图片：镜头版锚定词）与画幅词。
5. **道具特写**（用户需要时）：用场景图作参考生成同一物件的特写，外观、字体、文字内容必须与场景里那一件完全一致；末尾同样加美学提示词与画幅词。
6. **用户回传场景与道具图后检查**：
   - 画面文字是否写对（错字、乱码、数字）；
   - 文字是否与台词冲突（第 2 步清单）；
   - 剧情需要的道具是否都在、状态是否对（例：「空了的芋圆桶」必须是空桶）；
   - 各视点是否是同一地点；地标、主光、可走路线是否符合布局和各机位朝向。冲突时，以用户更满意且符合剧情的图为准修正布局，或用修图纠正另一张。
   - 有问题优先用图片编辑局部修改，模板：
     ```
     以参考图为底图，保持构图、光线、色调、所有物体和文字排版完全不变，只修改：<具体改动>。<美学提示词>，<画幅词>
     ```
7. 确定**上传编号**（全片固定不变）：① 角色甲设定图（换装版记为 ①-B、①-C……）② 角色乙设定图 …… 之后依次是按剧情选出的场景 M、A、B、C、D、POV 等视点图，最后是道具特写；未用的视点不占编号。

---

## 第 5 步：导演分镜与表演设计

本步必须遵守附录原文，尤其是：Scene and performance workflow、Professional emotion-performance planning、附录 A（声音标签、微表情控制短语、微表情修饰词、从意图到连续过程、多情绪转换、时间预算）、附录 B（听者、接话、行动动词、地位、调度、重音停顿、语速表、喜剧语法、跨段衔接、镜头配合、常见误演）。

### 5.1 角色表演基调卡（每个角色一张）
- 想要什么（目标）、阻力、潜台词；
- 高位还是低位，是否翻转、在哪句翻转；
- 语速、音色、句尾习惯；
- 惯用身体动作与「手上的活」（只用参考图或剧本里确有的道具）；
- 情绪曲线（由事件推动的弧线，标出每次转折的触发）；
- 冷面或克制型角色要设计「层次点」：全片唯一一次破功、唯一一次笑意等，并写清发生在哪句。

### 5.2 空间锁定卡（剧本定制版 · 全片唯一空间来源）

空间乱位的根源是每段提示词各自重新描述空间。本步结合剧本动作节拍、用户确认的场景图与第 4 步视点矩阵，写成一张「空间锁定卡」；图与布局不符时先核实剧情并修正布局。卡片锁定的是空间关系及其有因果的变化。之后每段视频提示词都原文复制它。卡片内容：

1. **左右用词规则**：画面方向一律写「画面左侧 / 画面右侧」，身体方向一律写「他/她自身左侧 / 自身右侧」，全片不出现不带主语的「左边」「右边」。
2. **空间坐标系与动作阶段**：根据实际空间形态选定对话动作轴线、运动矢量轴线或绝对地标系统，写清固定地标、可走区域、主光方向并附文字俯视图；逐一写出剧情触发的入画、移动、换位、转身与离开，标明起终点。只有实际存在的障碍才作为分隔线。
3. **人物站位与动态线**：每个动作阶段里各角色靠近哪个地标、面朝哪里、彼此距离、姿势、视线、行进轨迹与道具所在手或位置；阶段切换必须有剧本依据。独角戏同样记录人物与目标物的关系。
4. **机位矩阵表**：全片只用表中列出的机位，采用第 4 步实际生成的 M、A/B、C、D、POV 等视点编号；同一底图可派生单人、过肩、特写等机位，但须分别列出编号与构图。每个机位写清：
   - 摄影机相对人物、动作路径与地标的位置、高度、朝向；
   - 本机位使用哪张场景参考图（上传编号）；
   - 画面内每个人的位置与大致占比（例：老板在画面右侧三分之一，前景顾客虚化后脑占画面左侧约四分之一）；
   - 每个人的视线方向（看向画面左侧或右侧，偏高或偏低）；
   - 背景里可见的地标及其在画面哪一侧；
   - 主光从画面哪一侧来、轮廓光在人物哪一侧。
   - 插入镜头写清视点、物件与人物的相对位置；跟拍镜头写清摄影机与人物的相对关系及起终点。
5. **视线、动作与轴线规则**：根据实际人物关系或动作方向确定当前轴线，逐机位推导视线与画面左右。正反打中两人的视线须相向匹配；按附录 B9 的 A/B 编号约定，A 看画面左侧、B 看画面右侧，并在机位矩阵中固定各自拍摄对象。并肩行走时两人的行进方向保持一致。拥抱、接吻等关键亲密动作使用 C 侧面机位，让双方五官与接触线清晰可辨，避免过肩前景遮挡。剧情确需越轴或换边时，先写清过轴动作、过渡镜头或新建立的空间关系，再更新后续机位方向，不能无交代地跳变。
6. **进出与移动方向**：角色从哪里入画、经过哪些地标、离开去哪里，以及这些动作在各机位中的画面方向；递物和转身也须与布局及上一阶段状态一致。
7. **空间禁止项**（每段必带）：按本剧空间形态写出最关键的 3 条禁止项，例如无剧情依据地换位或瞬移、行进方向倒转、地标或主光换边、凭空增加人物或门窗。剧情明确要求且已在卡片中设计的移动与过轴不列为禁止项。

卡片同时写一份固定英文译文，英文版视频提示词原文复制这份译文。卡片与俯视图一起交给用户确认。

### 5.3 镜头系统
- 所有镜头都从空间锁定卡的机位矩阵表中选取；需要新机位时，先把它加进矩阵表（写齐上述全部项目），再使用。
- 先判断剧本里的动作和关系如何变化，再选镜头。静态双人对话需要交代双方反应时，可硬切正反打；独角戏、移动戏、多人调度或开放场域按动作路径和信息揭示选择机位，不强制正反打。需要听者反应时给可读的视点，避免全段只拍说话者。
- 按剧情选用镜头语言：过肩、单人近景、特写、手部或道具插入、主观镜头、焦点转移、轻微仰拍、推镜、前景遮挡；每种选择都对应具体信息或动作，不因示例而添物件。

**运镜决策规则（先定镜头语言，再判断要不要运镜）**

固定机位和硬切适合静态表演，H3 运镜可能带来人物变形、肢体漂移与画面闪烁；但剧本需要跟随移动或揭示空间时，应设计可控的运动。判断顺序：
1. 这段要传达什么情绪/信息 → 先定景别、角度、构图（镜头语言）；
2. 动态本身是否服务情绪或动作？静态对话、对峙、内心戏和微表情特写优先固定机位，靠景别切换表达；
3. 需要流动感（跟走位、空间揭示、视线引导、节奏加速）时才选运镜，一镜只做一种运动，幅度写小、速度写缓。

**运镜速查表＋H3 稳定性分级（选择时对照）**

| 运镜 | 情绪/用途 | H3 稳定性 | 提示词写法示例 |
| --- | --- | --- | --- |
| 慢推（缓慢推近） | 情绪顶点、金句、锁定视线 | 稳 | 「摄影机缓慢推近<人物>面部」 |
| 慢拉（缓慢拉远） | 揭示处境、收束情绪 | 较稳 | 「摄影机缓慢拉远，露出<环境>全貌」 |
| 慢横移 | 空间展示、扫过线索 | 较稳 | 「摄影机缓慢横移，依次扫过<物件>」 |
| 跟随走位（跟移） | 人物走动、追逐 | 慎用 | 「摄影机跟随<人物>朝画面<左/右>缓步移动」 |
| 轻微手持晃动 | 慌乱、失控、紧张 | 慎用 | 「轻微手持晃动，晃动幅度小且持续」 |
| 升降 | 俯仰揭示、高低位 | 慎用 | 尽量避开，用固定俯拍/仰拍替代 |
| 环绕 | 孤独、诡秘、浪漫 | 禁用 | 不写；改为「人物原地转身＋机位固定」 |
| 希区柯克变焦 | 惊悚、心理压迫 | 禁用 | 不写；用「固定机位＋缓慢推近」替代 |

**运镜写法规范（写入第 6 步提示词时）**
- 运镜写在「景别与机位」行与镜头描述里、`<d>` 之外；一句话一个运动，动词用「缓慢推近／缓慢拉远／缓慢横移／轻微晃动／跟随」，不写「运镜」「镜头运动」这类抽象词；
- 写清方向（朝画面左/右、朝人物面部）、幅度（轻微/缓慢）、起止（从……到……）；
- 固定机位镜头在禁止项里加「保持机位完全固定，不得自行推拉摇移」；运镜镜头写清运动方式并禁止附加第二种运动；
- 运镜镜头不同时叠加复杂微表情（特写运镜只承载一个变化，幅度更小）。

### 5.4 分段
- 每段不超过第 0 步确认的单段上限（默认 15 秒），按剧情节拍切，每段讲清一件事。
- 段尾可埋伏笔给下一段（例：眼神先瞟向某物，下一段才质问）；每段开头先演上一段留下的情绪，再进入新内容。
- **段间空间交接**：每段写「段首空间状态」与「段尾空间状态」，**只写人物与道具**：每个人的站位、朝向、姿势、手中道具、视线落点，以及道具的状态。**不得写机位编号**：「末镜【A-单人】」这类字样一旦进入下一段的段首状态，H3 会把它读成本段的开场镜头。下一段的段首空间状态必须逐字等于上一段的段尾空间状态；段内有走位时，终点必须符合卡片的进出方向。
- **跨段切点检验**：上一段末镜接下一段首镜，必须逐项通过：
  1. **换机位或景别**：按剧本空间选择正反打、动作方向上的新视点，或同方向至少两级景别变化；不把 A/B 正反打强加给独角戏和移动戏。
  2. **视线与动作匹配**：人物和道具的起终点、运动方向、速度与目光承接，符合当前动作阶段的空间锁定卡。
  3. **不无故越轴**：前后机位都在矩阵表里并遵守当前对话轴线、运动矢量或地标系统；剧情需要换轴时，先在上一段的动作或镜头里建立可读过渡。
  4. **不跳接**：不得同人、同机位、同景别直接相接；确需延续同一动作，也通过可读的机位或景别变化完成剪辑。
- 产出分段表：段号、时长、台词序号范围、核心节拍、镜头组织（写机位编号）、**首镜与末镜机位编号**、**跨段切点（上一段末镜 → 本段首镜及四项检验结果）**、段首/段尾空间状态、本段上传的参考图编号。
- **核对**：分段表覆盖台词表全部序号，无漏句、无改字、顺序不变；相邻两段的空间交接一致；每个跨段切点都通过上述四项检验。

### 5.5 逐句表演设计（声音标签、微表情控制短语、修饰词的配合）
对每句台词写清：说话人、行动动词、主重音（每句最多一个）、停顿类型（逻辑 0.2–0.4 秒 / 心理 0.5–1.5 秒及停顿中脸上做什么）、接话方式（正常接 / 快接 / 打断 / 迟接）、听者在哪个词上被击中、第一反应部位与延迟。

三类词库必须**按剧本、剧情、人物来配合使用**，不是随机添加，也不是每句都要用：
- **声音标签**（附录 A1）：只在剧本标注或剧情有依据时使用，并在设计说明里写出依据。参考选择方式（不是固定映射）：剧本写「惊讶」→ `<gasp>`；冷笑嘲讽、哭笑不得 → `<chuckle>`；妥协叹气 → `<sighs>`；狐疑压低 → `<softer>`；正色蓄力 → `<inhale>`；无奈抱怨 → `<groan>`；服气松一口气 → `<exhale>`。
- **微表情控制短语**（附录 A2）：每个关键反应选 1–2 个，按时间窗依次发生，一次只变一处；景别要看得见（特写只承载一个微小变化）。
- **微表情修饰词**（附录 A3）：用于控制触发与幅度，例如 `on hearing the word "<台词里真实存在的词>"`（听到某词才触发）、`while the rest of the face remains relaxed`（冷面角色只动一处）、`only on his/her own right/left side`（写清角色自身左右）、`then returns to a neutral expression`（破功后收回）、`just before speaking`、`for a split second`。
- 做时间预算：按附录 B6 语速表核算每个时间窗，开口前留约 0.3 秒、说完留约 0.5 秒。
- **声音情绪必须显式写出（第 6 步落到台词时间窗与 overall_soundscape）**：附录 A1 没有怒、委屈、冷漠等情绪标签，这类音色按附录 A4「表里没有的音色可以用自然语言描述」写成可执行的声音描述（例：「压着怒意」「尾音发颤」「低哑无情绪」「闷声撒娇带黏」），并标注语速（附录 B6，如约2.5字/秒、约5字/秒抢话）。不要用标签替代语义：`<softer>` 是音量不是情绪，`<chuckle>` 是轻笑不是冷笑。

### 5.6 声音导演设计（音乐与静音的介入规则）

每个片段在设计表演的同时定声音层，结论落到第 6 步的 overall_soundscape 与 non_diegetic_music：

1. **环境声先于画面**：能用声音建立氛围的镜头，优先写环境声（空间感、质感、远近），并写清「先声入画」或「先静后声」，不让画面先落地再补声音。
2. **音乐介入三问**：这段有没有无法靠台词/表情单独传达的情绪顶点？有 → 考虑起乐；没有 → 保持默认无配乐。静音是工具：噩耗、真相揭晓等情绪冲击处，优先写「环境声骤停，静默片刻」而非加乐。
3. **默认无配乐不豁免**：non_diegetic_music 仍必须写一句明确状态（「无配乐」或具体音乐描述：何时起、何时停、情绪质地），禁止空着。
4. **声画关系**：钩子镜头可用「先声入画」（下一段的声音先于画面约 0.5 秒进入），写在段首过渡说明里；只在剧情需要时使用，不每段都用。

### 5.7 输出与等待
输出：角色表演基调卡、空间锁定卡（含俯视图与英文译文）、机位矩阵表与镜头系统说明、分段表（含首镜与末镜、跨段切点检验结果、段首/段尾空间状态）、逐句设计要点（含所选声音标签及依据）、每段上传清单。请用户确认，或提出修改后再进入第 6 步。

### 5.8 段落表演意图推导（第 6 步写提示词前必做的内部推理）

四件套解决「情绪写什么」，本步解决「**怎么从剧本段落判断该写什么**」。写每一段提示词之前，先读本段剧本正文（台词、表演标注、事件、道具状态），按下面五步做内部推导；推导结果映射成第 6 步的四件套。推导只在内部完成，不输出推理过程；用户追问选择理由时，按「输入依据 → 表演目的 → 表达 → 触发时机」说明。

**第 1 步：读段落事件。** 用一句话说清本段演了什么、人物关系推进到哪一步（例：段1「叶晚摔包放狠话，江屿心虚不敢上前」）。信号来源：剧本的动作描述、事件、道具状态变化。

**第 2 步：定目标与阻力（演什么）。** 每个人物此刻要对对方做什么（按附录 B2 行动动词），阻力是什么，潜台词是什么。例：叶晚的目标=划清界限（警告），阻力=她其实在等他解释；江屿的目标=安抚示弱，阻力=她不肯接话。情绪是目标受阻的副产品，先定动词再定情绪，不从台词字面套表情。

**第 3 步：定情绪定性 + 质感 + 强度（0–10）。** 每个情绪**先定质感（温度/方向/克制态），再定强度**——同样是「生气 7」，冷怒、热怒、忍泪的怒是三场完全不同的戏，面部与声音写法不同。质感速查：
- 怒：**冷怒**（压着，声音平而低、眼神冷、动作少）／**热怒**（要爆，声音抬高、语速快、动作大）／**忍泪的怒**（声音发颤、眼眶湿、咬字硬）／**赌气的怒**（孩子气，扭头、嘴硬、小动作）；
- 悲：**麻木的悲**（低变化、目光空）／**强忍的悲**（抿唇、喉部滚动、呼吸顿）／**崩溃的悲**（破音、肩头塌、眼泪落下）；
- 喜：**轻笑**（嘴角微扬）／**忍不住的笑**（笑出声、眉眼弯）／**含泪的笑**（破涕，先湿眼再笑）；
- 怕：**强作镇定**（语速快、小动作多）／**僵住的怕**（呼吸停、身体定住）。
按下面的强度判断基准表定分，再按人物性格与弧线位置修正：
- 嘴硬心软 / 克制型角色在破功前压 1–2 档强度（外冷内热：冷面之下情绪浓度更高，露出来的只是一角）；
- 本段是全片情绪顶点（爆发、崩溃、强忍到极限、撕破脸）时 +1；
- 收尾 / 和好段 −1；
- 同一人物多句台词允许强度爬升，不许无依据跳变；升级段每段比上一段高，形成压迫递进。

**强度判断基准表（剧本信号 → 参考强度）**

| 段落剧本信号 | 强度 |
| --- | --- |
| 平静陈述、无冲突、普通问答 | 0–3 |
| 试探、解释、轻微情绪词（委屈 / 心虚 / 烦躁 / 敷衍） | 4–5 |
| 明确冲突词（冷笑 / 咬牙 / 发颤 / 愤怒 / 恳求 / 威胁 / 忍泪） | 6–7 |
| 情绪顶点（爆发 / 崩溃 / 强忍到极限 / 撕破脸 / 失而复得） | 8–10 |

**第 4 步：选表演手段（怎么呈现）。** 按附录 A1/A2/A3 与 B1/B6 选，每项都要说得清「输入依据 → 表演目的 → 表达 → 触发时机」：
- 声音：A1 标签（音量 / 重音 / 停顿 / 呼吸 / 笑声）+ **自然语言音色**（怒、委屈、冷漠等 A1 没有的必须用自然语言描述，如「压着怒意」「尾音发颤」「低哑无情绪」）+ B6 语速；
- 微表情：A2 短语 1–2 个，选本镜景别读得到的；
- 听者反应：B1，绑定台词里真实存在的词；
- 行动动词：B2。

**第 5 步：定触发与禁止项。** 每个情绪 / 表情 / 语气变化必须绑定触发（台词里的真实词、对方的动作、已建立的事件、人物自己意识到失态的瞬间），无触发的变化不写；按 B10 挑本段最可能出现的 2–4 条误演写进禁止项。

**推导 → 四件套映射（第 6 步落位）**

| 推导结果 | 落到第 6 步的哪一处 |
| --- | --- |
| 第 3 步的情绪定性 + 强度 + 表演关键词 | subject_definitions 的「情绪基调」 |
| 第 1–3 步的情绪走向（起点 → 变化 → 落点） | summary 的「情绪弧线」 |
| 第 4 步的音色 / 语速 / 句尾处理 | 台词时间窗的声音描述 + overall_soundscape 的「声音表演」 |
| 第 5 步的触发词 / 听者反应 / 禁止项 | detailed_description 时间窗 + 本段禁止项 |

**示例（《推两下没推动》段1：江边吵架对峙）**：事件=叶晚摔包放狠话、江屿心虚不敢上前；目标=叶晚划清界限（警告）／江屿安抚（示弱），阻力=她其实在等他解释、他不善言辞；情绪=叶晚生气 7 + 委屈 6（嘴硬压档后仍是高点，因为已等三小时）、江屿心虚 5；手段=叶晚声音压低压怒、语速约 2.5 字/秒、下颌绷紧、视线钉江面不看人，江屿喉结滚动；触发=「碰」字即警告、江屿被「碰」刺中后喉结滚动；禁止=面无表情念稿、眼神空洞对不上对象、持续微笑。

### 5.9 表演幅度分级与 H3 校准（实测防"没情绪"）

**幅度分级表（按景别选，别写景别看不见的）**

| 幅度 | 什么景别读得到 | 示例 |
| --- | --- | --- |
| 微幅 | 特写 / 大特写 | 下眼睑收紧、喉部细微移动、单侧嘴角微扬、睫毛轻颤 |
| 中幅 | 中近景 / 中景 | 皱眉、抿唇、视线移开、攥手、下巴微抬、偏头 |
| 大幅 | 全景 / 远景 | 扭头、摔包、起身、转身走、捂脸、扑进怀里 |

**校准规则（H3 实测：细微表情生成精度有限，克制写得越细越容易生成成"面无表情"）**
- 中近景为主的对白段，微幅与中幅混用，不要全用微幅；
- 生成结果情绪平淡时，按顺序升级直到画面可读：
  ① 情绪质感从「隐」改「显」（冷怒→热怒、强忍的悲→崩溃的悲）；
  ② 微幅短语升级为中幅（「下眼睑收紧」→「皱眉＋抿唇」）；
  ③ 加身体动作（面部之外先动身体，H3 对身体比面部稳）；
  ④ 声音加自然语言情绪与语速（「压着怒意」→「声音抬高、语速变快」）；
- 特写镜头只承载 1 个变化；全景靠动作与姿态表达，脸上的细节不写。

### 5.10 身体表演速查（面部之外的第二通道）

面部微表情之外，身体是第二表演通道，且 **H3 对身体动作的生成比面部稳定**——情绪平淡或画面需要更大可读度时，优先写身体。按输入依据选用，不堆叠；一个时间窗最多一个身体动作 + 一个面部变化。

- **肩背**：双肩垮下来（放弃／疲惫）、肩膀绷紧（防御／对峙）、肩头随呼吸起伏（情绪上涌）、肩膀微颤（强忍／哭前兆）；
- **手**：手指蜷进衣角或袖口（紧张、依赖）、攥拳又松开（强忍）、手悬空僵住（被击中、情绪顶点）、指尖反复按亮手机（焦虑等待）、手缓缓垂落（防线瓦解）；
- **腿脚**：站定不动（对峙）、后退半步（退让）、挪开一截（赌气）、重心在两脚间切换（不安）、起身朝画面左侧走（决绝）；
- **颈**：喉结滚动（吞咽紧张）、脖颈僵硬不随视线转动（拒绝／回避）、微微低头（示弱／害羞）、仰头看对方（挑衅／恳求）。

规则：身体动作与面部／声音由同一触发同步发生；动作方向（朝画面左／右、朝对方）写清；景别看不到的身体动作不写（胸部以上近景不承诺手部细节）。

### 5.11 无对白情绪段编排（纯表演段必用）

一段内没有台词（或台词极少）时，情绪靠四通道撑起来：**呼吸、视线、肢体、环境声**。编排：

1. **结构**：起始状态 → 触发（对方动作／环境事件／已知信息）→ 变化（身体先动、面部跟上）→ 余波定格；不要写成 10 秒静止。
2. **节奏**：每 2–3 秒一个可读变化；全景给动作与姿态，中景给视线＋身体，特写给呼吸＋微表情。
3. **环境声承担情绪**：吻戏环境声骤降只剩风声；路灯点亮一声「咔」作情绪物理分界；噩耗处环境声骤停静默——把声音当表演写进 overall_soundscape。
4. **禁止**：无对白不等于画面静止；也不等于加无依据的肢体乱动——每个动作都有触发。

**示例（强吻段，10s 无对白）**：对视（呼吸加重、喉结滚动）→ 捧脸俯身（手部动作）→ 吻下（叶晚身体僵住半秒→闭眼）→ 右手推两下没推动、手悬空僵住（情绪顶点）→ 手缓缓垂落（防线瓦解）。

---

## 第 6 步：MiniMax H3 视频提示词（中英双版）

每一段输出两个版本，各自是一个独立、完整、可直接粘贴的 `text` 代码块，严格按附录原文的六个标题与格式：

1. **中文版**：说明文字用中文；微表情写成「中文描述（附录 A2/A3 英文原文短语）」，例：`轻微眯眼（narrows the eyes slightly）`，并在全局视觉锁定里注明「括号内英文为微表情控制短语，与中文同义，用于精确控制部位与幅度」。
2. **English 版**：六个标题保持原样；景别机位、表演、声音、环境等说明文字全部译成英文；微表情直接使用附录 A2/A3 的英文原文短语；**台词保持中文原文不翻译**，仍写成 `<Subject N> (SN): <d>[Chinese] 原文</d>`，声音标签与 `<i>`、`<pause>` 位置与中文版完全一致；读法说明（如「28 reads as 二十八」）写在 overall_soundscape；全局视觉锁定末尾的美学提示词保留中文原文不翻译；空间锁定卡使用第 5 步定稿的固定英文译文。

每段提示词都要包含：
- 全部参考图的 Subject 定义（人物写入锁定卡内容、声音、性格，并注明参考图为三视图设定图、脸部只以左侧面部特写为准（正面全身视图的脸已遮盖）；换装角色写明本段用的是哪一套服装的设定图；场景写清对应哪个机位、机位方向、地标左右与光线，与空间锁定卡一致）；
- summary 里写明本段的段首空间状态与段尾空间状态（与分段表逐字一致，不含机位编号），紧接段首状态写明本段首镜编号、拍摄对象及其与上一段的衔接方式，段尾状态后写明末镜编号；`[Shot 1]` 的「景别与机位」明确开场第一帧就是计划中的机位与画面内容，不自行补建立镜头。是否有他人入画、前景过肩或全景，由分镜设计决定；上一段末镜编号只写在分段表里，不写进本段提示词；
- 全局视觉锁定：画幅、实际采用的切镜或连续拍摄方式、身份与环境来源绑定、**调色与场景锁定**（把本段每个机位与对应场景 Subject 逐一绑定，锁定已确认的色彩、雾感、柔光、颗粒、建筑与陈设，不重新设计场景；同一场景的各段使用同一份锁定文字，不预设 A/B 或固定段数）、**空间锁定卡全文（每段完全相同的同一份文字）**、切镜不跳色，末尾接美学提示词（无参考视频或参考图片：固定美学提示词；有参考视频或参考图片：镜头版锚定词）与画幅词；
- 每个 `[Shot N]` 的「景别与机位」一行以机位编号开头（例：`景别与机位：【A-过肩】中近景……`），并把该机位在卡片里的人物画面位置、视线方向、本镜环境来源（`本镜环境只来自<Subject N>`）原样写入，不得与卡片矛盾；然后是时间窗、表演、行动动词、听者反应、台词行。人物走位或转身要写清朝向画面哪一侧、朝哪个地标；
- 本段的禁止项：2–4 条最可能出现的 AI 误演，加上空间锁定卡里的空间禁止项；
- overall_soundscape（环境声、动作声、声音质感、混音优先级、数字读法、需要后期添加的音效）与 non_diegetic_music（默认「无配乐」）。
- **情绪可执行四件套（防"生成出来没有情绪"的平片，实测必需，缺失即不合规；内容按 5.8 的表演意图推导产出，不是凭空选词）**：
  - **subject_definitions 的「此刻状态」写情绪基调**：定性词 + 强度（0–10 分）+ 一句表演关键词（例：「此刻状态：坐在长椅右端，别过脸面朝江面，双手攥衣摆。情绪基调：生气（强度7）、委屈（强度6），嘴硬心软——表面冰冷警告，内在一直在等他解释；声音压低压怒、放狠话、倔强。」）；英文版写 `Emotion: angry (7/10) and hurt (6/10) — …`。情绪词不能只靠「生气委屈」这类一句带过，要被空间锁定与调色文字淹没时仍可被模型读取。
  - **summary 在段尾状态后写一句情绪弧线**：本段谁从什么情绪经什么变化到什么（例：「情绪弧线：叶晚压怒放狠话，江屿心虚露怯，对峙张力形成。」）；英文版写 `Emotion arc: …`。
  - **每个台词时间窗（`<d>` 行前的动作描述行）用自然语言写声音情绪与语速**（例：「声音压低、压着怒意，语速放慢（约2.5字/秒），每字清晰带警告」）。附录 A1 只有音量/重音/停顿/呼吸/笑声标签，没有怒、委屈、冷漠等情绪标签；这类音色必须按附录 A4 用自然语言描述，不能只用 `<softer>` 这类音量标签顶替（`<softer>` 只表达"声音小"，不表达"压着怒意"）。
  - **overall_soundscape 写一行「声音表演」**：本段每句台词的音色、语速、句尾处理（例：「声音表演：叶晚压低、压怒、咬字重、尾音发紧，江屿喉结滚动声轻微可闻」）；英文版写 `voice acting: …`。环境声与声音表演分行写，不混在一起。

**每段的交付结构：先给人看的「导演节奏速览」，再给 H3 代码块（强制）**

每段在代码块之外先附一份「导演节奏速览」，让人不看代码也能一眼掌握这段的节奏；它是给人看的导演看板，**绝不写进 `text` 代码块、绝不复制进 H3**——H3 只读六段式纯文本，额外的表格、符号、HTML 会被当成画面内容、降低成功率。复制进 H3 时只复制代码块。

每段交付顺序：
1. **导演节奏速览**（中文，放在代码块上方），固定含：
   - 标题行：段号、时长、画幅、镜头数、覆盖台词序号；
   - 节拍行：一句话标出「钩子 → 冲突 → 升级 → 反转/落点」及各自的时间点；
   - 一条纯文本时间轴：按真实时长比例排开各镜，每镜写镜号、机位、台词要点；运镜镜头与声音标记（环境声先入、慢推/慢拉、静音、起乐）单独标出；
   - 一张紧凑表：镜号｜机位｜景别｜时长｜运镜｜台词/动作要点｜声音/表情标记；
   - 一行运镜核对：本段运镜数量、分别在哪镜、其余镜头固定（对照 5.3 的护栏与稳定性分级）。
   ```
   【导演节奏速览 · 第X段】给人看，不进 H3；复制进 H3 时只复制下面的 text 代码块
   时长 <实际秒数> · <画幅> · <镜头数>镜 · 台词<序号范围>
   节拍：<按本段剧情写触发、阻力、变化与落点，并标时间点>
   时间轴：<按各镜真实时长成比例排开 S1、S2……，标出运镜与声音落点>
   运镜：<逐镜列出运动及稳定性；其余写固定>
   声音：<环境声、静音、配乐的实际起止点>
   | 镜 | 机位 | 景别 | 时长 | 运镜 | 台词/动作要点 | 声音/表情 |
   |---|---|---|---|---|---|---|
   | S1 | <机位矩阵编号> | <景别> | <秒数> | <固定或运动> | <要点> | <标记> |
   ```
   （仅示意字段；实际按本段镜头逐行填满，时间轴须按真实时长绘制。）
2. 紧接其后输出中文版（与 English 版）`text` 代码块，六段式与格式不变；用户明确只要中文版时只出中文版。
3. 对话里需要彩色看板时，可另出一张 HTML 分镜节奏卡（色块按真实时长成比例，标注运镜与声音标记），但同样不进 H3；HTML 完整设计文档里每段都带这张卡（见结尾第 7 条）。

**交付前核对（必须由我完成，不能留给用户）：**
- 把所有段落里的台词逐句与第 2 步台词表比对：无漏句、无改字、顺序与说话人一致，中英两版台词完全相同；
- 每段时长不超过上限，时间窗从 00:00.000 连续到总时长、无空隙，每个窗口按语速表说得完；
- **空间核对**：
  - 所有段的全局视觉锁定里，空间锁定卡文字完全相同（中文版之间相同，英文版之间相同）；
  - 每个镜头都有机位编号，且在机位矩阵表中；镜头里写的人物画面位置、视线、地标左右、主光方向、环境来源与卡片一致；
  - 不存在不带主语的「左边 / 右边」；
  - 上一段的段尾空间状态与下一段的段首空间状态逐字一致，且都不含机位编号；走位、转身、递物方向符合进出方向；
  - 每个跨段切点（上一段末镜 → 下一段首镜）都通过第 5.4 步的四项检验；每段 summary 与 `[Shot 1]` 写明的首镜编号和 `[Shot 1]` 实际的机位编号一致；
- 人物锁定卡（配饰左右、服装）、道具状态跨段一致；
- 每段全局视觉锁定都含调色与场景锁定句，末尾都有美学提示词与画幅词；全部提示词里没有妆容词（眼影、腮红、红晕、唇色、妆容）。
- **每段都有情绪可执行四件套**（subject_definitions 情绪基调+强度、summary 情绪弧线句、台词时间窗声音情绪+语速、overall_soundscape 声音表演行），中英两版一一对应，无缺失。

---

### Ref2VA 六段式格式硬规则（2026-10-26 实测校准）

以下规则对齐 MiniMax H3 官方 Ref2VA 格式，实测验证后写入，不得违反：

**1. 空间锁定卡每段只写本段内容，禁止剧透后续段落**
- 每段的全局视觉锁定里，空间关系只写**本段生效**的内容：人物站位、面朝方向、主光、关键地标、本段禁止项。
- 后面段落才会发生的动作（掏手机、逼近、强吻、拥抱、道具状态变化等），到对应段落的空间锁定卡里再写，**不得提前写入本段**。
- 目的：避免 H3 提前演后面的剧情，导致节奏崩盘；同时压缩提示词长度，防止重点被稀释。

**2. Shot 1 不带时间戳范围**
- `[Shot 1]` 直接开始镜头描述，默认从 0 秒开始。
- 禁止写 `[Shot 1] 00:00.000–00:05.000` 这种时间范围。
- 官方规则原文：`[Shot 1] never gets a timestamp — it starts at zero by definition.`

**3. Shot 2 及以后用 At 时间戳 + cuts to 格式**
- 后续镜头开头必须写成：`[Shot 2] At 00:05.000, the camera cuts to...`
- 禁止写 `[Shot 2] 00:05.000–00:15.000` 这种时间范围格式。
- 官方规则原文：`Every later shot opens with a strictly increasing cut time: [Shot 2] At 00:03.500, the camera cuts to...`

**4. 台词行标准格式**
- 正确写法：`苏柚 (S1) says: <d>[Chinese] 台词内容</d>`
- 禁止写 `<Subject 1> (S1): <d>[Chinese] ...</d>`——去掉 `<Subject N>` 前缀，直接用角色名 + (S1) + says:
- 语气/声音描述写在 `<d>` 外面，和 says 连在一起。

**5. subject_definitions 只写身份外貌，不写情绪**
- subject_definitions 里每个 Subject 只写：身份、年龄、发型、五官、服装、参考图来源。
- 情绪、表演、状态写在 detailed_description 对应时间窗里（格式：`角色名此刻情绪：XX（强度N/10），表演关键词`）。
- 目的：身份定义和表演指令分离，避免角色漂移。

**6. 美学提示词用新版（2026-10-26 v2）**
- 已移除：高调过曝描述、薄雾空气感、bokeh光斑、美颜滤镜感、人物肤质句。
- 新版提示词见第 1 步 B 固定美学·场景/视频版。


交付时写明：总生成时长、预计成片时长、每段上传的参考图编号；建议先试跑一两段最能检验表演与空间衔接的片段（说明要看什么），效果对了再批量生成。

### 6.1 成片尾帧检验（逐段生成时执行）

提示词写的段尾状态，不等于生成出来的结尾画面。用户回传某一段的成片后，先检验它的结尾，再让用户生成下一段：
1. 抽帧：用 ffprobe 取时长，抽最后一帧和倒数约 0.5 秒的一帧（`ffmpeg -v error -sseof -0.05 -i <视频> -frames:v 1 tail.png`，`ffmpeg -v error -sseof -0.5 -i <视频> -frames:v 1 tail_05.png`），用 Read 查看；用户只回传截图时直接看截图。
2. 对照本段的段尾空间状态与空间锁定卡逐项检查：最后一个镜头的机位与景别；每个人在画面哪一侧、朝向、视线落点；手的位置与手中道具；道具状态（例：杯子是否已封口、桶是否仍为空桶）；背景地标与主光是否换边。
3. 一致：告诉用户可以直接生成下一段。
4. 不一致：
   - 只是姿势或道具的小偏差（手位、视线、道具位置），而且不影响剧情：按尾帧实际画面改写「本段段尾空间状态」与「下一段段首空间状态」（两处仍保持逐字一致），只重出下一段的中英两版提示词，并说明改了什么；
   - 最后一个镜头的机位或景别与计划不同：重新检验跨段切点，不通过时调整下一段的首镜，再重出下一段提示词；
   - 人物无剧情依据地换边或越轴、背景地标与主光方向错误、道具状态与剧情矛盾（例：芋圆桶里出现了芋圆）：建议重跑本段，不往下接；剧本要求且已在空间锁定卡中设计的移动或过轴按计划核对。
   - 调色或场景与参考图明显不符（例：没有粉调与雾感、场景被重画）：与已通过的段落并排对比，以用户认可的那段为准，建议重跑本段。
5. 修改过的段落同步更新提示词文件与 HTML 设计文档（如已制作）。

---

## 结尾：询问是否需要 HTML 设计文档

视频提示词交付后，问用户：**是否需要一份 HTML 版的完整设计文档？** 用户同意后，制作**单个 .html 文件**并用 SendUserFile 发给用户（只给文件，不发布成网页）。

HTML 内容（专业剧本格式呈现）：
1. 封面：片名、类型、成片时长、画幅、图片模型与视频模型、日期。
2. 故事梗概与角色表（角色、年龄、身份、性格、表演基调）。
3. 美学风格：拆解表与实际使用的美学提示词（固定美学或提取的锚定词）。
4. 资产提示词：人物三视图设定图（含换装版）、按剧情选出的场景视点图、道具特写、修图提示词、人物锁定卡、上传编号表。
5. 空间锁定卡：俯视图（可用内联 SVG 或等宽文字图）、动作阶段与路线、机位矩阵表、视线和轴线规则、进出方向、各段段首/段尾空间状态。
6. 完整剧本：采用专业剧本格式——场景标题（如「内景 奶茶店柜台 - 日」）、动作描述行、角色名居中大写样式、括号内表演提示、台词居中缩进；台词与台词表完全一致。
7. 导演分镜与表演设计：镜头系统、分段表、每段镜头列表（机位编号、景别、运镜、时长）、**每段一张分镜节奏时间轴卡（色块按真实时长成比例，标出运镜镜头、环境声先入/静音/起乐等声音标记，以及钩子/升级/反转节拍）**、逐句表演设计（行动动词、重音、接话、听者反应、声音标签及依据、微表情）。
8. 视频提示词：每段中文版与 English 版，等宽字体代码框，每框带「复制」按钮（navigator.clipboard，失败时退回选中文本）。

制作要求：样式与脚本全部内联在一个文件里，不依赖外部脚本；页面 `<title>` 用片名；颜色定义为 CSS 变量并支持浅色与深色（prefers-color-scheme）；手机宽度可读、无横向滚动；带打印样式（每段提示词不被分页截断）；左侧或顶部目录可跳转各章节。做完自己打开检查一遍再发送。

---

# 附录：tudou-single-h3 原文（不得修改）

以下为 tudou-single-h3 skill 全文，第 5、6 步必须照此执行。

# Tudou Single H3 · 单片段提示词

Turn the user's scene request and any supplied references into one ready-to-paste MiniMax H3 prompt for a single video clip. With reference images, use the reference-based workflow below; with text only, define subjects from the user's description without inventing uploaded references. Do not ask the user to pre-classify references; infer each image's role and preserve the intended identity, wardrobe, location, and visual style.

## Scope and defaults

- Deliver one clip prompt per request, not a full-film production package or multiple alternative clips unless requested. This skill writes prompts; it does not upload assets or spend generation credits.
- A single clip may contain cuts when the user requests them. Otherwise prefer one continuous shot with a clear action progression; do not impose a three-shot structure.
- Follow the requested genre, visual style, performance, and audio. Do not default to Japanese settings, winter, romance, prayer, photorealism, or music-video treatment.
- If timing is unspecified, use a six-second creative planning default and identify it as the assumed duration in `summary`, not as a claimed H3 platform limit. Do not invent supported resolutions, durations, or API parameters. Leave aspect ratio unspecified unless supplied or reasonably inferable.
- Ask only when essential missing input prevents a faithful result. If an explicitly required image is unavailable, request it rather than inventing its contents.

## Output contract

Output only one complete prompt using these six headings in this exact order:

```text
subject_definitions:
summary:
retention_analysis:
detailed_description:
overall_soundscape:
non_diegetic_music:
```

Use `<Subject 1>`, `<Subject 2>`, and onward consistently. Write the prompt in the user's requested language; for a Chinese-language request without a stated preference, write Chinese. Keep dialogue and visible text in the user's original language. Do not add a preface, explanation, prompt fragments, or a second alternative unless requested.

### Format hard rules (apply in every environment and every agent)

- Return the prompt inside **one** fenced code block (```text). Nothing else inside the block; outside the block write nothing, unless the user asked for explanation.
- The block starts with `subject_definitions:` and contains exactly the six headings above, each on its own line, in that order, spelled exactly, lower-case, followed by a colon. Never translate, rename, number, bold, or wrap them in Markdown (`#`, `**`, tables, bullet lists of headings).
- Under `detailed_description:`, write the global visual lock first, then shot blocks labeled `[Shot 1] 00:00.000–00:06.000` with sub-beats `00:00.000–00:01.200：…`. Times are continuous, start at `00:00.000`, end exactly at the total duration, and use three decimals.
- Each dialogue line appears once, on its own line, as `<Subject N> (SN): <d>[Language] …</d>`.
- If a section has nothing to add, write a short explicit statement (for example `non_diegetic_music: 无配乐。`), never leave it empty or delete it.

Skeleton (structure only; replace every part with the actual content):

```text
subject_definitions:
<Subject 1> (S1)：……
<Subject 2>：……
summary:
……
retention_analysis:
<Subject 1>：fully_preserved —— ……
detailed_description:
全局视觉锁定：……
[Shot 1] 00:00.000–00:06.000
景别与机位：……
00:00.000–00:01.200：……
<Subject 1> (S1): <d>[Chinese] ……</d>
00:01.200–00:06.000：……
overall_soundscape:
……
non_diegetic_music:
……
```

Use a compact production-prompt structure: subject definitions first, then a one-paragraph summary stating duration, format, story beat, and reference-role separation; then a per-subject retention analysis; then a global visual lock followed by timed `[Shot 1]`, `[Shot 2]`, and onward blocks.

## Reference-role inference

Classify every supplied image before writing:

- A character portrait, turnaround sheet, or outfit sheet becomes a fully preserved character subject.
- An environment, building, or location image becomes a fully preserved scene subject.
- A cinematic screenshot becomes an attribute-transfer-only style subject when separate images already establish the target characters or setting, or when the screenshot primarily communicates lighting, grading, lens quality, or atmosphere rather than a reusable subject.
- A composition, staging, pose, or action screenshot becomes an **extraction-only analysis source** when separate images already establish the target characters and setting. Inspect it, extract its camera angle, framing, spatial proportions, left/right placement, depth layers, and action geometry, then **exclude it from the final H3 reference-image upload set**.
- A supplied first-frame image becomes the visual starting state. Preserve its immediately visible people, positions, framing, wardrobe, and environment unless the requested action requires a later change.

Honor any roles named by the user over automatic inference. If a role is ambiguous, make the least disruptive assumption and state it in `retention_analysis`; do not pause for clarification. When character cards and scene assets coexist with a cinematic frame, favor treating that frame as a pure visual-style reference so it cannot overwrite the supplied identities, wardrobe, setting, or blocking.

## Composition-reference extraction rule

When the user provides a separate image only to communicate composition, person placement, pose, interaction, camera height, or action rhythm, do not let that image compete with the target identity references. A visually strong composition screenshot can otherwise cause H3 to copy its faces, wardrobe, and setting even when the prompt says otherwise.

1. Classify it internally as `extraction_only`; do not create a `<Subject N>` for it and do not mention it as a H3 reference image in the final prompt.
2. Translate its useful visual information into direct text constraints: camera angle and height; shot size and crop; frame percentages; screen-left/screen-right placement; foreground, middle-ground, and background layers; scale relationships; gaze lines; pose; hand placement; and action timing.
3. Explicitly bind identity, wardrobe, and environment only to the uploaded character and scene references. For example: `must use <Subject 2>'s male identity and <Subject 3>'s female identity`; never rely on a composition image to supply either person.
4. Exclude every recognizable element from the composition source: faces, hair, wardrobe, accessories, scene, architecture, lighting, grading, captions, and visible text. Preserve only the abstract spatial/action rule in words.
5. Exception: if the same image is the user's only source for a character, location, or required first frame, it is not extraction-only; classify it using the ordinary character, environment, or first-frame rules instead.

For a reference set containing scene + target character cards + a composition screenshot, the final H3 upload set normally contains only the scene and character cards. The composition screenshot stays outside H3; its extracted constraints appear only in `detailed_description`.

Number uploaded references in their final upload order after excluding extraction-only sources, and use that mapping consistently. For text-only prompts, `<Subject N>` identifies a described subject, not an uploaded image; state that no reference images were supplied in `retention_analysis`.

For each subject, write an exact, visible description. Include identity-defining facial and hair traits, complete wardrobe, accessories, and left/right placement for characters. Include key architecture, terrain, vegetation, weather, and foreground elements for scenes.

## Style-reference control

When an image is a style-only reference, define it exactly as an attribute transfer, never as source content:

```text
<Subject N> is reference image N used solely as a visual-style reference. Transfer only its artistic direction, cinematography, lens character, color palette, saturation, color-temperature relationship, exposure, contrast, lighting logic, material rendering, depth of field, bokeh texture, grain, highlight roll-off, shadow density, atmospheric perspective, and overall mood. Do not transfer any recognizable people, faces, hairstyle, wardrobe, objects, architecture, text, composition, camera angle, pose, or action from <Subject N>.
```

In `retention_analysis`, label that subject `attribute_transfer`; label characters and locations `fully_preserved`.

In `detailed_description`, begin with a direct separation between content and style. State that the style reference controls **how the video is photographed and graded**, while character, wardrobe, scene, blocking, and action come only from the fully preserved subjects. Then use this adaptable continuity lock. Keep weather or particles only when the requested scene needs them:

```text
All shots must continuously retain <Subject N>'s overall color system, color-temperature relationship, luminance distribution, contrast, key-light direction, light softness, environmental bounce logic, material detail, focal-length feel, depth-of-field relationship, bokeh behavior, grain scale, highlight roll-off, shadow density, atmospheric perspective, and artistic mood. Cuts must not cause a jump in grading, lighting ratio, skin tone, sharpness, grain, bokeh, or lens texture. Preserve only scene-appropriate weather and particles; when they are absent, maintain depth through natural foreground layers, atmosphere, spatial perspective, and out-of-focus highlights.
```

A visual-style reference is optional. If none is supplied, follow the user's written style instructions and derive restrained continuity constraints from available content references. If neither provides a style, use neutral visual language without inventing a genre-specific direction. Apply style-reference separation only when such a reference exists.

## Scene and performance workflow

1. Convert the user's story into a timed, shot-by-shot sequence. Respect all stated durations, hard cuts, camera distance, screen positions, and audio constraints. Use `00:00.000` timing and `[Shot N]` labels. State the total duration and aspect ratio when either is specified or inferable.
2. Use unambiguous framing language. Describe both shot size and crop, for example: `two-person medium-close shot, framed from mid-thigh upward`. For a two-person close shot, specify which face is sharp and which figure is recognizably soft.
3. Preserve continuity across cuts: character identity, outfit, accessories, time of day, location, props, weather direction, and screen-left/screen-right placement remain stable unless the user requests a change.
4. Describe micro-expression acting as a sequence of isolated, small changes, each with its own time window. Specify eye state, gaze destination, eyelid tension, breathing pause when useful, head movement, mouth-corner movement, and the emotional result. Let pupils move before the head, and let softened eyelids precede the smile when the action calls for restrained affection.
5. Restrict a delicate emotional beat to one clear change at a time. Choose the actual movement from the user's scene and intended performance, not a default smile or eye-opening routine. Limit exaggerated movement only when it conflicts with the requested acting; preserve explicitly requested broad smiles, abrupt turns, or heightened performance.
6. For a resolved emotional beat, end with a stable, readable pose for the final 0.8–1.0 seconds when timing permits. Respect requested ongoing motion or other endings.

## Professional emotion-performance planning

When a request involves emotional acting, treat emotion words as outcomes to be earned, not as a list of expressions to display. Before drafting the timeline, internally define this compact performance brief:

1. **Given circumstance and trigger:** What has just happened, who is the character responding to, and what specific visible, audible, or already-established fact begins each change? Do not invent a trigger when the user has supplied none; use the least disruptive continuity-based trigger or keep the performance internally motivated and restrained.
2. **Objective, obstacle, and subtext:** What does the character want from the other person in this moment, what prevents it, and what are they unable or unwilling to say outright? Let dialogue, silence, and gaze serve that intention rather than label emotions.
3. **Emotional quality and intensity:** Distinguish the quality of an emotion (for example, indignant hurt versus betrayed anger; frightened compliance versus startled fear) and its intensity level. Do not treat every "sad," "angry," or "afraid" request as the same facial shape.
4. **Emotional arc and carryover:** Plan a causal path with readable stages—such as contained anger → hurt exposure → loss of control—rather than abrupt swaps. A later state retains appropriate residue from the prior one: anger may remain in breath and diction after tears begin; fear may remain in gaze and vocal hesitation after a plea.
5. **External score:** Select only the visible and audible evidence that the supplied framing can show: face (eyes, brows, mouth, jaw), voice (pace, volume, texture, pauses), and body only if the user permits it and the framing supports it. Coordinate all selected channels with the same event and avoid decorative gestures.
6. **Character and situation calibration:** Match amplitude to the stated personality, relationship, privacy of the setting, and stakes. A request for heightened performance permits larger, still-causal expression; a request for restraint favors pressure, interruption, and incomplete release rather than stock gestures.
7. **Playable endpoint:** State what remains at the end—recovered resolve, suspended fear, unresolved sobbing, relieved warmth, etc. Do not reset to neutral or a smile by default.

For actor-test prompts, make the acting challenge observable without turning the output into a grading rubric: provide a clear trigger, a legible inner shift, coordinated facial/voice evidence, and an end state. When the user asks for evaluation criteria, map the result to psychological causality, emotional quality, transition continuity, technical coordination, control of intensity, and felt realism.

## Actor performance: voice, expression, and timing

When a clip involves dialogue, vocal performance, or facial acting, read 下文「附录 A：演员演绎速查表」. Select only the entries that serve the requested performance; do not paste the whole glossary into the prompt.

### 根据用户输入选择，不随机搭配

速查表是可选表达词库，不是随机抽取池，也不是每次必须覆盖的清单。先理解用户内容，再选择能实现这段表演的词条；不为了丰富画面、增加变化或展示标签而添加动作。

1. **提取依据**：识别用户明确指定的演法、禁用项、原始台词、人物关系与意图、正在发生的事件、情绪起点与变化、景别和时长。未提供的信息不编造成确定事实。
2. **按优先级判断**：用户明确演法与限制优先，其次是剧情事件和人物意图，再其次是台词语义与上下文。不能仅凭一个词或问号推断哭腔、愤怒、恐惧或嘲讽；如用户要求“笑着说狠话”，应保留笑与狠话的反差。
3. **先定表演节拍**：明确谁在什么刺激下产生什么变化，以及何时说话、停顿或保持沉默。没有情绪变化的平静陈述可以维持自然表情，不必制造转折。
4. **分别选择声音和可见动作**：对每个候选标签或微表情，内部确认“输入依据 → 表演目的 → 具体表达 → 触发时机”。声音、面部动作可表达不同层次的情绪，但这种反差必须有用户要求或情境依据。没有依据的候选项删除；不需要声音标签时可以只保留普通对白。
5. **检查可执行性**：只保留当前景别可读、时长可容纳且互不冲突的动作；根据克制或外放的演法调整幅度。不能为了加入某个词条而改写用户台词、人物意图或镜头计划。
6. **依据不足时收敛**：选择中性、自然、最少附加动作的表达，不随机补哭、笑、喘、结巴、耳语或吞咽。只有缺失信息会改变核心剧情或表演含义且无法保守处理时才询问。

以上判断在内部完成，默认仍只交付六段完整提示词；用户询问选择理由时，再说明输入依据与选用项的对应关系。同一输入的表达可以变化，但表演意图、强度和触发依据应保持一致。

### 将表演意图组织成连续过程

- 先确定人物此刻想做什么、为什么迟疑或改变，再安排可见动作。同一句台词可表达害羞、崩溃、麻木或克制，不能由台词字面直接套用演法。具体方法见附录 A「从表演意图到连续过程」。
- 按需要形成“起始状态 → 刺激或准备 → 变化或中断 → 说话／行动 → 余波”的因果链；这不是固定五阶段模板，平静陈述不必制造爆发，短片段也不必填满所有阶段。
- 分别控制情绪强度、动作幅度、语速、音量、音色和对白清晰度。低声不自动等于含混，平淡不等于嘴唇不动；按实际发音呈现自然口型，不为清晰度强制夸张张嘴。
- 附属运动跟随真实原因：转头带动头发，低头带动饰物，呼吸带动肩胸。只使用用户描述或参考图确有的元素，不随机补风、飘带、流苏或配饰；强烈动作也要符合用户要求的画面边界。
- 结尾承接该次表演留下的状态或运动，不默认微笑、恢复中性或冻结画面。若未明确要求冻结帧，“停留在某种神态”可保留自然呼吸、眨眼或尚未结束的惯性运动，但不能违背声音与动作限制。
- 输出前统一台词版本并检查发声时间与声音范围。明确的台词修正或“只说某句”优先于示例中混入的台词；无法判断的核心冲突才询问。对白时长不够时先减少可选动作、调整未锁定的时间分配，不擅自删改台词、加速慢速演法或延长指定总时长。

### 多情绪转换与对白递进

当用户要求多个情绪变化时，先为整个片段写一句可检验的情绪弧线：人物因同一事件或关系变化，从什么状态经过哪些转折，最终留下什么状态。情绪数量服从时长和剧情，不为了“多”而排列无关表情。详见附录 A「多情绪转换与对白递进」。

- 每次转换都必须有可见或可听的触发：对方的动作、沉默、已知信息、人物意识到自己的失态，或用户指定的事件。不得用未说明的画外声音、突然出现的物件或无原因的情绪跳变推动转折。
- 将台词当作情绪弧线的一部分：每句台词应推进人物目标、关系或压力，并与说话前后的表情相衔接。不要把多句台词写成同一语气、同一表情下的平铺陈述。
- 先安排目光、表情或身体准备，再让台词落下；说完后为对方的沉默、人物的意识或动作后果留出反应时间。若一句话本身是情绪顶点，允许其先说出口，再在余波中显露反应。
- 按台词含义和用户要求分别设定每句的语速、音量、重音和停顿；相邻句须保留声音连续性。强度可以上升、降低或反转，但不能无依据地从耳语跳到嘶吼，或从崩溃瞬间变成愉快。
- 无入画的对话对象可以作为角色的稳定注视方向，但只能以用户明确或已建立的剧情意图描述其状态。不得为方便推进情绪，擅自给对方补台词、脚步、关门声或其他可听行动。

以下仅演示选择逻辑，不是情绪到标签的固定映射：

| 用户输入 | 可选择的演绎 | 不应自行附加 |
| --- | --- | --- |
| “压低声音，怕门外的人听到” | 根据压低程度选择 `<softer>` 或 `<whisper>`；有观察门口的剧情时才加入侧瞥 | 无依据的哭腔、喘气、惊恐表情 |
| “想哭但忍住，平静地说完” | 用眼睛湿润但不落泪等少量可见变化体现克制，声音保持用户要求的平静 | 自动使用 `[Chinese, crying]`、抽泣或下唇持续颤抖 |
| “跑到门口，喘着气说话” | 按台词间隙放置 `<pant>` 或 `<catches breath>`，给恢复呼吸留时间 | 将喘气直接解释为害怕，或在同一瞬间安排持续说话与吸气 |
| 只有“你真的要走吗？” | 保留询问语义，使用自然语气；等待上下文决定更具体演法 | 仅因“走”或问号就指定悲伤、哭腔或挽留动作 |

- Bind each speaking character once in `subject_definitions`, using `<Subject N> (SN)` with the same subject number throughout. Do not assign speaker identities to environment or style references. Maintain the character's voice across cuts.
- In timed `detailed_description` blocks, place language and delivery cues plus dialogue and vocal tags inside `<d>...</d>`. Keep the speaker label, facial movements, body acting, and camera instructions outside it. Preserve the user's actual dialogue and language; translate descriptive prose only as requested. Tags retain their exact spelling.
- Convert each emotional beat into a visible sequence: trigger → localized facial change → spoken or silent reaction → release or hold. Specify amplitude, duration, gaze target, and the relation to speech when useful. Word-triggered reactions must follow an actual word in the supplied dialogue; do not change dialogue merely to fit an example.
- Coordinate speech, breathing, and visible movement on one timeline. Allow enough time for the line, pauses, and reactions. Avoid simultaneous contradictory actions such as closed lips during speech, an inhale during a sustained utterance, or a smile held while its disappearance is requested. Sequential beat windows may contain naturally synchronized audio and visual actions.
- Use a small number of readable changes per beat. Match detail to framing: subtle eyelid or throat changes belong in a readable close view, while distant shots need larger visible gestures. Do not insert a close-up or cut against the user's shot plan merely to show a micro-expression.
- Silence does not require a dialogue block. Do not add speech, humming, audible breathing, or other vocalizations when the user requests a silent performance; visible breathing can be described outside `<d>`.
- These tags are user-provided writing conventions, not a verified universal H3 parser or API contract. Use them as the skill's default notation; if the target environment is known not to support them, express the same performance in plain language. Do not add compatibility disclaimers to every generated prompt.
- Include `Facial Realism` only when the user or actual workflow confirms that `MiniMax-H3-Facial-Realism-CloseUp` LoRA is loaded. Never assume it is loaded, load it automatically, or treat the phrase as a universal quality booster.

## Scene acting: listening, cues, actions, status, blocking, timing

For any clip with dialogue between characters, a confrontation, a negotiation, a comic beat, or any request about acting quality (“文戏”, “演技”, “台词”, “表演”), also read 下文「附录 B：文戏表演编排」. It complements the actor-performance glossary: the glossary controls *how one speaker sounds and moves*; scene-acting controls *who listens, how lines are picked up, what each line does to the other person, who holds status, how distance and props carry subtext, where stress and pauses go, and whether the lines fit the time*.

Apply it with the same selection discipline (input basis → purpose → visible/audible evidence → timing). In particular:

- **Listener track.** For every line in a multi-character clip, also write the listener: the exact word that lands, the first reacting channel, its delay (normally 0.2–0.4 s; a freeze of 0.3–0.6 s before reacting when stung), and any suppressed attempt to interrupt. Do not invent lines or sounds for an off-screen listener.
- **Cue pickup.** Choose normal pickup, overlap, interruption (written as a broken line ending in “——”), or a delayed reply with a visible silence, according to relationship and stakes. Never let characters alternate at an even, recital-like pace without reason.
- **Action verbs.** Give each line an internal action toward the other person (逼问, 搪塞, 试探, 讨好, 刺痛, 稳住 …). A turn in the scene is a change of tactic after the previous one fails, preceded by a visible moment of realization. Keep these verbs internal unless the user wants them shown; express them through gaze, timing, stress, and delivery.
- **Status.** Decide who holds the higher position and whether it flips; place the flip on a specific line or action. Do not equate loudness with status.
- **Blocking and props.** When the user permits body acting and the framing can show it, use distance, orientation, eye level, and existing props as subtext. Never add props or movement the input does not support.
- **Stress and pauses.** One main stress per line (`<i>…</i>`), chosen by what the speaker most needs the other person to hear. Distinguish logical pauses (0.2–0.4 s) from psychological pauses (0.5–1.5 s) and write what the face does during a psychological pause.
- **Time budget.** Check each window with the speech-rate table in 附录 B (≈4 字/秒 normal; 5–6 heated; 2.5–3 restrained). If the lines do not fit, cut optional business first; never ship a timeline that cannot be spoken.
- **Genre register.** Calibrate to the genre grammar (everyday realism, epic/period, comedy timing with setup → beat → punchline and delayed reactions, dialect only on request).
- **Failure-mode bans.** Add the 2–4 most likely AI mis-performances for this beat to the description's restrictions (e.g., constant smiling, recital-like alternation, dead eyes while speaking, lip-sync drift).

## Single-clip action and audio planning

Build one readable beat: starting state → main action or interaction → visible result. Allocate non-overlapping time windows that cover the full duration without gaps. For a continuous take, use one `[Shot 1]` block with timed sub-beats. Add further shot blocks only when cuts are requested or necessary to the user's stated shot plan.

Use micro-expression details for delicate emotional acting; use clear anticipation, contact, weight transfer, and follow-through for physical actions. Do not force restrained smiles or small movements onto energetic action. Keep the final hold only when it fits the requested ending; ongoing motion can remain ongoing when requested.

In `overall_soundscape`, describe ambience, action sounds, voice quality, and mixing priorities, referring to the speaker and dialogue timing already written in `detailed_description`. Write each full dialogue line once in its timed shot block to avoid duplicate delivery or conflicting directions. In `non_diegetic_music`, follow the requested music treatment; default to no added score when unspecified. Do not invent dialogue, lyrics, captions, or extra people. These six headings are this skill's writing format, not a claim about H3 API fields.

## Quality pass before output

Check that:

- all attached references have a defined role;
- every extraction-only composition/action source is omitted from the final H3 reference-image upload set, omitted from `subject_definitions`, and represented only by text constraints in `detailed_description`;
- uploaded scene and character references, not extraction-only sources, are the sole basis for generated identity, wardrobe, and environment;
- each subject keeps the same label in every section;
- the timeline covers exactly the user's duration or the clearly stated planning default;
- every cut has a clear pre-cut and post-cut framing;
- when a style-only reference exists, it controls visual treatment, never source content;
- every delicate micro-expression is broken into chronologically ordered, isolated beats;
- for emotional acting, each change has a causal trigger or an explicitly established inner realization; the emotional quality, intensity, visible/aural evidence, and carryover from the previous beat agree;
- the performance uses only the expression channels the user permits, fits the framing and character situation, and ends in the requested residual state rather than a default reset;
- style-only references contribute attributes only, never content;
- visual continuity is locked across all shots;
- the prompt forbids the likely generation failures for the requested beat;
- sound and music do not contradict the user's requirements;
- speaker bindings remain consistent, and each dialogue line appears once with enough time for its delivery and pauses;
- `<d>` blocks contain only dialogue, language/delivery cues, and vocal tags; facial actions and camera directions stay outside;
- expression triggers, lip movements, breathing, and spoken words agree on the timeline, including silent-performance requirements;
- `Facial Realism` appears only when the corresponding LoRA is confirmed loaded.
- every selected vocal tag and facial action has an identifiable basis in the user's instructions or scene context; unsupported embellishments and automatic emotion-to-tag mappings are removed.
- emotional changes, accessory motion, and ending states follow the scene's causal sequence rather than a stock performance template;
- dialogue wording, delivery speed, available speaking time, and permitted sound sources agree; unresolved hard constraints are not concealed by an impossible timeline.
- for multi-emotion performance, every change has a stated trigger and causal link; dialogue, reaction windows, and the final state form one continuous emotional arc.
- in multi-character clips, every line has a listener reaction and a chosen cue-pickup type; interruptions appear as broken lines in the dialogue itself;
- each line has one main stress at most; psychological pauses state what the face does; every window passes the speech-rate check;
- status, blocking, and props (if used) are supported by the input and readable in the framing; the genre register matches the request;
- the 2–4 most likely AI mis-performances for this beat are explicitly excluded;
- the output is one `text` code block containing exactly the six headings in order, with no Markdown inside and nothing outside unless requested.

---

# 附录 A：演员演绎速查表（声音与微表情）

本表来自用户提供的演绎约定，用于组织单个片段的表演提示词，不代表已经验证的 H3 通用接口语法。按剧情、景别和时间选择所需条目，不堆叠整张表。中文提示词可将英文微表情短语转写成同义中文；声音标签保留原样。

## A1. 语气与声音标签

| 标签 | 作用 |
| --- | --- |
| `<pause>` | 短暂停顿 |
| `<long pause>` | 长停顿，留出沉默 |
| `<i>词语</i>` | 重读包裹的词语 |
| `<whisper>台词</whisper>` | 耳语说出包裹的台词 |
| `<softer>` | 降低后续台词音量 |
| `<humming>音节</humming>` | 哼唱包裹的音节 |
| `<breath>` | 插入呼吸声 |
| `<inhale>` | 吸气 |
| `<exhale>` | 呼气 |
| `<deep breath>` | 深呼吸，准备开口或平复情绪 |
| `<catches breath>` | 停下来缓一口气 |
| `<pant>` / `<pants>` | 急促喘气 |
| `<laughs>` | 笑出声 |
| `<chuckle>` | 短促轻笑 |
| `<sighs>` | 叹气 |
| `<gasp>` | 突然倒吸气 |
| `<mhm>` | 表示认同的“嗯哼”声 |
| `<phew>` | 松一口气的“呼”声 |
| `<groan>` | 低沉呻吟或抱怨声 |
| `<uh>` | 犹豫时的“呃”声 |
| `<hmm>` | 思考或迟疑的“嗯”声 |
| `<stutter>` | 结巴、重复或断续发音 |
| `<coughs>` | 咳嗽 |
| `<clears throat>` | 清嗓子 |
| `<sniff>` | 吸鼻子 |
| `<smacks lips></smacks lips>` | 咂嘴 |
| `[English]` / `[Chinese]` | 指定英语／中文对白 |
| `[English, crying]` / `[Chinese, crying]` | 指定语言，并带哭腔说话 |
| `[English, singing]` / `[Chinese, singing]` | 指定语言，并演唱台词 |
| `[Hum]` | 哼唱旋律 |
| `<d>台词</d>` | 包住对白及声音标签；面部动作与运镜写在外部 |
| `<Subject 1> (S1)` | 绑定人物与说话人身份 |

保留表中标签形态：成对标签闭合，`<pause>` 等独立标签不补造闭合标签。语言和演唱标记表达声音要求，不代表需要画面字幕。停顿与呼吸占用片段时长，不能将长台词、长停顿和细密动作同时挤进短时间窗。

## A2. 微表情控制短语

| 部位 | 控制短语 | 作用 |
| --- | --- | --- |
| 眉毛 | `raises one eyebrow slightly` | 轻挑一侧眉毛 |
| 眉毛 | `briefly raises both eyebrows` | 短暂抬起双眉 |
| 眉毛 | `draws the eyebrows slightly together` | 双眉轻微向眉心靠拢 |
| 眉毛 | `slightly raises the inner corners of the eyebrows` | 轻微抬起眉头 |
| 眉毛 | `the brow tension gradually releases` | 逐渐放松眉间紧张 |
| 眼睛 | `narrows the eyes slightly` | 轻微眯眼 |
| 眼睛 | `the eyes widen briefly, then settle` | 短暂睁大眼睛，再恢复 |
| 眼睛 | `blinks once, slowly` | 缓慢眨眼一次 |
| 眼睛 | `the lower eyelids tighten slightly` | 下眼睑轻微收紧 |
| 眼睛 | `the eyes become moist without tears falling` | 眼睛湿润，眼泪不落下 |
| 视线 | `glances sideways without turning the head` | 头部不动，眼神侧瞥 |
| 视线 | `briefly lowers the gaze, then restores eye contact` | 短暂垂眸，再恢复目光接触 |
| 视线 | `the gaze flicks toward the door, then returns` | 目光迅速扫向门口，再移回来 |
| 视线 | `holds steady eye contact` | 保持稳定的目光接触 |
| 嘴角 | `one corner of the mouth lifts slightly` | 单侧嘴角轻微上扬 |
| 嘴角 | `a faint, closed-mouth smile appears` | 浮现轻微的闭嘴微笑 |
| 嘴角 | `the smile gradually fades` | 笑容逐渐消失 |
| 嘴角 | `suppresses a smile by pressing the lips together` | 抿嘴压住笑意 |
| 嘴角 | `the corners of the mouth turn down slightly` | 两侧嘴角轻微下垂 |
| 嘴唇 | `presses the lips together briefly` | 短暂抿紧嘴唇 |
| 嘴唇 | `the lips part slightly before speaking` | 开口前嘴唇轻微张开 |
| 嘴唇 | `the lower lip trembles faintly` | 下嘴唇轻微颤动 |
| 下颌 | `the jaw tightens subtly` | 下颌轻微绷紧 |
| 下颌 | `the jaw slowly relaxes` | 下颌缓慢放松 |
| 脸颊 | `the cheeks lift slightly as the eyes gently narrow` | 脸颊轻抬，同时眼睛轻眯 |
| 鼻部 | `the nostrils flare slightly` | 鼻翼轻微张开 |
| 鼻部 | `briefly wrinkles the nose` | 短暂皱鼻 |
| 喉部 | `swallows softly, with a small movement in the throat` | 轻轻吞咽，喉部细微移动 |

## A3. 微表情修饰词

| 修饰词 | 作用 |
| --- | --- |
| `slightly / subtly` | 缩小动作幅度 |
| `briefly / for a split second` | 缩短动作持续时间 |
| `gradually / slowly` | 放慢表情变化 |
| `only on the left side` | 将动作限制在左侧；需要时说明是角色自身左侧还是画面左侧 |
| `just before speaking` | 将动作安排在开口前 |
| `on hearing the word "leave"` | 听到指定词语时触发表情；按实际台词替换触发词 |
| `then returns to a neutral expression` | 动作后恢复中性表情 |
| `while the rest of the face remains relaxed` | 保持其他面部区域放松 |
| `Facial Realism` | 仅配合已确认加载的 `MiniMax-H3-Facial-Realism-CloseUp` LoRA 使用的触发词 |

## A4. 从表演意图到连续过程

从用户提供的表演示例中提炼以下规则。学习的是选择与编排方法，不继承示例中的古风服饰、人物性别、暖金色光、固定机位、五秒时长、竖屏比例或具体台词，也不将几类情绪当作必选菜单。

### 用行为呈现情绪及其变化

先识别人物目标与阻力，再决定是否需要变化，以及变化如何被观众看见。例如，想靠近却害羞可能表现为对视后回避，又试探着看回；想说却克制可能表现为准备开口后中断，再决定是否说出。这些只是因果关系的说明，不能仅看到“害羞”就强加偷看，也不能只看到“克制”就强加吞咽。

选择少量能够表达意图的视线、眉眼、口唇、头颈或呼吸变化。每个动作写清起点、触发、幅度和去向；已经持续的状态不必每秒重新发生。爆发可以有积蓄和余波，麻木可以保持低变化，欲言又止可以出现动作中断；均以输入依据为准。细微表演不等于所有表演必须细小，用户要求激烈爆发时允许更大的动作。

### 声音、口型与身体按同一事件配合

- 先确定原始台词与演法，再选择音量、音色、语速、停顿和重音。特殊声音标签只是表达手段，表里没有的音色可以用自然语言描述，不创造看似标准的新标签。
- 低声、清晰、迟疑可以同时成立；大声、嘶哑和破音也可分别控制。不要将“大声”默认写成清亮喊叫，也不要把“平淡”写成没有发音口型。
- 吸气准备、说话、停顿吞咽、说后呼气或喘息按生理顺序安排。只有用户要求或场景支持时才添加相关动作与声音；喉部可见动作不自动意味着需要放大吞咽音效。
- 发音期间口型与实际词句一致，抿紧嘴唇、闭嘴微笑等不与持续发音冲突。需要字词触发时，将反应绑定到真实台词中的具体位置；不对每个字机械分配一个表情。
- 表情“空洞、失焦”优先写成目光缺少明确注视目标、回神迟缓等可读行为，不把特定瞳孔变化视为必然。皮肤变化、泪水、颈部紧张只在输入支持且画面可读时使用，不堆叠全部生理细节。

### 景别、运动与余波

判断当前构图实际能看到什么。胸部以上的取景不能承诺看清身侧双手的指节；面部近景也不应同时承诺全身动作细节。必要时改用画内可读的肩颈或面部表达；用户同时硬性要求冲突的构图和关键动作时再澄清。

头发、服装和饰物只响应已有身体运动或明确环境条件。不要用无原因的持续飘动填充静止画面；区分“无风声”与“无风”，后者不能安排由风导致的飘动。先核实参考图或文字确有相应物件，再写其运动。

收尾延续刚发生的行为：可以继续回避、等待、松弛、喘息或维持空洞状态，但只选符合本段内容的结果。角色停住时，已有的饰物惯性可以逐渐消退；不要要求其无因突然静止。没有明确冻结帧要求时，不把情绪停留写成整幅画面停止运动。

## A5. 多情绪转换与对白递进

当一个片段需要多个情绪时，先把它理解为一条由事件推动的弧线，而非“依次做几种表情”。写出人物的初始目标、让目标受影响的触发，以及最后留下的心理状态。用户若给出明确情绪顺序，保留该顺序；若只要求“多个情感转换”，从人物关系、事件和台词中推导一个最少且连贯的弧线，缺少足够依据时使用保守变化，而不是自行制造极端转折。

可以采用如下的编排结构，但不要机械填满：

1. **建立状态**：让观众先读懂人物此刻的关注点、期待、戒备或回避。
2. **触发转折**：用已知事件、对方沉默、角色观察到的动作，或角色意识到自己的反应来促使变化。
3. **台词或行动推进**：每句台词承担一个明确作用，例如确认、试探、追问、阻止、掩饰或坦白。台词不是情绪说明书；必须搭配可见的说话前后反应。
4. **余波与下一次选择**：一段话说完后，人物可以等待、追随、收回、平复或重新决定。下一句台词应由这份余波引出。
5. **结局状态**：结尾保留这次过程的结果，例如仍在等待、勉强镇定、终于坦白或决定离开；不可默认恢复笑容或中性表情。

这些步骤可压缩、合并或省略。一个短促的“别走”可以本身就是触发与行动；长片段则可以留出更多停顿和反应。不要让每句话都配一个新表情，也不要在台词刚结束的同一帧立即跳到下一种情绪。

为每句对白明确四件事：**为什么现在说、说给谁、语气怎样、说完发生什么**。声音变化应遵循弧线：例如期待时可轻快，疑惑时放慢或降低音量，阻止时提高力度，掩饰时变轻，坦白时恢复稳定。此为可能的因果逻辑，不是固定的情绪映射；用户指定的表演与反差优先。

未入画的对象只能通过人物已有的视线、反应和用户给定的信息存在。可以写“她看见对方似乎要离开”这样的已知剧情，但不能让不可见对象突然说话或制造声音来替代触发。若声音范围禁止外界声音，使用无声的视觉线索或片段开始前已发生的信息；若用户同时要求可闻外界刺激和绝对静音，需要澄清。

## A6. 输入冲突与时间预算

1. **台词唯一**：正文与声音控制中的台词必须一致。若用户明确“只说 X”，按 X 清理其他位置，不能将两个版本拼起来。没有明确优先依据且影响原意时，提出一个聚焦的问题。
2. **时间可行**：为实际词句、要求的语速、停顿和呼吸保留时间。不要把“慢慢说完”塞进明显不足的窗口。先压缩可选表情和铺垫、重分配未锁定时间；若台词、语速与总时长均为硬约束且无法兼容，说明冲突并询问调整哪项，不交付假装可行的时间轴。
3. **声音范围明确**：分别判断对白、其他人物发声、环境声、外界音效与配乐是否允许。“无背景音乐”不等于静音，“只有人物声音”也不代表所有呼吸、抽泣都必须加入。“没有额外音效”与明确要求的人物吞咽声可以并存，不把已获准的人物声音一起删掉。
4. **刺激与可闻性一致**：在禁止外界声音的片段里，不突然加入敲门声、鸟鸣或画外台词。仅当输入支持时，可写为片段开始前的刺激或已有视觉刺激；用户又明确要求片段内听到该声时，应澄清冲突，而非暗中换掉关键事件。
5. **约束针对误演**：根据本段意图排除最可能的偏差，例如不把克制演成撒娇、不把麻木演成愤怒。不要复制覆盖所有情绪的负面清单，不禁止用户明确需要的激烈动作。

## A7. 编排示例：对白与面部动作分开书写

下面仅示范 `detailed_description` 内的局部写法，不替代技能要求的六段完整输出。假设用户已提供台词“你真的要走吗？”并要求克制、轻声的表演，`<Subject 1> (S1)` 已在人物定义中绑定。

```text
[Shot 1] 00:00.000–00:06.000
固定近景，清楚呈现 <Subject 1> 的面部；目光落在画面右侧的对话对象身上。
00:00.000–00:01.200：眉头轻微向眉心靠拢，其他面部区域保持放松；不说话。
00:01.200–00:04.600：开口前嘴唇轻微张开，保持对对方的注视。
<Subject 1> (S1): <d>[Chinese] <softer>你<pause>真的要走吗？</d>
00:04.600–00:06.000：说完后嘴唇自然合拢，眉间紧张缓慢释放，继续等待对方回应。
```

`overall_soundscape` 只补充环境声、声音质感和混音关系，不再次复制该句台词。没有用户对白时，不借用示例台词。

---

# 附录 B：文戏表演编排（听、接、动作动词、地位、调度与节奏）

本附录补充附录 A《演员演绎速查表》。速查表解决“一个人说话时声音和脸怎么控制”；本附录解决文戏里更难的部分：**谁在听、怎么接、每句话在做什么、两人谁压着谁、身体和距离怎么说话、重音停顿放在哪、时间够不够**。

使用原则与速查表一致：这是**按输入选择的方法**，不是每次都要塞满的清单。每一项都要能说出“输入依据 → 表演目的 → 可见/可听的表达 → 触发时机”；说不出依据的就不写。

## B1. 听比说重要：听者表演与接话节奏

文戏一半在听的人身上。两人以上的片段，对每句台词同时安排**说话人**和**听者**。

**听者必须写清：**
- 在哪个具体词上被击中（绑定台词里真实存在的词，例如“听到‘败将’时”）；
- 被击中后的第一反应发生在哪个部位（目光、下颌、呼吸、手），幅度多大；
- 反应比台词晚多少：正常 0.2–0.4 秒；被刺痛或震惊时先“定住”0.3–0.6 秒再反应；早有预料的人可以几乎不反应（不反应本身就是表演）。
- 是否想插话：嘴唇轻启又合上、吸气后没开口、身体前倾半寸又收回。

**接话节奏（cue pickup）四种，按关系和情绪选择：**

| 接法 | 时间关系 | 适用 |
| --- | --- | --- |
| 正常接 | 上句落地后 0.3–0.6 秒开口 | 平稳交流、一般对话 |
| 快接／抢话 | 上句最后一两个字还没说完就开口（重叠 0.1–0.3 秒） | 争吵、急切、压制对方、熟人斗嘴 |
| 打断 | 上句说到一半被截断，被打断者的台词要写成残句“你根本不——” | 一方失去耐心、地位压制、阻止对方说出口 |
| 迟接 | 上句落地后沉默 1–2 秒才开口，沉默中写听者的反应 | 被刺中、在权衡、拒绝配合、情绪顶点后的余波 |

规则：
- 没有理由不要让两人匀速轮流念台词；这是 AI 文戏最典型的“念稿感”。
- 打断和抢话必须在台词文本里体现（残句、破折号），不能只在描述里写“打断”。
- 画外的对话对象没有用户给的台词时，不替他补台词；他的存在只能通过画内人物的视线和反应体现。

## B2. 演动作，不演情绪：行动动词与换策略

专业演员演的是**动词**（对对方做什么），情绪是动词遇到阻力后的副产品。为每句台词标一个行动动词，写成“对谁 + 做什么”。

**常用行动动词（按需选择）：**
- 进攻类：逼问、揭穿、羞辱、威胁、施压、挑衅、刺痛、激将
- 防守类：搪塞、回避、否认、拖延、稳住、装傻、掩饰
- 拉近类：试探、讨好、安抚、示弱、求、哄、引诱
- 推开类：拒绝、打发、冷落、警告、划清界限
- 揭示类：坦白、认输、承认、交底

**换策略规则：**
- 一个动词没起作用（对方不接、反击、沉默），人物才换下一个动词。转折点写成“这招没用 → 换一招”，而不是“从愤怒变成委屈”。
- 换策略之前给一个可见的“意识到”瞬间（目光停顿、呼吸断一下、手的动作停住），再进入新动词。
- 同一句台词，换一个动词就是另一种演法。例：“你走吧。”
  - 打发：语速平、不看对方、话说完立刻转回手上的事；
  - 试探：说完抬眼观察对方反应、尾音略轻；
  - 求（反话）：声音发紧、说完没有移开目光，等对方留下。
- 用户已经指定演法时，以用户为准；动词只用来让指定演法有因果。

## B3. 地位（高低位）与权力流动

两人场景先判断**谁在上位、是否会翻转**。同一句“坐下”，上位者说和下位者说是两场戏。

**高位的可见表现（按需挑 1–2 个）：** 视线稳定、不急于移开；先开口或决定何时结束对话；语速偏慢、停顿不急着填；身体占据空间、动作少而完整；可以不回答问题。

**低位的可见表现：** 先移开视线或频繁确认对方反应；语速偏快、话尾上扬或自我修正；身体收拢、小动作多（摸物件、调整衣角）；抢着解释。

规则：
- 地位关系由剧情和人物关系决定，不由音量决定；大声的人可以是低位（虚张声势），平静的人可以是高位。
- 一段戏的张力常来自**地位翻转**：写清翻转发生在哪一句、哪个动作上（例如低位者第一次不移开视线）。
- 不需要翻转时，保持地位一致，不要每句都摇摆。

## B4. 调度就是关系：距离、朝向与道具

在用户允许身体表演且景别能看到时，用调度表达关系变化：

- **距离**：走近一步 = 施压或靠近；退半步 = 防御或退让；有人后退而另一人跟进 = 追逼。距离变化要对应台词或关系变化，不做无意义走位。
- **朝向**：正对 = 直面；侧身 = 半回避；背对 = 拒绝或隐藏表情（背对时把表演转移到声音和后颈、肩膀）。
- **视线高度**：一人站一人坐、一人俯视一人仰视，天然带出地位。
- **道具戏**：手里的物件（杯子、刀、文件、武器）是潜台词的出口——握紧、放下、推开、递过去又收回。只使用用户描述或参考图里确有的道具，不凭空添加。
- 画幅限制：胸部以上的近景看不到走位和手里的道具；需要调度表达时，景别必须能容纳，否则改用肩颈、呼吸、视线表达，不擅自改用户的景别。

## B5. 重音与停顿：怎么选，不只是怎么写

**重音选择**——同一句话，重音位置决定意思。先问“这句话真正要对方听见的是哪个词”：
- 例“我没说他偷了钱”：重读“我”（是别人说的）；重读“没”（否认）；重读“偷”（不是偷，是借）；重读“钱”（偷的不是钱）。
- 一句话通常只有**一个主重音**，最多再加一个次重音；处处重读等于没有重读。
- 反话、讽刺的重音落在被反讽的词上，语气比字面意思“多拐一个弯”。

**停顿分两类：**
- **逻辑停顿**：按语法断句，帮助听清；短（0.2–0.4 秒），不带情绪。
- **心理停顿**：话到嘴边在想、在忍、在找词、在等对方反应；0.5–1.5 秒，是戏的所在。必须写清停在哪个词前、停顿期间脸上发生什么（例如“说到‘你’之后停住，目光下落，下颌收紧，再说出后半句”）。
- 沉默超过 1.5 秒时，要给沉默一个可见内容（对视、回避、呼吸、手上动作），否则会被生成成卡顿。

## B6. 语速与时间预算（可计算）

写完时间轴必须按字数核对每个时间窗能不能说完。中文参考值：

| 状态 | 语速 |
| --- | --- |
| 正常交谈 | 约 4 字/秒 |
| 激动、争吵、抢话 | 5–6 字/秒 |
| 克制、沉重、威胁、低声 | 2.5–3 字/秒 |
| 喊口号、霸气台词（一字一顿） | 2–2.5 字/秒 |
| 逻辑停顿 | 0.2–0.4 秒 |
| 心理停顿 | 0.5–1.5 秒 |
| 开口前准备（吸气、嘴唇微张） | 0.2–0.5 秒 |
| 说完后的余波反应 | 至少 0.5 秒 |

**算法：** 台词时长 ≈ 字数 ÷ 语速 + 停顿合计 + 开口准备；再加上听者反应和余波。超出时间窗时，按顺序处理：① 删可选表情和铺垫；② 重新分配未锁定的时间；③ 仍不够，向用户说明并询问改哪一项（台词、语速或时长），不能交付说不完的时间轴，也不能擅自删改用户台词。

## B7. 按类型校准表演尺度

“克制 / 外放”之外，还要选对**类型的表演语法**：

- **生活流 / 现代正剧**：动作小、口语化、允许不完整的句子和语气词；重音少，停顿多；避免舞台腔。
- **古装 / 史诗 / 神话正剧**：气沉、咬字完整，句尾不上扬，停顿更长更稳；动作少而有分量，“定”比“动”更有力量；霸气台词一字一顿，靠胸腔共鸣而不是尖叫。
- **喜剧**：
  - 铺垫 → 包袱：包袱之前留 0.3–0.6 秒的“空”，包袱说得干脆，不笑场；
  - 延迟反应：听到荒唐的话先正常回应，0.5–1 秒后才反应过来（double take）；
  - 面无表情地说荒唐话（deadpan），反差越大越好笑；
  - 自作聪明 → 翻车：先装、后破功，破功要快、要狠；
  - 不要每句都挤眉弄眼，好笑来自节奏和反差，不来自表情幅度。
- **方言、口音**：只在用户要求时使用，写清方言种类和程度（轻微口音 / 完整方言）。

## B8. 跨片段的情绪衔接（分段生成必用）

分段生成时，每段开头不能从零起演。在“当前状态”里加入**情绪当前状态**：
- 上一段结束时人物的情绪和强度（例：怒意 7/10，尚未发泄）；
- 生理残留：呼吸是否还没平复、声音是否还沙哑、眼眶是否还红；
- 视线停在哪里、身体朝向哪里；
- 上一段最后一句台词的余音：本段第一个反应要回应它（听者反应、反驳、沉默）。

本段开头 1–2 秒先演“残留”，再进入本段的新目标。

## B9. 镜头与表演配合

- **视线匹配**：正反打时，A 看画左，B 必须看画右，跨镜头保持一致；人物看向画外对象时写清是画左还是画右、高还是低。
- **看镜头**：除非用户要求（独白、打破第四面墙、讨要三连这类直接对观众说话），否则人物不看镜头。
- **给剪辑留头尾**：每个有台词的镜头，开口前留 0.3–0.5 秒的准备，说完后留 0.5 秒反应，方便剪辑师找剪点。
- **景别与幅度**：特写只承载 1 个微小变化；中景可以承载视线 + 身体；全景要靠走位和姿态，脸上的细节看不见就不要写。

## B10. AI 生成的常见误演（按场景挑 2–4 条写进禁止项）

- 持续微笑、每句话都带笑；
- 表情过度、挤眉弄眼，所有情绪都做成夸张的大表情；
- 说话时眼神空、对不上对象，或无故直视镜头；
- 口型与台词不同步、闭着嘴说话；
- 多种情绪糊成一张“淡淡忧伤脸”，看不出变化；
- 所有台词同一个音高、同一个速度，像念稿；
- 两人匀速轮流说话，没有反应、没有接话节奏；
- 哭戏只有眼泪，呼吸和声音没有变化；
- 愤怒只会大喊，没有压抑和蓄积；
- 头发、衣服无风乱飘；
- 角色说话时身体完全僵住，或反过来手一直乱动。

只挑和本段表演最相关、最可能出错的几条，不要整张表复制。

## B11. 输出前的文戏自检

- [ ] 每句台词都有说话人、行动动词、听者反应和接话方式；
- [ ] 每次情绪或策略转换都有触发，并有“意识到”的瞬间；
- [ ] 地位关系清楚，若有翻转，翻转点落在具体台词或动作上；
- [ ] 调度（如有）对应关系变化，景别能看得见；
- [ ] 每句只有一个主重音，心理停顿位置和停顿期间的表情写清；
- [ ] 每个时间窗按字数和语速核算过，说得完，留有反应时间；
- [ ] 表演尺度符合类型（生活流、史诗正剧、喜剧等）；
- [ ] 分段生成时已继承上一段的情绪当前状态；
- [ ] 视线方向跨镜头一致，除非要求否则不看镜头；
- [ ] 禁止项里写了本段最可能出现的 2–4 种误演。
