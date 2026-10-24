#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《红绳》Step 5 — v2.1 校对线稿生成器（EP02–EP05 参数化版）

核心原则（v2.1）：**线稿是对 Step 4 视频提示词的视觉校对**。
本脚本逐片段读取 `05-workflow/epXX/红绳片段NN/视频提示词.md`，
把其中的【场景状态】【风格基准】【SHOT动作脚本】与 `@图片N` 身份映射
按原文转写为六宫格 / 九宫格黑白校对线稿提示词，不独立编造剧情、不新增机位。

支持的提示词格式：`## 片段NN｜标题（时间）｜镜头XX-YY` + 【SHOT动作脚本】`SHOT NN｜…`
（EP04 / EP05 全量采用此格式）。
EP02（Ref2VA 英文 subject_definitions + [Shot N]）与 EP03（散文式「画面与动作」）
格式不同，本脚本**拒绝生成**并打印原因，避免用错解析器产出越界线稿。

用法：
    python generate_ep_v21_lineart.py --ep ep04 --dry-run
    python generate_ep_v21_lineart.py --ep ep04 --only 01 02
    python generate_ep_v21_lineart.py --ep ep04 --ep ep05            # 生成（需生图通道）
    python generate_ep_v21_lineart.py --ep ep04 --plan               # 只写清单，不调接口
"""

import argparse
import base64
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

PROJECT = Path(r"D:/HermesWorkspace/ai小说/红绳")
WF = PROJECT / "05-workflow"
OUTPUT_DIR = PROJECT / "05-images" / "storyboard"
LOG_DIR = WF / "output"

# ── 生图通道 ────────────────────────────────────────────────────────
# 09-20 实测：65535.space 平台已迁移，旧 img-cn/api/api-cn 主机全部 502 停用。
# 生图改走新平台「任务 API」，统一由 scripts/img_api.py 适配
# （默认 base = https://task-api-1-cn.65535.space，原生 /v1/tasks + 轮询）。
MODEL = "gpt-image-2"
SIZE = "16:9"               # 原生任务 API 推荐写法：比例 + 2K 档位 → 2048x1152
RESOLUTION = "2k"
TIMEOUT = 300
CONCURRENCY = 3

SUPPORTED = {"ep04", "ep05"}

# ── 通用线稿规则（与 generate_ep01_v21_lineart.py 保持一致）─────────
STYLE = (
    "画风：黑白灰粗铅笔故事板线稿，干净利落的分镜线稿质感；叙事画面严格只用黑白灰，"
    "人物、服装、道具、场景、特效都不得使用实际彩色；只有制作标注允许彩色——"
    "红色＝身体动作与运动方向箭头，蓝色＝摄影机运动与机位标记，绿色＝构图与取景框，"
    "橙色＝光线方向，紫色＝声音与情绪提示。"
)
LAYOUT = (
    "版式：16:9 横版故事板，从左到右、从上到下阅读；格与格之间有清楚的白色分隔线；"
    "每格左上角只放一个极简阿拉伯数字编号，右上角最多放 4 个汉字的分镜标题；"
    "不要大段正文、对白气泡、完整台词框、时间轴、水印、Logo。"
)
NO_TEXT = (
    "文字规则：画面内一切标牌、公告栏、书页、笔记本、屏幕、表格、证件上的文字"
    "一律以无字灰块或极简抽象符号表示，不得出现任何可读文字（中文、英文、数字皆不可）；"
    "对白一律不入画，不得出现字幕、气泡或台词框。"
)
FORBID = (
    "禁止：摄影写实、真人照片、3D 渲染、欧美漫画、低幼卡通、厚涂油画、彩色填充画面、"
    "晴天暖阳、字幕、对白文字、漫画台词气泡、水印、Logo、宫格编号外的任何说明文字。"
)
IDENTITY_PREFIX = (
    "身份锁定（只继承人物外形、服装与年龄感，不继承参考图背景与构图）："
)
# 全局人设基准（AGENTS.md 短剧视觉风格：身份与画风以人设四格为准）
IDENTITY_BASE = (
    "全项目统一基准：陆沉、林晓、王老师、安娜的外形与校服版型以"
    "05-images/人物/陆沉_人设四格.png、林晓_人设四格.png、"
    "王老师_30岁美女教师_日漫四格_v3.png、安娜_高冷杀手学生_日漫四格.png 为准；"
    "王老师固定为 30 岁女性班主任兼语文教师，严禁男性化或学生形象；"
    "普通同学使用同一套日漫赛璐珞语言，不得复刻主角五官、红发绳或红绳。"
)


# ── 解析 ────────────────────────────────────────────────────────────
def read_prompt_file(seg_dir: Path):
    md = seg_dir / "视频提示词.md"
    if md.exists():
        return md, md.read_text(encoding="utf-8", errors="replace")
    txts = sorted(seg_dir.glob("*.txt"))
    if txts:
        return txts[0], txts[0].read_text(encoding="utf-8", errors="replace")
    return None, ""


def section(text: str, key: str) -> str:
    m = re.search(r"【" + re.escape(key) + r"】(.*?)(?=\n【|\Z)", text, re.S)
    return m.group(1).strip() if m else ""


def parse_header(text: str):
    m = re.search(r"(?m)^#+\s*片段\s*(\d+)\s*[｜|]\s*([^（(\n｜|]+)", text)
    if not m:
        return None, "", ""
    num = m.group(1).zfill(2)
    title = m.group(2).strip()
    m2 = re.search(r"[（(]([^）)]*\d[^）)]*)[）)]", text[:200])
    span = m2.group(1).strip() if m2 else ""
    return num, title, span


def parse_bindings(text: str):
    """提取 `@图片N 作为 XXX（描述）` 行原文。"""
    out = []
    for ln in text.splitlines():
        ln = ln.strip()
        m = re.match(r"^(@图片\s*\d+.*)$", ln)
        if m:
            out.append(m.group(1).strip())
    return out


def parse_shots(text: str):
    """解析【SHOT动作脚本】内的 `SHOT NN｜[景别][机位]+[动作] [VFX：…] [对白]`。"""
    block = section(text, "SHOT动作脚本")
    shots = []
    for ln in block.splitlines():
        m = re.match(r"^SHOT\s+(\d+)\s*[｜|]\s*(.+)$", ln.strip())
        if not m:
            continue
        idx, body = m.group(1), m.group(2).strip()
        # `[景别][机位]+[动作] [VFX：…] [对白]`：先去掉字段连接符 `+`，再按 `][` 边界切分
        norm = re.sub(r"\+(?=\[)", "", body)
        parts = [p.strip().strip("[]").strip()
                 for p in re.split(r"(?<=\])\s*(?=\[)", norm) if p.strip()]
        size = parts[0] if len(parts) > 0 else ""
        cam = parts[1] if len(parts) > 1 else ""
        act = parts[2] if len(parts) > 2 else ""
        vfx = ""
        for p in parts[3:]:
            if p.upper().startswith("VFX"):
                vfx = re.split(r"[：:]", p, 1)[-1].strip()
        if act.upper().startswith("VFX") and not vfx:   # 无动作字段的退化情形
            vfx = re.split(r"[：:]", act, 1)[-1].strip()
            act = ""
        shots.append({"n": idx, "size": size, "cam": cam, "act": act, "vfx": vfx})
    return shots


def grid_for(nshots: int):
    if nshots >= 7:
        return "3×3 九宫格", 9
    if nshots >= 5:
        return "2×3 六宫格", 6
    if nshots >= 3:
        return "2×3 六宫格", 6
    return "2×2 四宫格", 4


def split_action(act: str):
    """把单镜动作拆成前段/后段（仅按原文标点拆分，不改写内容）。"""
    for sep in ("；", "，随后", "，然后"):
        i = act.find(sep)
        if 4 < i < len(act) - 4:
            return act[:i + (1 if sep == "；" else 0)].strip(), act[i + len(sep):].strip()
    mid = len(act) // 2
    j = act.find("，", mid)
    if j == -1:
        j = act.find("，", 0, mid)
    if j > 4:
        return act[:j].strip(), act[j + 1:].strip()
    return act, ""


def distribute(nshots: int, cells: int):
    """把 cells 个格子分配到 nshots 个镜头上（不新增镜头，只拆分或延续）。"""
    base = cells // nshots
    extra = cells % nshots
    alloc = [base + (1 if i < extra else 0) for i in range(nshots)]
    return alloc


def build_cells(shots, cells):
    alloc = distribute(len(shots), cells)
    out, idx = [], 0
    for sh, k in zip(shots, alloc):
        if k <= 1:
            idx += 1
            out.append({"cell": idx, "shot": sh["n"], "text": sh["act"], "vfx": sh["vfx"]})
            continue
        head, tail = split_action(sh["act"]) if k == 2 else (sh["act"], "")
        for j in range(k):
            idx += 1
            if j == 0:
                t = head
            elif j == 1 and tail:
                t = tail
            else:
                t = "延续本镜动作的后续阶段，机位、景别、人物位置保持不变，停在动作完成态"
            t = t.strip().rstrip("；;，,")
            if len(t) < 10:
                t = (t + "——保持本镜机位与景别不变，只延续上一格的人物位置与空间关系，"
                         "无新人物、无新动作。").strip("；")
            out.append({"cell": idx, "shot": sh["n"], "text": t,
                        "vfx": sh["vfx"] if j == 0 else ""})
    return out


def build_prompt(ep: str, num: str, title: str, span: str, text: str):
    shots = parse_shots(text)
    if not shots:
        return None, "未解析到【SHOT动作脚本】的 `SHOT NN｜` 行，格式不受支持"

    grid, cells = grid_for(len(shots))
    beats = build_cells(shots, cells)

    bindings = parse_bindings(text)
    scene = section(text, "场景状态")
    styleb = section(text, "风格基准")
    limit = section(text, "输出限制")
    glob = section(text, "全局约束")

    # 格 ↔ SHOT 对应表（防越界，供人工逐格核对）
    corr = "；".join(
        f"格{b['cell']}↔SHOT {b['shot']}" for b in beats
    )
    maxlen = len(shots)
    corr_head = (
        f"{'六' if cells == 6 else ('九' if cells == 9 else '四')}格节拍"
        f"（逐格对应本段视频提示词的第 1–{maxlen} 个镜头：{corr}；"
        f"不得出现视频提示词之外的新机位、新人物或新剧情）："
    )

    beat_lines = []
    for b in beats:
        tag = f"{b['cell']}. [{b['shot']}镜｜{shots[int(b['shot']) - 1]['size']}] " \
              f"{shots[int(b['shot']) - 1]['cam']}："
        line = f"{tag}{b['text']}"
        if b["vfx"] and b["vfx"] not in ("无", "無"):
            line += f"（特效标注，用紫色/橙色标记表达：{b['vfx']}）"
        beat_lines.append(line)

    parts = [
        f"《红绳》第{int(ep[-2:])}集 片段{num}《{title}》校对线稿。",
        LAYOUT,
        "目标尺寸 2K 级清晰度，16:9 横版。",
        STYLE,
        NO_TEXT,
    ]
    if scene:
        parts.append("场景（照抄本段视频提示词的【场景状态】）：" + scene)
    if styleb:
        parts.append("风格基准：本线稿只取其中的构图、天气、光线与空间信息，"
                     "叙事画面仍严格黑白灰——" + styleb)
    parts.append(IDENTITY_PREFIX + ("；".join(bindings) if bindings else "（本段无 @图片 绑定行）"))
    parts.append(IDENTITY_BASE)
    parts.append(corr_head)
    parts += beat_lines
    tail = f"全局约束（同样适用于线稿）：{glob}" if glob else ""
    if tail:
        parts.append(tail)
    if limit:
        parts.append("本段禁止项（转写自【输出限制】）：" + limit)
    parts.append(FORBID)
    return {
        "ep": ep, "num": num, "title": title, "span": span, "grid": grid,
        "cells": cells, "shots": len(shots),
        "source": None, "prompt": "\n".join(p for p in parts if p),
    }, None


def target_name(ep: str, num: str, title: str, slot: str):
    return f"@图片{slot}_第{int(ep[-2:]):02d}集片段{num}{title}_线稿.png"


def collect(eps):
    """返回 [(ep, seg_dir, num, title, span, prompt_dict_or_None, err)]"""
    rows = []
    for ep in eps:
        if ep not in SUPPORTED:
            rows.append((ep, None, "", "", "", None,
                         f"格式不受支持：{ep} 的提示词为 Ref2VA/散文格式，需专用解析器（见报告）"))
            continue
        for d in sorted((WF / ep).glob("红绳片段*")):
            if not d.is_dir():
                continue
            src, text = read_prompt_file(d)
            if src is None:
                rows.append((ep, d, "", "", "", None, "无提示词文件"))
                continue
            num, title, span = parse_header(text)
            if not num:
                rows.append((ep, d, "", "", "", None, "未解析到片段标题行"))
                continue
            p, err = build_prompt(ep, num, title, span, text)
            if p:
                p["source"] = src.relative_to(PROJECT).as_posix()
                m = re.search(r"@图片\s*(\d+)", text)
                p["slot"] = m.group(1) if m else "?"
                p["file"] = target_name(ep, num, title, p["slot"])
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
    (LOG_DIR / f"step5_lineart_plan_{stamp}.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [f"# 《红绳》Step 5 校对线稿清单（EP04–EP05 参数化生成计划）",
          "", f"> 生成时间：{stamp}　｜　来源：`05-images/scripts/generate_ep_v21_lineart.py --plan`",
          "> 规则：线稿基于 Step 4 视频提示词的 SHOT 动作脚本生成，只做拆分不新增镜头。",
          "", f"## 一、可生成片段（{len(items)}）", "",
          "| 集 | 片段 | 标题 | 时长位 | 版式 | 格数 | 视频提示词镜头数 | 上传槽位 | 目标文件 |",
          "|---|---|---|---|---|---|---|---|---|"]
    for it in items:
        md.append(f"| {it['ep']} | {it['segment']} | {it['title']} | {it['span']} | "
                  f"{it['grid']} | {it['cells']} | {it['shots']} | @图片{it['slot']} | `{it['file']}` |")
    md += ["", f"## 二、暂不支持自动生成（{len(problems)}）", "",
           "| 集 | 目录 | 原因 |", "|---|---|---|"]
    for pr in problems:
        md.append(f"| {pr['ep']} | {pr['dir']} | {pr['reason']} |")
    md += ["", "## 三、生图通道就绪后的三条命令", "", "```cmd",
           "cd D:\\HermesWorkspace\\ai小说\\红绳\\05-images",
           "set IMG_API_KEY=<新平台有效Key>（在 https://my.65535.space 生成/转移）",
           "set IMG_BASE_URL=https://task-api-1-cn.65535.space",
           "python scripts\\img_api.py                                        :: 只读自检 Key",
           "python scripts\\generate_ep_v21_lineart.py --ep ep04 --ep ep05", "```",
           "",
           "> 09-20 实测：旧主机 img-cn/api/api-cn.65535.space 已 502 停用（平台迁移），",
           "> 生图统一改走新平台任务 API，由 `scripts/img_api.py` 适配。", ""]
    path = LOG_DIR / f"Step5_线稿清单_EP04-EP05_{stamp}.md"
    path.write_text("\n".join(md), encoding="utf-8")
    return path


def generate_one(p):
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
    ap.add_argument("--ep", action="append", default=None, help="可重复，如 --ep ep04 --ep ep05")
    ap.add_argument("--only", nargs="*", default=None, help="只处理指定片段号，如 01 02")
    ap.add_argument("--dry-run", action="store_true", help="打印提示词，不调接口")
    ap.add_argument("--plan", action="store_true", help="只写清单文件，不调接口")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    eps = args.ep or ["ep04", "ep05"]
    rows = collect(eps)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    print(f"任务片段行: {len(rows)}")
    for ep, d, num, title, span, p, err in rows:
        if p:
            print(f"  [{ep}/{num}] {title} | {p['grid']} | SHOT={p['shots']} | "
                  f"@{p['slot']} → {p['file']}")
        else:
            print(f"  [{ep}/{d.name if d else '-'}] 跳过：{err}")

    plan_path = write_plan(rows, stamp)
    print(f"\n清单: {plan_path}")

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
