#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《红绳》Step 5 — v2.1 校对线稿生成器（EP02 / EP03 — H3 Ref2VA 适配器）

补上 `05-workflow/output/全流程v2.1_状态核验_20260917.md` 第五节登记的缺口。

背景（09-18 实测更正）：09-17 台账称 EP02「无法用中文解析器」、EP03 片段02–07
「仅为散文，无镜头分解」。09-18 逐文件实测**推翻**该结论：
  - EP03 全 16 段的 `视频提示词.md` 均为标准 Ref2VA 六段结构，
    `detailed_description` 内含 `[Shot N] 在 XX.XXX 秒处，[景别]：动作。，使用 [Camera]`；
  - EP02 片段 04–12、14–16 同样含 `[Shot N]`（片段04 为英文 Ref2VA，
    片段05–12 为中文 Ref2VA），片段13/17 走「动作流」但纯提示词 `.txt` 内亦有 `[Shot N]`。

故本脚本按 Ref2VA 结构解析 `detailed_description` 段内的 `[Shot N]`，逐镜转写为
六宫格 / 九宫格黑白校对线稿提示词。**只解析、只拆分，不新增镜头、不改写动作、
不编造剧情**；不取 `<Picture N>` 绑定行里的「对应 [Shot 1] 至 [Shot 3]」这类引用行。

核心原则（v2.1）：**线稿是对 Step 4 视频提示词的视觉校对**。

用法：
    python generate_ep0203_v21_lineart.py --plan
    python generate_ep0203_v21_lineart.py --dry-run
    python generate_ep0203_v21_lineart.py --ep ep03 --only 01 02
    python generate_ep0203_v21_lineart.py --ep ep02 --ep ep03          # 生成（需生图通道）
"""

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import img_api  # noqa: E402  （65535.space 迁移后的生图适配层）
from generate_ep_v21_lineart import (  # noqa: E402
    PROJECT, WF, OUTPUT_DIR, LOG_DIR,
    STYLE, LAYOUT, NO_TEXT, FORBID, IDENTITY_PREFIX, IDENTITY_BASE,
    MODEL, SIZE, RESOLUTION, TIMEOUT, CONCURRENCY,
    grid_for, distribute,
)

SUPPORTED = {"ep02", "ep03"}

SECTION_KEYS = [
    "subject_definitions", "summary", "retention_analysis",
    "detailed_description", "overall_soundscape", "non_diegetic_music",
    "negativePrompt",
]

# 景别词（用于从 [方括号] 或「，景别：」中识别）
SIZE_WORDS = [
    "侧面大远景", "侧面跟拍", "侧面中景", "侧面全景", "跟拍中景", "双人中景",
    "过肩中景", "中远景", "大远景", "大全景", "中全景", "中近景",
    "远景", "全景", "中景", "近景", "特写",
]
# 英文景别 → 中文标注（仅作标注，不改写原文动作）
SIZE_EN = [
    (r"extreme\s+wide|extreme\s+long", "大远景"),
    (r"medium[-\s]close[-\s]two[-\s]shot", "中近景（双人）"),
    (r"medium[-\s]wide|wide\s+shot", "中全景"),
    (r"medium\s+close[-\s]up", "中近景"),
    (r"close[-\s]up", "近景"),
    (r"medium\s+shot", "中景"),
    (r"\bwide\b", "远景"),
]
_TIME_PATS = [
    r"在\s*([0-9]{1,2}:[0-9]{2}\.[0-9]{3})\s*处",
    r"在\s*([0-9.]+)\s*秒处",
    r"\bAt\s*([0-9]{1,2}:[0-9]{2}\.[0-9]{3})",
    r"\bAt\s*([0-9.]+)\b",
]


def _infer_size(text: str) -> str:
    """从机位/动作原文里推断景别标注（只作标注，不改写原文）。"""
    for pat, cn in SIZE_EN:
        if re.search(pat, text, re.I):
            return cn
    for w in sorted(SIZE_WORDS, key=len, reverse=True):
        if w in text:
            return w
    return ""


# ── 解析 ────────────────────────────────────────────────────────────
def section_body(text: str, key: str) -> str:
    """取 `key:` 到下一个段名之间的正文（兼容 `detailed_description: 内容` 同行写法）。"""
    m = re.search(r"(?m)^[ \t]*#*[ \t]*" + re.escape(key) + r"[ \t]*:[ \t]*", text)
    if not m:
        return ""
    start = m.end()
    keys = "|".join(re.escape(k) for k in SECTION_KEYS)
    nxt = re.search(r"(?m)^[ \t]*#*[ \t]*(?:" + keys + r")[ \t]*:", text[start:])
    end = start + nxt.start() if nxt else len(text)
    return text[start:end].strip()


def parse_index(ep: str):
    """从 `05-workflow/epXX/剧本片段索引.md` 取 片段号 → (标题, 时间位)。"""
    p = WF / ep / "剧本片段索引.md"
    out = {}
    if not p.exists():
        return out
    for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^\|\s*(\d{1,2})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", ln)
        if m:
            out[m.group(1).zfill(2)] = (m.group(2).strip(), m.group(3).strip())
    return out


def parse_shots(text: str):
    """解析 `detailed_description` 内的 `[Shot N]` 块。返回 [{n, time, size, cam, act, voice}]。"""
    body = section_body(text, "detailed_description")
    if not body:
        return []
    marks = list(re.finditer(r"\[Shot\s*(\d+)\]", body))
    if not marks:
        return []
    shots, seen = [], {}
    for i, m in enumerate(marks):
        n = m.group(1)
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        blk = body[m.end():end].strip()
        if n in seen:                      # 同一编号重复时保留最长块
            if len(blk) > len(seen[n]):
                seen[n] = blk
                for s in shots:
                    if s["n"] == n:
                        s.update(_split_fields(blk))
            continue
        seen[n] = blk
        rec = {"n": n}
        rec.update(_split_fields(blk))
        shots.append(rec)
    return shots


def _split_fields(blk: str):
    """把一个 [Shot N] 块拆成 time / size / cam / act / voice（payload 全部取自原文）。"""
    work = blk.strip()
    t = ""
    for pat in _TIME_PATS:
        m = re.search(pat, work)
        if m:
            t = m.group(1)
            work = (work[:m.start()] + work[m.end():]).strip()
            break

    work = re.sub(r"^[，,]?\s*持续至\s*[0-9:.]+\s*[。，,]?", "", work).strip()
    work = re.sub(r"^视频\s*", "", work).strip()

    size, cam = "", ""
    mb = re.match(r"^\s*((?:\[[^\]]*\]\s*)+)", work)
    if mb:
        brackets = [b.strip() for b in re.findall(r"\[([^\]]*)\]", mb.group(1))]
        work = work[mb.end():].strip()
        if brackets:
            size = brackets[0]
            if len(brackets) > 1:
                cam = "，".join(brackets[1:])
    else:
        # `，景别：` —— 捕获段禁止含数字，避免把 `在00:00.000` 误当景别
        m2 = re.match(r"^[，,]?\s*([^，,：:。0-9]{1,10})\s*[：:]", work)
        if m2:
            size = m2.group(1).strip()
            work = work[m2.end():].strip()

    if not cam:
        # 排除否定语境的 `使用`（如「禁止使用连续变焦…来代替切镜」），否则会把禁项当机位
        mc = re.search(r"(?<!禁止)(?<!不得)(?<!不能)(?<!避免)(?<!不要)"
                       r"使用\s*([^。；]{4,80})", work)
        if mc:
            cam = mc.group(1).strip("，,、 ")
            work = (work[:mc.start()] + work[mc.end():]).strip()

    if not cam:                                   # 英文 Ref2VA
        me = re.search(r"\bUse\s+(a\s+[^.；]{3,90})[.。]", work)
        if me:
            cam = me.group(1).strip()
        else:
            me = re.search(r"\bcut to\s+(a\s+[^.,；]{3,90})", work)
            if me:
                cam = me.group(1).strip()

    voice = [d.strip() for d in
             re.findall(r"<d>\s*(?:\[[^\]]*\]\s*)?(.*?)</d>", work, re.S) if d.strip()]

    act = re.sub(r"<d>.*?</d>", "", work, flags=re.S)
    # 只清理「说话人报幕」脚手架，不删动作信息
    act = re.sub(r"(?:说话人|[\u4e00-\u9fa5A-Za-z0-9 ]{1,12}\s*\(S\d\))\s*"
                 r"(?:在画面内面对交流对象、[^：:]*|以对应声线说)?[：:]\s*", " ", act)
    act = re.sub(r"(?:^|\s)(?:<Subject\s*\d+>|[\u4e00-\u9fa5]{1,6})?（S\d+）说[：:]\s*", " ", act)
    # `<Picture N>` 是首帧/参考锚点引用：转写为中文标注，避免模型去画"图片边框"
    act = re.sub(r"<Picture\s*(\d+)>", r"（首帧锚点 图片\1）", act)
    act = re.sub(r"\s{2,}", " ", act).strip(" ，,。；;")
    # 摘除字段后可能留下重复标点（如 `开始。。`），折叠一次
    act = re.sub(r"[。]{2,}", "。", act)
    act = re.sub(r"[，,]{2,}", "，", act)
    act = re.sub(r"[？?]{2,}", "？", act)

    if not size:
        size = _infer_size((cam + " " + act)) or "未显式标注"

    return {"time": t, "size": size, "cam": cam, "act": act, "voice": voice}


def _split_act(act: str):
    """把单镜动作拆成前段/后段（仅按原文标点，不改写）。兼容中文与英文。"""
    for sep in ("；", "，随后", "，然后"):
        i = act.find(sep)
        if 4 < i < len(act) - 4:
            return act[:i + 1].strip(), act[i + len(sep):].strip()
    if not re.search(r"[\u4e00-\u9fa5]", act):        # 英文：按句号切
        k = act.find(". ")
        if 20 < k < len(act) - 20:
            return act[:k + 1].strip(), act[k + 2:].strip()
    mid = len(act) // 2
    j = act.find("，", mid)
    if j == -1:
        j = act.find("，", 0, mid)
    if j > 4:
        return act[:j].strip(), act[j + 1:].strip()
    return act, ""


def build_cells(shots, cells):
    """把 cells 个格子分配到 len(shots) 个镜头（不新增镜头，只拆分或延续）。"""
    alloc = distribute(len(shots), cells)
    out, idx = [], 0
    for sh, k in zip(shots, alloc):
        if k <= 1:
            idx += 1
            out.append({"cell": idx, "shot": sh["n"], "text": sh["act"],
                        "voice": sh["voice"]})
            continue
        head, tail = _split_act(sh["act"]) if k == 2 else (sh["act"], "")
        for j in range(k):
            idx += 1
            if j == 0:
                t = head
            elif j == 1 and tail:
                t = tail
            else:
                t = ("延续本镜动作的后续阶段，机位、景别、人物位置保持不变，"
                     "停在动作完成态")
            t = t.strip().rstrip("；;，,")
            if len(t) < 10:
                t = (t + "——保持本镜机位与景别不变，只延续上一格的人物位置与空间关系，"
                          "无新人物、无新动作。").strip("；")
            out.append({"cell": idx, "shot": sh["n"], "text": t,
                        "voice": sh["voice"] if j == 0 else ""})
    return out


def parse_bindings_from_inventory(d: Path):
    """当提示词本体没有参考图绑定时，回退到 `素材清单.md` 的参考图清单。"""
    inv = d / "素材清单.md"
    if not inv.exists():
        return []
    out = []
    for ln in inv.read_text(encoding="utf-8", errors="replace").splitlines():
        s = ln.strip().lstrip("-*# ").strip().strip("`")
        if re.match(r"^`?(?:@图片|图片)\s*\d+", s):
            out.append(s)
    return out


def build_prompt(ep: str, num: str, title: str, span: str, text: str,
                 bindings_fallback=None):
    shots = parse_shots(text)
    if not shots:
        return None, "未解析到 detailed_description 内的 `[Shot N]`，格式不受支持"

    grid, cells = grid_for(len(shots))
    beats = build_cells(shots, cells)

    bindings = []
    for ln in text.splitlines():
        s = ln.strip()
        if re.match(r"^([-*]\s*)?`?@图片\s*\d+", s) or re.match(r"^[-*]\s*`?image\d+", s):
            bindings.append(s.lstrip("-* ").strip())

    scene = section_body(text, "summary")
    styleb = section_body(text, "retention_analysis")
    sound = section_body(text, "overall_soundscape")
    neg = section_body(text, "negativePrompt")

    corr = "；".join(f"格{b['cell']}↔SHOT {b['shot']}" for b in beats)
    corr_head = (
        f"{'六' if cells == 6 else ('九' if cells == 9 else '四')}格节拍"
        f"（逐格对应本段视频提示词的第 1–{len(shots)} 个镜头：{corr}；"
        f"不得出现视频提示词之外的新机位、新人物或新剧情）："
    )

    by_n = {s["n"]: s for s in shots}
    beat_lines = []
    for b in beats:
        sh = by_n[b["shot"]]
        tag = f"{b['cell']}. [{sh['n']}镜｜{sh['size']}]"
        if sh["cam"]:
            tag += f" {sh['cam']}："
        else:
            tag += "："
        line = f"{tag}{b['text']}"
        if b["voice"]:
            line += ("（声音提示，用紫色标注本格对白，不入画："
                     + "／".join(b["voice"]) + "）")
        beat_lines.append(line)

    parts = [
        f"《红绳》第{int(ep[-2:])}集 片段{num}《{title}》校对线稿"
        + (f"（{span}）" if span else "") + "。",
        LAYOUT,
        "目标尺寸 2K 级清晰度，16:9 横版。",
        STYLE,
        NO_TEXT,
    ]
    if scene:
        parts.append("场景（照抄本段视频提示词的 summary）：" + scene)
    if styleb:
        parts.append("保留关系（照抄 retention_analysis，线稿只取空间与身份信息）：" + styleb)
    if not bindings and bindings_fallback:
        bindings = list(bindings_fallback)
    parts.append(IDENTITY_PREFIX + ("；".join(bindings) if bindings else "（本段无参考图绑定行）"))
    parts.append(IDENTITY_BASE)
    parts.append(corr_head)
    parts += beat_lines
    if sound:
        parts.append("本段声效（只作紫色标注参考，不入画）：" + sound)
    if neg:
        parts.append("本段禁止项（转写自 negativePrompt）：" + neg)
    parts.append(FORBID)

    slot = "?"
    m = re.search(r"@图片\s*(\d+)", text) or re.search(r"image(\d+)", text)
    if m:
        slot = m.group(1)

    return {
        "ep": ep, "num": num, "title": title, "span": span, "grid": grid,
        "cells": cells, "shots": len(shots), "slot": slot,
        "prompt": "\n".join(p for p in parts if p),
    }, None


def read_prompt_file(d: Path):
    """返回候选提示词文件（按优先级）：视频提示词.md → *视频提示词*.md → *.txt。

    动作流片段（如 EP02 片段13）的 `视频提示词.md` 只是说明页，
    真正的 Ref2VA 主提示词在 `动作流_H3纯提示词.txt`，故需逐个回退。
    """
    cands = []
    md = d / "视频提示词.md"
    if md.exists():
        cands.append(md)
    cands += [p for p in sorted(d.glob("*视频提示词*.md")) if p not in cands]
    cands += sorted(p for p in d.glob("*.txt") if p not in cands)
    for p in cands:
        txt = p.read_text(encoding="utf-8", errors="replace")
        if txt.strip():
            yield p, txt


def parse_slot(d: Path, text: str) -> str:
    """确定 `@图片N` 上传槽位：提示词内 → 素材清单.md → 未知。"""
    m = re.search(r"@图片\s*(\d+)", text)
    if m:
        return m.group(1)
    inv = d / "素材清单.md"
    if inv.exists():
        it = inv.read_text(encoding="utf-8", errors="replace")
        hits = re.findall(r"(?:@图片|图片)\s*(\d+)", it)
        if hits:
            return hits[0]
    return "?"


def collect(eps):
    rows = []
    for ep in eps:
        if ep not in SUPPORTED:
            rows.append((ep, None, "", "", "", None, f"不在本适配器范围：{ep}"))
            continue
        idx = parse_index(ep)
        for d in sorted((WF / ep).glob("红绳片段*")):
            if not d.is_dir():
                continue
            m = re.search(r"(\d+)", d.name)
            num = m.group(1).zfill(2) if m else ""
            title, span = idx.get(num, ("", ""))
            p, err, used = None, "无提示词文件", ""
            for src, text in read_prompt_file(d):
                cand, cerr = build_prompt(ep, num, title, span, text,
                                          parse_bindings_from_inventory(d))
                if cand:
                    p, err, used = cand, None, src
                    p["slot"] = parse_slot(d, text)
                    p["source"] = src.relative_to(PROJECT).as_posix()
                    prefix = f"@图片{p['slot']}_" if p["slot"] != "?" else "（槽位未定）"
                    p["file"] = (f"{prefix}第{int(ep[-2:]):02d}集"
                                 f"片段{num}{title}_线稿.png")
                    break
                err = f"{src.name}: {cerr}"
            rows.append((ep, d, num, title, span, p, err))
    return rows


def write_plan(rows, stamp):
    items, problems = [], []
    for ep, d, num, title, span, p, err in rows:
        if p:
            items.append({
                "ep": ep, "segment": num, "title": title, "span": span,
                "grid": p["grid"], "cells": p["cells"], "shots": p["shots"],
                "slot": p["slot"], "file": p["file"], "source": p["source"],
                "state": "待生成（生图通道阻塞）",
            })
        else:
            problems.append({"ep": ep, "dir": d.name if d else "", "reason": err})
    plan = {"generated": stamp, "items": items, "unsupported": problems}
    (LOG_DIR / f"step5_lineart_plan_EP02-EP03_{stamp}.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [f"# 《红绳》Step 5 校对线稿清单（EP02–EP03 · Ref2VA 适配器）",
          "", f"> 生成时间：{stamp}　｜　来源：`05-images/scripts/generate_ep0203_v21_lineart.py --plan`",
          "> 规则：线稿基于 Step 4 视频提示词 `detailed_description` 内的 `[Shot N]` 生成，",
          "> 只做拆分不新增镜头；标题取自各集 `剧本片段索引.md`。",
          "", f"## 一、可生成片段（{len(items)}）", "",
          "| 集 | 片段 | 标题 | 时长位 | 版式 | 格数 | 镜头数 | 槽位 | 目标文件 |",
          "|---|---|---|---|---|---|---|---|---|"]
    for it in items:
        md.append(f"| {it['ep']} | {it['segment']} | {it['title']} | {it['span']} | "
                  f"{it['grid']} | {it['cells']} | {it['shots']} | @图片{it['slot']} | `{it['file']}` |")
    md += ["", f"## 二、暂不支持自动生成（{len(problems)}）", "", "| 集 | 目录 | 原因 |", "|---|---|---|"]
    for pr in problems:
        md.append(f"| {pr['ep']} | {pr['dir']} | {pr['reason']} |")
    md += ["", "## 三、生图通道就绪后的命令", "", "```cmd",
           "cd D:\\HermesWorkspace\\ai小说\\红绳\\05-images",
           "set IMG_API_KEY=<新平台有效Key>（在 https://my.65535.space 生成/转移）",
           "set IMG_BASE_URL=https://task-api-1-cn.65535.space",
           "python scripts\\img_api.py                                     :: 只读自检 Key",
           "python scripts\\generate_ep0203_v21_lineart.py --ep ep02 --ep ep03", "```",
           "",
           "> 09-20 实测：旧主机 img-cn/api/api-cn.65535.space 已 502 停用（平台迁移），",
           "> 生图统一改走新平台任务 API，由 `scripts/img_api.py` 适配。", ""]
    path = LOG_DIR / f"Step5_线稿清单_EP02-EP03_{stamp}.md"
    path.write_text("\n".join(md), encoding="utf-8")
    return path


def generate_one(p):
    """生成单张校对线稿。失败如实返回原因，不伪造图片。"""
    path = OUTPUT_DIR / p["file"]
    if path.exists():
        return {"file": p["file"], "status": "skip"}
    if not img_api.api_key():
        return {"file": p["file"], "status": "fail", "err": "IMG_API_KEY 未设置"}
    t0 = time.time()
    try:
        raw, _doc = img_api.generate_image(
            p["prompt"], size=SIZE, resolution=RESOLUTION,
            model=MODEL, timeout=TIMEOUT)
    except img_api.ImgApiError as e:
        return {"file": p["file"], "status": "fail", "err": str(e)[:200]}
    except Exception as e:  # noqa: BLE001
        return {"file": p["file"], "status": "fail", "err": repr(e)[:200]}
    path.write_bytes(raw)
    return {"file": p["file"], "status": "ok", "size_kb": round(len(raw) / 1024),
            "cost_s": round(time.time() - t0, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", action="append", default=None)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--plan", action="store_true")
    args = ap.parse_args()

    eps = args.ep or ["ep02", "ep03"]
    rows = collect(eps)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    print(f"任务片段行: {len(rows)}")
    okc = 0
    for ep, d, num, title, span, p, err in rows:
        if p:
            okc += 1
            print(f"  [{ep}/{num}] {title} | {p['grid']} | SHOT={p['shots']} | "
                  f"@{p['slot']} → {p['file']}")
        else:
            print(f"  [{ep}/{d.name if d else '-'}] 跳过：{err}")

    plan_path = write_plan(rows, stamp)
    print(f"\n可生成 {okc} / 合计 {len(rows)}")
    print(f"清单: {plan_path}")

    if args.plan:
        return 0

    if args.dry_run or not img_api.api_key():
        if not img_api.api_key():
            print("\n⚠ IMG_API_KEY 未设置：仅打印提示词，未调用接口。")
        for ep, d, num, title, span, p, err in rows:
            if not p:
                continue
            if args.only and num not in args.only:
                continue
            print("=" * 72)
            print(f"[{ep} 片段{num}] → {p['file']}")
            print(p["prompt"])
        return 0

    targets = [p for ep, d, num, title, span, p, err in rows
               if p and (not args.only or num in args.only)]
    results = []
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futs = [pool.submit(generate_one, p) for p in targets]
        for f in as_completed(futs):
            res = f.result()
            results.append(res)
            print(f"  {res['status']:<5}{res['file']} {res.get('err', '')}")
    ok = [r for r in results if r["status"] == "ok"]
    print(f"\n生成 {len(ok)}/{len(targets)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
