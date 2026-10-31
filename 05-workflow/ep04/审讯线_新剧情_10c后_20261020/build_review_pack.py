# -*- coding: utf-8 -*-
"""红绳 EP04 审讯线（10c 后）审核包生成：
1) 解析各段 H3 提示词（summary / Picture / Audio / Shot / 对白）
2) 生成参考图宫格（一张图看完所有参考图）
3) 输出审核清单 Markdown
"""
import os, re, json
from PIL import Image, ImageDraw, ImageFont

ROOT = r"D:\HermesWorkspace\ai小说\红绳"
WF = os.path.join(ROOT, "05-workflow")
NEW = os.path.join(WF, "ep04", "审讯线_新剧情_10c后_20261020")
D4 = os.path.join(WF, "ep04", "红绳片段11d4_世界的代价")
OUT = os.path.join(NEW, "审核包_20261031")
os.makedirs(OUT, exist_ok=True)

FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"

SEGMENTS = [
    ("11a", "父亲失踪", os.path.join(NEW, "11a_父亲失踪_H3纯提示词.txt")),
    ("11b", "换个话题", os.path.join(NEW, "11b_换个话题_H3纯提示词.txt")),
    ("11c", "赤瞳", os.path.join(NEW, "11c_赤瞳_H3纯提示词.txt")),
    ("11c2", "母亲死因", os.path.join(NEW, "11c2_母亲死因_H3纯提示词.txt")),
    ("11d", "交易", os.path.join(NEW, "11d_交易_H3纯提示词.txt")),
    ("11d2", "凭什么相信", os.path.join(NEW, "11d2_凭什么相信_H3纯提示词.txt")),
    ("11d3", "父亲留下什么", os.path.join(NEW, "11d3_父亲留下什么_H3纯提示词.txt")),
    ("11d4a", "世界的代价", os.path.join(D4, "11d4a_世界的代价_H3纯提示词.txt")),
    ("11d4b", "帮助我们找到他", os.path.join(D4, "11d4b_帮助我们找到他_H3纯提示词.txt")),
    ("11e", "门外", os.path.join(NEW, "11e_门外_H3纯提示词.txt")),
]

# 状态（来自 连续性台账.md）
STATUS = {
    "11a": "未审核草稿",
    "11b": "未审核草稿",
    "11c": "未审核草稿（v3）",
    "11c2": "未审核草稿",
    "11d": "未审核草稿",
    "11d2": "未审核草稿（v4）",
    "11d3": "未审核草稿",
    "11d4a": "未审核草稿",
    "11d4b": "未审核草稿（v2 语音异常已停用，用 v1）",
    "11e": "**stale**：旧版引用 11d2 出点，须改为承接 11d4b 末帧后重生成",
}

FIXED_PICS = {
    1: os.path.join(NEW, "参考图", "陆沉_正脸.png"),
    2: os.path.join(NEW, "参考图", "老韩_正脸.png"),
    3: os.path.join(ROOT, "05-images", "场景", "场景_ND审问室_日漫v3.png"),
}

AUDIO_DIR = os.path.join(WF, "归档素材", "人物参考音色")
AUDIO_MAP = {
    "陆沉": os.path.join(AUDIO_DIR, "陆沉.wav"),
    "老韩": os.path.join(AUDIO_DIR, "老韩.wav"),
}

LAST_FRAME_CHOICE = {
    "10c": "10c_末帧.png",
    "11a": "11a_末帧.png",
    "11b": "11b_末帧.png",
    "11c": "11c_末帧_v3.png",
    "11c2": "11c2_末帧.png",
    "11d": "11d_末帧.png",
    "11d2": "11d2_末帧_v4.png",
    "11d3": "11d3_末帧.png",
    "11d4a": "11d4a_末帧.png",
    "11d4b": "11d4b_末帧.png",
    "11e": "11e_末帧_v2.png",
}

def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def parse(text):
    out = {"summary": "", "pictures": [], "audios": [], "shots": [], "soundscape": ""}
    # 仅从 subject_definitions 段落取 Picture/Audio（终止于下一个已知小节）
    m_sub = re.search(
        r"subject_definitions:\s*\n(.*?)(?:\n\s*(?:summary:|detailed_description:|retention_analysis:|\[reference generation)|\Z)",
        text, re.S)
    if m_sub:
        for line in m_sub.group(1).splitlines():
            line = line.strip()
            pm = re.match(r"<Picture (\d+)>\s*(.+)", line)
            if pm:
                out["pictures"].append((int(pm.group(1)), pm.group(2).strip()))
            am = re.match(r"<Audio (\d+)>\s*(.+)", line)
            if am:
                out["audios"].append((int(am.group(1)), am.group(2).strip()))
    m = re.search(r"summary:\s*\n(.+?)\n\s*(?:retention_analysis:|detailed_description:)", text, re.S)
    if m:
        out["summary"] = m.group(1).strip()
    if not out["summary"]:
        m2 = re.search(r"\[reference generation \+ keyframe completion\]\s*\n?(.+?)(?:\n\n|\n\[Shot)", text, re.S)
        if m2:
            out["summary"] = m2.group(1).strip()
    # 镜头：兼容 "[Shot 1] 0.00–1.20秒" / "[Shot 2] 1.20秒硬切..." / "[Shot 2] 4.0s，hard cut..."
    marks = list(re.finditer(r"\[Shot (\d+)\]\s*([\d.]+)(?:[–-]([\d.]+))?\s*(?:秒|s)", text))
    for i, mm in enumerate(marks):
        num = int(mm.group(1))
        t0 = float(mm.group(2))
        t1 = float(mm.group(3)) if mm.group(3) else None
        block_end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        body = text[mm.end():block_end].strip()
        if t1 is None:
            t1 = float(marks[i + 1].group(2)) if i + 1 < len(marks) else 15.0
        dialogues = []
        for dm in re.finditer(r"<d>\[Chinese\]\s*(.+?)</d>", body, re.S):
            dialogues.append(dm.group(1).strip())
        story = re.sub(r"<d>.*?</d>", "", body, flags=re.S)
        story = re.sub(r"<Picture (\d+)>", r"[图\1]", story)
        story = re.sub(r"<Subject (\d+)>", r"[角色\1]", story)
        story = re.sub(r"<Audio (\d+)>", r"[音色\1]", story)
        story = re.sub(r"<[^>]+>", "", story)
        story = re.split(r"[。]", story, maxsplit=1)[0].strip()
        story = story.lstrip("，,、；;：: ")
        if len(story) > 120:
            story = story[:119] + "…"
        speaker = ""
        sp = re.search(r"<Subject (\d+)>[^说]*?说[：:,]", body)
        if sp:
            speaker = "Subject " + sp.group(1)
        out["shots"].append({
            "n": num, "t0": t0, "t1": t1,
            "story": story, "dialogues": dialogues, "speaker": speaker,
        })
    ms = re.search(r"overall_soundscape:\s*\n(.+?)\n\s*non_diegetic_music:", text, re.S)
    if ms:
        out["soundscape"] = ms.group(1).strip()
    return out

def pic_path_for(seg, idx, desc):
    # 1) 上段精确末帧优先（描述里可能同时提到角色名）
    m = re.search(r"片段(\w+)的精确末帧", desc)
    if m:
        key = m.group(1)
        fn = LAST_FRAME_CHOICE.get(key, key + "_末帧.png")
        p = os.path.join(NEW, "参考图", fn)
        if os.path.exists(p):
            return p
    # 2) 按描述内容匹配固定参考
    if "陆沉" in desc and "正脸" in desc:
        p = FIXED_PICS[1]
        return p if os.path.exists(p) else None
    if "老韩" in desc and "正脸" in desc:
        p = FIXED_PICS[2]
        return p if os.path.exists(p) else None
    if "审问室" in desc:
        p = FIXED_PICS[3]
        return p if os.path.exists(p) else None
    if "东郊分部大门" in desc or "ND 东郊" in desc:
        p = os.path.join(ROOT, "05-images", "场景", "场景_ND东郊分部大门_薄暮_日漫电影感.png")
        return p if os.path.exists(p) else None
    return None

def main():
    segs = []
    used_pics = {}  # path -> label
    for sid, title, p in SEGMENTS:
        if not os.path.exists(p):
            segs.append({"id": sid, "title": title, "error": "提示词文件缺失"})
            continue
        t = read(p)
        parsed = parse(t)
        pics = []
        for idx, desc in parsed["pictures"]:
            path = pic_path_for(sid, idx, desc)
            label = os.path.basename(path) if path else ("未找到:" + desc[:40])
            pics.append({"idx": idx, "desc": desc, "path": path, "label": label})
            if path:
                used_pics[path] = label
        audios = []
        for idx, desc in parsed["audios"]:
            who = "老韩" if "老韩" in desc else ("陆沉" if "陆沉" in desc else "")
            audios.append({"idx": idx, "desc": desc, "who": who, "path": AUDIO_MAP.get(who, "")})
        segs.append({
            "id": sid, "title": title, "status": STATUS.get(sid, ""),
            "summary": parsed["summary"], "shots": parsed["shots"],
            "soundscape": parsed["soundscape"], "pics": pics, "audios": audios,
        })

    # 固定参考也加入宫格（即使某段没用）
    for i, p in FIXED_PICS.items():
        if os.path.exists(p):
            used_pics[p] = os.path.basename(p)

    # ---- 宫格图 ----
    items = sorted(used_pics.items(), key=lambda kv: kv[1])
    COLS = 4
    TW, TH = 480, 300   # 图片区域
    LABEL_H = 54
    PAD = 14
    rows = (len(items) + COLS - 1) // COLS
    W = COLS * TW + (COLS + 1) * PAD
    H = 90 + rows * (TH + LABEL_H) + (rows + 1) * PAD
    canvas = Image.new("RGB", (W, H), (24, 26, 33))
    d = ImageDraw.Draw(canvas)
    f_title = ImageFont.truetype(FONT_B, 34)
    f_label = ImageFont.truetype(FONT, 20)
    d.text((PAD + 4, 24), "红绳 EP04 审讯线 · 参考图总览（宫格）", font=f_title, fill=(235, 238, 245))
    for i, (path, label) in enumerate(items):
        r, c = divmod(i, COLS)
        x = PAD + c * (TW + PAD)
        y = 90 + PAD + r * (TH + LABEL_H)
        try:
            im = Image.open(path)
            im = im.convert("RGB")
            iw, ih = im.size
            scale = min(TW / iw, TH / ih)
            nw, nh = int(iw * scale), int(ih * scale)
            im = im.resize((nw, nh), Image.LANCZOS)
            canvas.paste(im, (x + (TW - nw) // 2, y + (TH - nh) // 2))
        except Exception as e:
            d.text((x + 10, y + 10), "加载失败", font=f_label, fill=(255, 120, 120))
        d.rectangle([x, y, x + TW, y + TH + LABEL_H], outline=(70, 78, 96), width=2)
        # 标签
        label_text = label
        if len(label_text) > 30:
            label_text = label_text[:29] + "…"
        d.text((x + 10, y + TH + 12), label_text, font=f_label, fill=(210, 216, 230))
    sheet = os.path.join(OUT, "参考图宫格.png")
    canvas.save(sheet)

    # ---- 审核清单 ----
    lines = []
    lines.append("# 红绳 EP04 审讯线（10c 后）· 生成前审核清单\n")
    lines.append(f"- 参考图宫格：`{os.path.relpath(sheet, NEW)}`")
    lines.append(f"- 生成方式：RunningHub 金鱼工作流（AI 应用 webappId 2110357037929558018）")
    lines.append(f"- 规格：15 秒 / 16:9 横屏 / 2K 级高清；无字幕、无 BGM、无水印")
    lines.append("")
    lines.append("## 参考音频（音色库路径）\n")
    for who, p in AUDIO_MAP.items():
        lines.append(f"- {who}：`{p}`" + ("" if os.path.exists(p) else " （文件缺失！）"))
    lines.append("")
    lines.append("## 逐段审核\n")
    for s in segs:
        if "error" in s:
            lines.append(f"### {s['id']} {s['title']}\n\n⚠️ {s['error']}\n")
            continue
        lines.append(f"### {s['id']} {s['title']}\n")
        lines.append(f"- 状态：{s['status']}")
        if s["summary"]:
            lines.append(f"- 段落概要：{s['summary']}")
        lines.append("")
        lines.append("**参考图**\n")
        for pc in s["pics"]:
            lines.append(f"- Picture {pc['idx']}：`{pc['path']}`" if pc["path"] else f"- Picture {pc['idx']}：⚠️ {pc['desc']}")
        if s["audios"]:
            lines.append("")
            lines.append("**参考音频**\n")
            for au in s["audios"]:
                lines.append(f"- Audio {au['idx']}（{au['who']}）：`{au['path']}`" if au["path"] else f"- Audio {au['idx']}：{au['desc']}")
        lines.append("")
        lines.append("**镜头总结**\n")
        for sh in s["shots"]:
            dlg = "；".join(sh["dialogues"]) if sh["dialogues"] else ""
            lines.append(f"- [Shot {sh['n']}] {sh['t0']:.2f}–{sh['t1']:.2f}s · {sh['story']}" + (f" · 台词：{dlg}" if dlg else ""))
        if s["soundscape"]:
            lines.append("")
            lines.append(f"- 声音：{s['soundscape']}")
        lines.append("")
    md = "\n".join(lines)
    md_path = os.path.join(OUT, "审核清单.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(json.dumps({"sheet": sheet, "md": md_path, "images": len(items), "segments": len(segs)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
