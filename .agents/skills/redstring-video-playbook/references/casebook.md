# 案例库：每一次翻车换来的规则

> 来源：`提示词避坑手册.md`（案例索引）、`成片自审与提示词复盘规范.md`、`视频制作技巧_David.md` §八（P09 v7–v10）、`H3提示词生成前必读与标签门禁.md`（成功基线）。
> 用法：写提示词前扫一遍同类；复盘时先在这里找有没有先例，再决定是否新增类型。

---

## 一、失败案例

### P06a r3 → r4：车头朝反 + 栏杆自动抬

| 项 | 内容 |
|---|---|
| 现象 | 车头朝向与剧情相反；道闸栏杆无人操作自己抬起 |
| 归因 | F 朝向数量 / B 无因动作 |
| 触发句 | 写了 `the barrier rises`；车辆只写 `drives in` |
| 改法 | 栏杆：`the guard presses the console button; the barrier arm rises`；车辆：`Car faces AWAY from camera, nose toward the lit tunnel; movement is forward into the ramp only` |
| 沉淀规则 | 会自己动的物体一律「操作者 + 部位 + 动作 + 结果」；车辆要写"车头朝哪、只允许哪个方向移动" |

### P06b：卡面/工牌疑似带字

| 项 | 内容 |
|---|---|
| 现象 | 门禁卡、工牌出现了字样/纹理 |
| 归因 | D 描述缺失 |
| 触发句 | `card reader`、`white ID badge` 只点名未加约束 |
| 改法 | 物件所在行写 `plain surface, no readable text`；工牌直接删或 `blank white rectangular badge, no lettering` |
| 沉淀规则 | "无文字"必须写在**物件所在的那一行**，不能只在别处声明一次 |

### P09 v4 → v5/v6：沈默侧脸丢眼镜

| 项 | 内容 |
|---|---|
| 现象 | 侧脸特写里眼镜消失（正脸还在） |
| 归因 | E 参考图属性漂移 |
| 触发句 | 只在人物定义写了眼镜，镜头行没写 |
| 改法 | `Keep thick black rectangular-rimmed eyeglasses exactly as <Picture 4>—frames on nose bridge and over the ear in every angle including tight side profile.` 主体定义 + 侧脸镜头行双重写死 |
| 沉淀规则 | 越"不美化"的特征越容易丢：眼镜、疤、旧衣、疲惫感、发绳 |

### P09 v4 → v6：手机拿反 + 疑似两部手机

| 项 | 内容 |
|---|---|
| 现象 | 背面贴耳、左右手不一致、画面出现两部手机 |
| 归因 | F 朝向数量歧义 |
| 改法 | `ONE PHONE ONLY. SAME hand pulls and raises it—LEFT hand presses the glowing front/screen face flat to LEFT ear/cheek, fingers gripping. Ear faces the screen side.` |
| 沉淀规则 | 左右/正反/数量三件事永远不留给模型猜：观察者锚点 + 接触面 + `only/one` |

### P09 v5：RunningHub 提交被拦

| 项 | 内容 |
|---|---|
| 现象 | 已去掉 demonic/devil 仍被平台拦截 |
| 归因 | A 负向泄漏 + G 平台术语 |
| 触发 | 大量全大写 `FORBIDDEN`；新增 `rear / rear-cam / upside-down / backwards` |
| 改法 | 保留已通过的 v4 句式；禁止项改 `Avoid: …`；少写 rear/cam/upside/backwards；特效改 teal-blue wispy flame |
| 沉淀规则 | 提交前扫敏感词表 + 控制 `FORBIDDEN` 密度，改写而非删需求 |

### P09 v7 → v10：台词时序错位（四连击）

| 版本 | 现象 | 改法 |
|---|---|---|
| v8 | 门卫镜头出现「晚安」（应硬切后才说） | 门卫全段写 `ZERO「晚安」phonemes`（subject/summary/detailed/soundscape 四处）+ Avoid |
| v8 | 说完后侧脸持机静默过长，尾段又念一遍 | 说完写 `ZERO spoken syllables / lips locked` 到片尾；出字 2–3s 后尽快切回 |
| v9 | 屏字在说话前/同时出现 | 拆两镜：说话镜 `NO on-screen text yet`；下一镜 `lips CLOSED, silent ≥1.5s` 后才出字 |
| v10 | 硬切前仍有「晚安」渗漏（ASR ~3.6–4.6s） | 硬切后先 `lips CLOSED mute 0.3–0.5s`；台词窗锁死 `~5.5–6.5s ONLY`；Avoid 写 `any「晚安」before HARD CUT` |

沉淀规则（已进 SKILL §8）：短句 **ONCE** 四处声明；**说完再出屏字**；**正写 + Avoid 双保险**；**长静默必复读**。

### P11 v4 → v6：门卫三连错

| 项 | 内容 |
|---|---|
| 现象① | 昏迷却睁眼/半睁 |
| 归因 | A 负向泄漏（`FORBIDDEN open or half-open eyes` 把"睁眼"注入） |
| 改法 | 不写"禁止睁眼"，改成 `Face turned down toward the floor; eyes not visible` |
| 现象② | 要求"躺在地上"+"中低机位前景持续可见"，成片变成靠墙瘫坐 |
| 归因 | C 构图矛盾（模型牺牲表演保构图） |
| 改法 | 接受"靠门框瘫坐、头深垂"，或改俯拍/越肩；特写裁到锁骨以上并写 `head stays above the frame` |
| 现象③ | 胸牌出现人名字样 |
| 归因 | D 描述缺失 |
| 改法 | 删胸牌或写 `blank white rectangular badge, no lettering` |
| 现象④ | 解锁后门自动开、且从左边开 |
| 归因 | B 无因动作 / F 朝向歧义 |
| 改法 | `Door stays fully CLOSED after unlock. Only her hand turns the RIGHT-side vertical handle (viewer-right) and pushes the leaf inward.` |
| 沉淀规则 | 昏迷=让眼睛不在画面里；"躺+前景"是矛盾；带字物件要么删要么 blank；门要写"解锁只亮灯" |

---

## 二、成功基线（可复用）

**EP02 片段03「苏婉正面奔向林晓并哭着拥抱」**（RunningHub 任务 `2093361161608327169`，2026-08-29）

有效输入：
- 苏婉人物图、林晓人物图；
- 由文字站位**独立生成的首帧**（不是从故事板裁切）；
- 两条人物音色；
- **未上传故事板图片**。

成功站位：`门口 -> 苏婉 -> 教室过道 -> 林晓/机位`；机位在林晓肩旁朝门口反拍，苏婉实际正对林晓，同时在画面中保持正面可见。

成功对白绑定：苏婉=`<Subject 1> (S1)`/`<Audio 1>`，林晓=`<Subject 2> (S2)`/`<Audio 2>`，三条对白各只出现一次说话人标签。

结论：**故事板像素不进模型 + 分镜逻辑完整文字化 + 纯六段正文 + 唯一说话人标签 + 明确世界轴线**，显著降低站位错误、口型异常和串线。

---

## 三、复盘模板

```markdown
# P{编号}_v{版本}_复盘

## 成片
规格 / 时长 / 任务 ID / 生成耗时

## 抽帧结论（6 格，每 2.5s）
格 1–6：中的 / 没中的

## 问题表
| 现象 | 触发句（引原文） | 归因 |
|---|---|---|
|  |  | A–H / 未遵循既有规则（引用 David 条目） |

## 改法
具体到改哪一句 → 改成什么（另存 v+1，不覆盖旧版）

## 查证记录
对照了避坑手册哪几型；查了 David 文档哪些条目；是否有需要回写手册的新发现

## 结论
是否重跑 / 用什么版本 / 是否已汇报等待确认
```

**判定标准**：每个问题都必须能指向提示词里的具体行；指不出来 = 还没查到底。
