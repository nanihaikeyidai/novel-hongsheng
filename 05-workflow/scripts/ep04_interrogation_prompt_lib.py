# -*- coding: utf-8 -*-
"""EP04 审讯线（场 9–15）H3 提示词生成器。

设计要点
--------
30 段如果逐段手写，角色描述、场景描述、风格声明一定会漂移。本模块把
六段结构里**跨段不变**的部分锁成常量（subject_definitions / retention_analysis /
空间轴线 / 风格声明 / 通用 negative），每个片段只提供自己的镜头脚本，
由 build() 拼成完整提示词。

这样保证：
1. 陆沉/老韩/审问室的身份锚点跨 30 段完全一致；
2. 音色声明不会被漏掉——只要片段声明了说话人，build() 自动补 <Audio N> 绑定、
   retention 绑定说明、overall_soundscape 强制人声、negative 静音类禁项；
3. 神态与微动作由 MICRO_SHOTS 提供，且在镜头层强制要求。
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
EP = ROOT / "05-workflow" / "ep04"

# ---------------------------------------------------------------- 跨段常量

LUCHEN_SUBJ = (
    "<Subject 1> 是陆沉，依据参考图：17岁高中男生，黑色短发微乱，白衬衫深色长裤校服，"
    "瘦高，脱离感、克制、眼神防备。他坐在金属桌左侧座位上。"
    "锁定面部五官、发型、校服款式与颜色、年龄感与身材比例。"
    "允许变化：坐姿、呼吸起伏、眼神与眉间肌变化、手部小动作、口型、头部微转。"
    "不允许：换脸、换发型、换服装、受伤痕迹、起身离座（除明确写起身的镜头）。"
)

# 铐住状态（解铐镜头之前使用）——双手从背后改扣在桌面固定环上，活动范围极小
LUCHEN_CUFFED = (
    "他的双手从背后改扣在桌面固定环上——一副银色手铐扣在桌沿的金属固定环上，"
    "活动范围极小，只能小幅移动。"
)

# 已解状态（解铐镜头之后使用）——手铐已打开摘下，双手自由放在桌面
LUCHEN_UNCUFFED = (
    "他的手铐已经被解开：手铐打开着放在桌沿的固定环旁边，"
    "他的双手自由地放在桌面上，可以自由活动。"
)

LAOHAN_SUBJ = (
    "<Subject 2> 是老韩，依据参考人设图：五十多岁的东亚男性，花白头发向后梳理得很规矩，鬓角明显发白，"
    "眼角有鱼尾纹，面部轮廓略宽厚，深灰色夹克袖口卷起两折，深色直筒长裤，左手腕一只素面金属腕表。"
    "神情是长年跑案子磨出来的疲惫，叠一层恰到好处的亲和——嘴角略微放松但不笑，眼神沉稳稳定。"
    "锁定面部五官、花白发型、夹克款式与深灰色、卷起的袖口、腕表、年龄感与身材比例。"
    "允许变化：坐姿、站姿、手部动作、口型、眉间与嘴角的微表情、瓶盖动作、身体前倾的幅度。"
    "不允许：换脸、换发型、换服装、变年轻、出现武器、出现眼镜帽子口罩。"
)

SCENE_SUBJ = (
    "<Subject 3> 是审问室空间，依据参考场景图：机构内部的简约谈话室。灰白色平整墙面，房间无窗。"
    "中央一张冷灰色的长方桌，桌面是整块冷灰色平板，上面有几道浅浅的划痕，"
    "桌子的长边朝着房间纵深方向延伸；桌子左右两侧各一把深灰色椅子，椅子是有直杆靠背的硬椅子。"
    "房间左侧墙从室内看过去，就是一整面均匀的暗灰色平板——"
    "它看起来就是一块平整的灰色墙面，不反射、不透出、不呈现任何镜面效果，"
    "看不到任何形状、任何轮廓、任何影子、任何空间。"
    "暗灰色平板上只泛着一层极淡的均匀光晕，除此之外什么都没有。"
    "重点：暗灰色平板上绝对不出现任何人形、任何轮廓、任何倒影、任何人的影子。"
    "房间纵深正前方偏右是一扇深灰色的厚重门。桌面中央偏左放一只透明玻璃杯盛约七分满温水，"
    "中央偏右放置一个未拆封的汉堡，形状是一个长方形扁平的包装袋——"
    "袋面是浅棕色的牛皮纸色，上面有几处模糊的印刷字样（完全不可读），"
    "袋口有一道锯齿形折边封口，整个包装袋是一块扁平的、微微鼓起的长方体，"
    "从侧面看有明显的厚度而不是圆球形——它必须一眼看出是一个汉堡包装袋，"
    "而不是一个褐色的纸团、石头或立方体。房间正上方冷白色顶灯自上方垂直落下，"
    "桌面中央形成一小片明确亮区，房间四角自然压暗形成渐变阴影。"
    "锁定墙体材质、金属桌造型与位置、两把椅子的左右分布、单向透视玻璃位置、纵深门的位置、"
    "桌面道具的数量与相对位置。允许变化：极轻微光衰减、人物投影随动作微调。"
    "不允许：改变桌子长边方向、改变椅子左右分布、交换门与玻璃位置、出现窗户、出现第二张桌子、"
    "增加房间杂物、桌面出现文件纸张电脑或可读文字、暖黄灯光、阳光。"
)

# 桌沿固定环与手铐（固定环是审问室的固定家具；手铐的状态由 CUFFED / UNDONE 决定）
def cuff_subj(cuff_state: str = "undone") -> str:
    """按状态生成铐具主体描述。

    踩坑记录：原先无论哪个状态都写「允许变化：手铐的咬合状态（铐住→被打开→摘下放在环旁）」，
    这等于给模型发了一张全局许可证，它会在每一段自行挑选状态——实测 09c 段手铐被画成
    「打开着放在桌上」（那是解铐之后的状态），10b/10c 段又画成铐在手腕上，同一条成片里
    前后状态打架。改为按段锁定状态，并把「禁止出现的相反状态」写进 negative。
    """
    if cuff_state == "cuffed":
        state = (
            "本段手铐是【咬合锁住】的状态：铐环闭合，锁舌完全插入锁孔，"
            "两个铐环分别套在陆沉的两个手腕上，短链绷紧连到桌沿的固定环。"
            "本段全程保持咬合锁死，不打开、不松开、不被摘下。"
        )
        # 注意：这里只禁「打开态」，不能写「手铐凭空消失」「手腕上没有铐具」这类
        # 否定描述——它们等于反复提醒模型「铐具可能不在」，实测反而把手铐抹掉了。
        #
        # v6 追加教训（第二次踩否定描述反噬）：v5 的forbid 里写了
        # 「出现第二副手铐」，结果 10c 段桌面右侧真的凭空多出一副手铐。
        # 同一个道理——凡是在禁止句里提到的概念，都会被喂给模型。
        # 唯一安全的做法：用正向数量约束替代否定禁令。
        #   ✗ 「出现第二副手铐」→ ✗ 真的多了一副
        #   ✓ 「全画面只有一副手铐，就是陆沉手腕上这一副」→ 数量被钉死
        forbid = (
            "不允许：铐环张开的形状、打开状态的金属环、铐具变成绳索或扎带。"
        )
        # v7 追加：连「除此之外没有任何手铐」也不能写——v6 实测它照样把多余铐具
        # 画出来了。凡是否定句、凡是提「别的铐具在哪」的概念，都会喂给模型。
        # 数量只能这样表达：唯一存在的那一副在哪、是什么形态，全说清楚，
        # 不再额外声明「别的没有」。
        only = "全画面里唯一存在的一副手铐，就是铐在陆沉两个手腕上的这一副。"
    elif cuff_state == "unlocking":
        state = (
            "本段手铐经历一次由锁到开的完整过程：起始为咬合锁住，"
            "随后老韩用钥匙打开锁舌、两个铐环张开、手铐被摘下并放在桌沿固定环旁边。"
            "这一过程必须被完整看到，不跳过、不瞬移。"
        )
        forbid = (
            "不允许：镣铐凭空消失、链条变长、铐具变成绳索或扎带。"
        )
        only = "全画面里唯一存在的那副手铐，就是这一副，从锁住到打开只发生它自己的变化。"
    else:  # undone
        state = (
            "本段手铐是【已经打开并摘下】的状态：两个铐环张开、合拢口朝上，"
            "整副手铐平放在桌沿的金属固定环旁边，短链松松地垂在桌面上。"
            "本段全程保持这个状态，手铐不再回到陆沉手腕上。"
        )
        forbid = (
            "不允许：手铐套在手腕上的样子、铐环闭合的形状、锁舌插入的形状、绷紧的链条。"
        )
        only = "全画面里唯一存在的那副手铐，就是桌沿固定环旁这副展开的铐具。"
    allow = ("允许变化：戴在手腕上的铐具随手臂动作的极小角度变化。"
             if cuff_state == "cuffed" else "允许变化：手铐在桌面上的细微位移。")
    # v5 踩坑记录：v4 三段的落盘提示词完全一致，但只有 09c（手部特写）把铐具画在
    # 手腕上，10a/10b/10c（均为中景全景）全都把铐具画成了桌面上一副张开的金属环。
    # 根因不在状态描述，而在**主语与位置锚点的顺序**：v4 的开头是
    # 「<Subject 4> 是桌沿的固定环与手铐，桌沿处一个灰色的金属固定环，
    #   一副银色手铐与一条短链连在桌沿的固定环上」——
    # 主体和首个位置锚点都在「桌沿」，中景里桌面占比大，模型就照着把铐具摆到了桌面上；
    # 09c 是手部特写，手腕信息压过了它才碰巧画对。
    # 修法：按状态重排主语。cuffed 态把「戴在手腕上的手铐」放在主语位，
    # 桌沿固定环降为链条末端的附属物；同时把「两个铐环分别套在陆沉的两个手腕上」
    # 提到 subject 段最前面，让手腕位置在开头就被锚定。
    if cuff_state == "cuffed":
        head = (
            "<Subject 4> 是陆沉手腕上戴着的一副银色手铐，铐环闭合，锁舌完全插入锁孔，"
            "两个铐环分别套在陆沉的两个手腕上；一条短链从铐环延伸到桌沿的一个灰色金属固定环上。"
        )
        tail = (
            "短链的另一端始终连在桌沿那个灰色金属固定环上。"
            "锁定手铐的银色、铐环闭合的形状、两个铐环分别在两只手腕上、"
            "固定环的颜色与位置、短链的长度有限。"
        )
    else:
        head = (
            "<Subject 4> 是桌沿的固定环与一副银色手铐，桌沿处一个灰色的金属固定环，"
            "手铐放在这个固定环旁边，一条短链连在固定环上。"
        )
        tail = "锁定固定环的颜色与位置、手铐的银色、短链的长度有限。"
    return head + state + tail + allow + only + forbid


CUFF_SUBJ = cuff_subj("undone")

AUDIO_LU = (
    "<Audio 1> 是老韩的声音音色参考，仅用于锁定音色、音域与中年男性基础语速；"
    "不复制该音频的任何原始台词内容，也不复制其背景噪声。"
    "老韩的实际台词以本文档 detailed_description 中的 <d>[Chinese] ...</d> 为准。"
)
AUDIO_CHEN = (
    "<Audio 2> 是陆沉的声音音色参考，仅用于锁定音色、音域与少年男性基础语速；"
    "不复制该音频的任何原始台词内容，也不复制其背景噪声。"
    "陆沉的实际台词以本文档 detailed_description 中的 <d>[Chinese] ...</d> 为准。"
)

RET_STYLE = (
    "渲染风格强制（本作最硬的一条红线）：成片必须是一张日本动画赛璐璐胶片的观感，"
    "而不是照片或3D渲染。具体到人物：皮肤平涂，脸上只用两到三层色块分明暗，"
    "不出现毛孔、皮肤纹路、油光反光和写实高光亮点；头发是一大片深色色块加几根发丝，"
    "不是写实的根根细发；衣服是平涂布料色块加两三条硬边褶皱线。"
    "具体到背景：墙面与金属桌用清晰的建筑线稿勾边，透视规整，金属面只有两三块形状明确的平涂高光，"
    "不做镜面反射。整幅画像马克笔上色的动画原画：深色勾线勾轮廓、色块边缘干净、阴影边界是硬边或半硬边。"
    "参考图仅作为空间结构、道具位置与人物身份锚点使用，"
    "不得把参考图的写实材质与光影质感带入成片；成片画风一律服从日漫赛璐璐。"
)

# 空间轴线：30 段共用一条，永不反转
AXIS = (
    "空间轴线（以参考场景图为准，全片段不可反转）：摄影机机位线始终保持在房间右侧墙一侧，不越轴。"
    "画面左侧墙是一整面均匀的暗灰色平板，看起来是平整的灰色墙面，不反射、不透出、不呈现任何镜面效果，绝对不出现任何人形、轮廓、倒影或影子。"
    "金属桌长边沿画面纵深方向延伸；温水杯在桌面中央偏左、未拆封汉堡在中央偏右；"
    "陆沉固定坐在桌子左侧座位，身体朝向右侧；老韩固定坐在桌子右侧空椅，身体朝向左侧陆沉；"
    "厚门固定在纵深正前方偏右。摄影机在正反打时始终留在轴线同一侧，"
    "陆沉恒在画面左侧、老韩恒在画面右侧，视线方向成对匹配，绝不反转左右。"
)

STYLE_LINE = (
    "15秒，16:9横屏，2K级高清。高精度日漫青春电影感的画面，像一张画得很细的日本动画赛璐璐胶片截图。"
    "人物的皮肤是平的——脸上只有两到三层色块区分明暗，没有皮肤的纹路毛孔，没有油光反光，"
    "脸颊和鼻梁上不出现写实的高光亮点。头发是一大片干净的深色色块加几根分组的发丝，"
    "不是一根根写实的细丝。衣���是一块块平涂的布料色块，褶皱只用两三条硬边阴影线交代。"
    "整个画面像用马克笔上色的动画原画：清楚的深色勾线勾出人物轮廓和五官，"
    "色块的边缘干净，阴影的边界是硬边或者半硬边，颜色过渡不渐变。"
    "背景是手绘的动画背景：墙面和金属桌用清晰的建筑线稿勾边，透视规整，"
    "金属桌面上只有两三块形状明确的浅色高光形状，不是镜面反射。"
    "整体色调冷蓝灰、低饱和，人物面部亮度比背景高一档，脸始终是画面的最清楚的地方。"
    "禁止摄影写实、真人照片质感、照片感、三维渲染、3D游戏画面、CG感、"
    "体积光照、景深虚化模糊、欧美漫画、低幼卡通、厚涂油画。"
)

# 神态与微动作通用要求——每段自动追加，确保用户强调的这两点不遗漏
MICRO_RULE = (
    "神态与微动作要求（本段强制）：说话时必须有清晰可见的口型同步与至少一处微动作承载情绪——"
    "眉间肌的收放、眼睑的半阖或睁开幅度、嘴角单侧上扬、拇指与食指的无意识摩擦、"
    "指节轻叩桌面、肩线的一次放松或绷紧、一次短促的吞咽、"
    "视线的一次短暂回避再回到对方眼睛上。微动作幅度必须小而克制，是真实人物的习惯动作，"
    "不是夸张的舞台表演。情绪转折处必须有 0.3–0.8 秒的微停顿或呼吸变化，"
    "让情绪转折被看见而不是被台词带过。"
)

NEG_COMMON = (
    "subtitles, captions, on-screen text, Chinese characters, title cards, speech bubbles, UI, "
    "watermark, logo, BGM, background music, two speakers at once, both characters talking simultaneously, "
    "silent film, muted audio, no voice, missing dialogue, inaudible voice, whisper only, mumbling, "
    "robotic voice, voice crackling, both faces speaking, wrong speaker lip sync, "
    "camera off the speaker, mouth moving on silent character, "
    "Anna, Zhao Kai, Xiao Yue, any third character, "
    "any figure behind the one-way glass, reflection of another person, one-way mirror showing the other room, "
    "window in the room, sunlight, warm orange lighting, "
    "cheerful cartoon tone, smiling broadly, exaggerated cartoon acting, overacting, "
    # v7 踩坑记录（第三次否定描述反噬，但这次藏在 negative 里）：
    # 这行原来写着 `rope bindings, zip ties, multiple pairs of handcuffs,`
    # ——「多副手铐」虽然是 negative 里的禁止项，但它的实体名词被喂给了模型。
    # 实测 v6 段（带这个条目的段落）桌面右侧真的又凭空多出一副手铐，
    # 而 10a/10b 因为镜头里没露桌面所以没暴露。
    #
    # 结论：negativePrompt 里同样不能出现画面主体的实体名词。
    # 凡是要禁止的东西，必须是画面里本来不存在的概念（如「绳索」「扎带」这种
    # 导演根本没提过的道具），而不能是主角物的「错误版本」。
    # 数量类必须靠正文的正向约束去钉死，negative 无效。
    "rope bindings, zip ties, "
    "identity drift, face change, wrong hair, wrong uniform, younger version of Lao Han, "
    "photorealistic rendering, live action photo, realistic skin texture, skin pores, "
    "oily skin highlights, specular highlight on face, glossy hair, individual realistic hair strands, "
    "realistic cloth folds, detailed fabric texture, mirror reflection on metal table, "
    "subsurface scattering, ray tracing, ambient occlusion, depth of field blur, bokeh, "
    "3D render, CG look, cinematic lighting, rim light, volumetric lighting, "
    "western comic style, chibi, thick oil painting, vertical video, 9:16, "
    "camera crossing the axis, mirrored room layout, swapping left and right, "
    "characters switching sides, eye distortion, hand deformation, extra fingers, "
    "figure behind the glass, silhouette on the wall, human shadow on the wall, "
    "person reflected in the wall, mirror-like wall, glass reflection, "
    "brown lump, paper ball, cubic package, stone-like object, "
    "burger visible without packaging, unwrapped food"
)

NEG_VOICE_F = ", Lu Chen speaking, Lu Chen lip sync"     # 老韩独白时禁止陆沉出声
NEG_VOICE_H = ", Han speaking, Han lip sync"               # 陆沉独白时禁止老韩出声


# ---------------------------------------------------------------- 构建器

def build(
    *,
    seg_id: str,
    title: str,
    summary_body: str,
    shots: list[dict],
    subjects: list[str],
    speaker: str,               # "LAOHAN" | "LUCHEN" | "NONE"
    negative_extra: str = "",
    retention_extra: str = "",
    soundscape_extra: str = "",
    cuff_state: str = "undone",     # "cuffed" 铐住| "undone" 已解 | "unlocking" 正在解
) -> str:
    """拼装一段完整的 H3 六段提示词。

    shots 每项：{range, desc}  desc 必须是完整的镜头段落，含口型与微动作要求。

    cuff_state 决定铐具状态，并同步改写 retention 与 negative：
      cuffed     — 反铐锁在桌沿固定环（场 9 ~ 12e，解铐镜头之前）
      unlocking  — 本段内由老韩解开（12e2 解铐镜头本身）
      undone     — 手铐已打开摘下，双手自由（12e2 之后，即场 13-15）
    默认值是 undone：铐具在剧中只解开一次，之后所有段都应继承「已解」。
    解铐前的段落必须显式传 cuffed。
    """
    lines: list[str] = []
    lines.append("subject_definitions:")
    # 铐具主体按本段状态替换：调用方传的 CUFF_SUBJ 是无状态基线，这里强制换成
    # 与 cuff_state 匹配的锁定版本，避免「允许变化」许可让模型跨段乱选状态。
    cuff = cuff_subj(cuff_state)
    subjects = [cuff if s.startswith("<Subject 4>") else s for s in subjects]
    lines.extend(subjects)
    lines.append("")
    lines.append("summary:")
    lines.append(summary_body)
    lines.append("")
    lines.append("retention_analysis:")

    # 铐具状态三态：retention 必须写清楚，否则模型会漂回默认的「铐住」
    if cuff_state == "undone":
        cuff_ret = (
            "陆沉身份、校服、白衬衫深色长裤、五官、发型、年龄感；"
            "手铐已被解开并摘下放在桌沿固定环旁，双手自由放在桌面——"
            "本段全程维持双手自由的状态，不重新铐上；"
            "座位在桌子左侧这一空间关系不可反转。")
        cuff_neg = ""
    elif cuff_state == "unlocking":
        cuff_ret = (
            "陆沉身份、校服、白衬衫深色长裤、五官、发型、年龄感；"
            "手铐在本段内由老韩解开——先保持铐住，随后打开并摘下，"
            "这一过程必须被完整看到，不跳过、不瞬移；"
            "座位在桌子左侧这一空间关系不可反转。")
        cuff_neg = ""
    else:
        cuff_ret = (
            "陆沉身份、校服、白衬衫深色长裤、五官、发型、年龄感；"
            "反铐状态全程可见且不解除；座位在桌子左侧这一空间关系不可反转。")
        cuff_neg = ""

    lines.append(f"<Subject 1>: fully_preserved - {cuff_ret}")
    lines.append("<Subject 2>: fully_preserved - 老韩身份、花白发型、深灰夹克卷起袖口、腕表、"
                 "五十多岁年龄感与沉稳疲惫神态。")
    lines.append("<Subject 3>: fully_preserved - 审问室灰白墙、金属桌长边纵深方向、两把椅子左右分布、"
                 "左侧墙单向透视玻璃、纵深偏右厚门、桌面温水准偏左与未拆封汉堡准偏右、"
                 "冷白顶光压短投影。空间结构跨镜头完全不变。")
    if cuff_state == "undone":
        lines.append("<Subject 4>: fully_preserved - 桌沿固定环与短链位置不变；"
                     "手铐已打开、铐环分开，安静地搁在固定环旁的桌面上。")
    elif cuff_state == "unlocking":
        lines.append("<Subject 4>: fully_preserved - 桌沿固定环与短链位置不变；"
                     "手铐的状态变化（铐住→打开→摘下）是本段的核心动作，必须完整呈现。")
    else:
        lines.append("<Subject 4>: fully_preserved - 桌沿固定环、短链与金属铐具的咬合状态。")


    # 音频绑定声明——只要声明了说话人就自动补，避免漏引音色
    if speaker == "LAOHAN":
        lines.append("说话人与音频绑定：老韩 (S1) 一一绑定 <Audio 1>，该音频只提供音色与语速基准，"
                     "台词内容一律取自本提示词的 <d>[Chinese] ...</d>。"
                     "本片段只有老韩发声，<Subject 2> (S1) 为唯一说话人。陆沉不分配任何 (Sx) 标签，全程闭口。")
    elif speaker == "LUCHEN":
        lines.append("说话人与音频绑定：陆沉 (S1) 一一绑定 <Audio 2>，该音频只提供音色与语速基准，"
                     "台词内容一律取自本提示词的 <d>[Chinese] ...</d>。"
                     "本片段只有陆沉发声，<Subject 1> (S1) 为唯一说话人。老韩不分配任何 (Sx) 标签，全程闭口。")
    else:
        lines.append("说话人与音频绑定：本片段无对白，不分配任何 (Sx) 标签，"
                     "只有环境音与动作音。")
    if retention_extra:
        lines.append(retention_extra)
    lines.append(RET_STYLE)
    lines.append("")
    lines.append("detailed_description:")
    lines.append(STYLE_LINE)
    lines.append("")
    lines.append(AXIS)
    lines.append("")
    lines.append(MICRO_RULE)
    for s in shots:
        lines.append("")
        lines.append(s["desc"])
    lines.append("")
    lines.append("overall_soundscape:")
    if speaker == "LAOHAN":
        lines.append(
            "全程必须有老韩一段清晰可辨的中文对白人声，使用<Audio 1> 的中年男性音色，"
            "音量与环境音明显可区分，人声是本片段的主要声音内容，不得缺失或被环境音盖住。"
            "老韩由他先说，陆沉全程不说话、不发出任何声音。")
    elif speaker == "LUCHEN":
        lines.append(
            "全程必须有陆沉一段清晰可辨的中文对白人声，使用<Audio 2> 的少年男性音色，"
            "音量与环境音明显可区分，人声是本片段的主要声音内容，不得缺失或被环境音盖住。"
            "陆沉由他先说，老韩全程不说话、不发出任何声音。")
    else:
        lines.append("本片段无对白，只有环境音与动作音，不出现任何人声。")
    lines.append("空调低鸣持续作为底噪。除此之外无其他音效。")
    if soundscape_extra:
        lines.append(soundscape_extra)
    lines.append("")
    lines.append("non_diegetic_music:")
    lines.append("N/A")
    lines.append("")
    lines.append("negativePrompt:")
    neg = NEG_COMMON
    if speaker == "LAOHAN":
        neg += NEG_VOICE_F + ", wrong voice gender for Lao Han, young female voice for Lao Han"
    elif speaker == "LUCHEN":
        neg += NEG_VOICE_H + ", wrong voice gender for Lu Chen, adult female voice for Lu Chen"
    lines.append(neg + negative_extra)
    text = "\n".join(lines)
    return text.rstrip() + "\n"


# ---------------------------------------------------------------- 门禁

def lint(text: str, expect_audio: int, cuff_state: str = "cuffed") -> list[str]:
    """返回问题列表，空列表表示通过。

    cuff_state 用于校验铐具描述与声明的状态是否自洽——
    解铐是跨段的连续动作，提示词与retention 打架会让 H3 画回铐住的画面。
    """
    problems: list[str] = []
    labels = ["subject_definitions:", "summary:", "retention_analysis:",
              "detailed_description:", "overall_soundscape:", "non_diegetic_music:"]
    pos = [text.find(l) for l in labels]
    if any(i < 0 for i in pos):
        missing = [l for l, i in zip(labels, pos) if i < 0]
        problems.append(f"缺标签: {missing}")
    elif pos != sorted(pos):
        problems.append("六段标签顺序错误")
    if not text.startswith("subject_definitions:"):
        problems.append("首行必须是 subject_definitions:")
    declared = len(set(re.findall(r"<Audio (\d+)>", text.split("detailed_description:")[0])))
    if declared != expect_audio:
        problems.append(f"音频不一致：subject_definitions 声明 {declared} 个 <Audio N>，"
                        f"实际应绑定 {expect_audio} 个")
    for bad in re.findall(r"\(S\d+\)\s*<d>", text):
        problems.append(f"重复说话人标签: {bad}")
    if "```" in text or text.lstrip().startswith("#"):
        problems.append("混入 Markdown 标记")
    if "@图片" in text:
        problems.append("混入 @图片N 标记")

    # 铐具状态自洽：镜头层提到铐具时，必须与 cuff_state 相符
    if cuff_state == "undone":
        # 已解段里不能再出现「铐环里」「被铐住」这类仍在束缚的表述
        for bad in ("铐环里", "手铐从背后", "反铐", "铐环内"):
            if bad in text:
                problems.append(f"铐态冲突：cuff_state=undone 但仍出现「{bad}」")
    elif cuff_state == "cuffed":
        if "手铐已被解开" in text or "双手自由地放在桌面" in text:
            problems.append("铐态冲突：cuff_state=cuffed 但描述了解铐")
        # 铐住段绝不能出现「打开着/摘下/放在桌沿旁」——这是成片里手铐状态
        # 前后打架的直接来源，必须在提示词层面就锁死。
        for bad in ("打开着放在", "摘下放在", "放在桌沿固定环旁", "放在桌沿的固定环旁"):
            if bad in text:
                problems.append(f"铐态冲突：cuff_state=cuffed 但出现已解描述「{bad}」")

    # 跨段一致性：禁止再出现全局性的「允许变化：手铐的咬合状态」。
    # 这句等于给模型发许可证，让它在每段自行挑状态，实测已造成成片穿帮。
    if "允许变化：手铐的咬合状态" in text:
        problems.append("铐态冲突：仍存在全局「允许变化：手铐的咬合状态」许可，"
                        "应改为按段锁定的 cuff_subj(cuff_state)")

    # v6 门禁：禁止在提示词里出现「第二副手铐」这类数量否定。
    # 实测 v5 写了「出现第二副手铐」，10c 段桌面右侧真的凭空多出一副——
    # 否定句里提到的概念会被喂给模型。数量必须用正向约束表达。
    for bad in ("出现第二副手铐", "第二副手铐", "出现第二副"):
        if bad in text:
            problems.append(f"数量否定反噬：出现「{bad}」，"
                            "应改为正向约束「全画面里唯一存在的那一副」")

    # v7 门禁：negativePrompt 里也不许出现主角物的实体名词。
    # 实测 `multiple pairs of handcuffs` 写在 negative 里，
    # 10c 段桌面真的凭空多出一副手铐——negative 里同样只是「不被引用的概念」。
    neg_start = text.find("negativePrompt:")
    neg = text[neg_start:] if neg_start >= 0 else ""
    for bad in ("multiple pairs of handcuffs", "second pair of handcuffs",
                "multiple handcuffs", "extra handcuffs"):
        if bad in neg:
            problems.append(f"negative 反噬：negativePrompt 含「{bad}」，"
                            "禁止把主角物的「错误版本」写进 negative")

    # 台词时长门禁：中文自然语速约 4.5 字/秒
    # 台词塞太满会让 H3 加速念白、吞字、语速失真——这就是「乱说话」的根因。
    # 单段上限 55 字（约 12.2 秒），给留白与反应镜头留出时间。
    lines = re.findall(r"<d>\[Chinese\](.*?)</d>", text, re.S)
    total = sum(len(re.sub(r"\s", "", x)) for x in lines)
    if total > 55:
        problems.append(f"台词过密：共 {total} 字，按 4.5 字/秒需 {total / 4.5:.1f} 秒，"
                        f"超出 15 秒片段的可用时长（上限 55 字）")
    for x in lines:
        n = len(re.sub(r"\s", "", x))
        if n > 34:
            problems.append(f"单句过长：{n} 字（需 {n / 4.5:.1f} 秒），"
                            f"单句上限 34 字 —— {re.sub(chr(10), ' ', x)[:24]}…")
    return problems