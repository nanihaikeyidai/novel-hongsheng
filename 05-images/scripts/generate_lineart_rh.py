#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《红绳》Step 5 校对线稿 — 批量生成器（RunningHub AI 应用通道）

第 12 轮起：65535.space 与 RunningHub 标准模型均不可用，
改用 RunningHub **AI 应用** `2097866022547181570`（全能图片G-image-2.5文生图高品质版）。

提示词来源：三个既有 v2.1 生成器（逐字复用其 `prompt`，不改写、不新增镜头）：
    scripts/generate_ep01_v21_lineart.py       → STORYBOARDS（EP01，6 张）
    scripts/generate_ep0203_v21_lineart.py     → collect(['ep02','ep03'])（30 张）
    scripts/generate_ep_v21_lineart.py         → collect(['ep04','ep05'])（32 张）
合计 68 张。已存在的目标文件默认跳过（可断点续跑）。

用法：
    python scripts/generate_lineart_rh.py --list                 # 只列清单
    python scripts/generate_lineart_rh.py --eps ep01 --only 01   # 只跑指定
    python scripts/generate_lineart_rh.py                        # 跑全部待生成
"""

import argparse
import importlib.util
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rh_app_img  # noqa: E402

PROJECT = Path(r"D:/HermesWorkspace/ai小说/红绳")
OUTPUT_DIR = PROJECT / "05-images" / "storyboard"
LOG_DIR = PROJECT / "05-workflow" / "output"

# RunningHub NORMAL 账号实测：任务队列上限 = 1。
# 并发 >1 会大量返回 `421 TASK_QUEUE_MAXED`（第 12 轮实测），故串行。
CONCURRENCY = 1

# 第 12 轮实测成本（单张，16:9 / 2k / png）：
#   2097866022547181570 全能图片G-image-2.5文生图高品质版  → ¥0.463 + 2 coins
#   2046794551444119554 全能图片G-2.0-文生图-低价渠道版    → ¥0.100 + 2 coins  ← 默认（便宜 4.6 倍）
APP_HQ = "2097866022547181570"
APP_LOW = "2046794551444119554"
WEBAPP = APP_LOW


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_tasks(eps_filter=None):
    """统一任务表：[{ep, seg, prompt, out, slot}]"""
    tasks = []

    # ── EP01 ──────────────────────────────────────────────
    if not eps_filter or "ep01" in eps_filter:
        m = _load("generate_ep01_v21_lineart")
        for sb in m.STORYBOARDS:
            tasks.append({
                "ep": "ep01", "seg": sb["id"], "slot": sb.get("slot", "?"),
                "prompt": sb["prompt"], "out": m.out_path(sb),
            })

    # ── EP02 + EP03 ───────────────────────────────────────
    eps23 = [e for e in ("ep02", "ep03") if not eps_filter or e in eps_filter]
    if eps23:
        m = _load("generate_ep0203_v21_lineart")
        for ep, d, num, title, span, p, err in m.collect(eps23):
            if not p:
                print(f"⚠️  {ep} 片段{num} 无提示词：{err}", file=sys.stderr)
                continue
            tasks.append({
                "ep": ep, "seg": num, "slot": p.get("slot", "?"),
                "prompt": p["prompt"], "out": OUTPUT_DIR / p["file"],
            })

    # ── EP04 + EP05 ───────────────────────────────────────
    eps45 = [e for e in ("ep04", "ep05") if not eps_filter or e in eps_filter]
    if eps45:
        m = _load("generate_ep_v21_lineart")
        for ep, d, num, title, span, p, err in m.collect(eps45):
            if not p:
                print(f"⚠️  {ep} 片段{num} 无提示词：{err}", file=sys.stderr)
                continue
            tasks.append({
                "ep": ep, "seg": num, "slot": p.get("slot", "?"),
                "prompt": p["prompt"], "out": OUTPUT_DIR / p["file"],
            })
    return tasks


def one(task, force=False, retries=6):
    out = Path(task["out"])
    if out.exists() and not force:
        return {**task, "status": "skip", "size_kb": out.stat().st_size // 1024}
    last = ""
    for attempt in range(retries):
        try:
            t0 = time.time()
            dest, info = rh_app_img.generate(task["prompt"], out, webapp=WEBAPP)
            return {**task, "status": "ok", "size_kb": dest.stat().st_size // 1024,
                    "secs": round(time.time() - t0, 1), "taskId": info.get("taskId")}
        except Exception as e:
            last = str(e)
            # 队列占满 → 退避后重试，不算失败
            if "TASK_QUEUE_MAXED" in last or "421" in last:
                time.sleep(15 * (attempt + 1))
                continue
            break
    return {**task, "status": "fail", "err": last[:240]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eps", nargs="*", default=None, help="如 ep01 ep02")
    ap.add_argument("--only", nargs="*", default=None, help="只跑指定片段号")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--force", action="store_true")
    default_app = WEBAPP
    ap.add_argument("--webapp", default=default_app, help=f"AI 应用 id，默认低价版 {APP_LOW}")
    ap.add_argument("--dry-run", action="store_true", help="打印提示词，不调接口")
    args = ap.parse_args()

    globals()["WEBAPP"] = args.webapp

    tasks = build_tasks(args.eps)
    if args.only:
        tasks = [t for t in tasks if t["seg"] in args.only]
    print(f"任务总数：{len(tasks)}")
    if args.list or args.dry_run:
        for t in tasks:
            mark = "✅已有" if Path(t["out"]).exists() else "⬜待生成"
            print(f"  {mark} [{t['ep']} 片段{t['seg']}] @图片{t['slot']} → {Path(t['out']).name} ({len(t['prompt'])}字)")
            if args.dry_run:
                print("-" * 60)
                print(t["prompt"])
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = LOG_DIR / f"step5_lineart_rh_{stamp}.log"
    lines = [f"《红绳》Step 5 校对线稿 — RunningHub AI 应用通道 {stamp}",
             f"应用: {WEBAPP}  任务: {len(tasks)}", "=" * 60]
    print("\n".join(lines))

    results = []
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futs = {pool.submit(one, t, args.force): t for t in tasks}
        for i, fut in enumerate(as_completed(futs), 1):
            r = fut.result()
            results.append(r)
            tag = {"ok": "✅", "skip": "⏭", "fail": "❌"}[r["status"]]
            detail = f"{r.get('size_kb')}KB {r.get('secs','')}s" if r["status"] != "fail" else f"ERR {r.get('err')}"
            line = f"[{i}/{len(tasks)}] {tag} {r['ep']}片段{r['seg']} {Path(r['out']).name} | {detail}"
            print(line, flush=True)
            lines.append(line)

    ok = [r for r in results if r["status"] == "ok"]
    fail = [r for r in results if r["status"] == "fail"]
    sk = [r for r in results if r["status"] == "skip"]
    lines += ["", "=" * 60, f"✅ 新增 {len(ok)} | ⏭ 跳过 {len(sk)} | ❌ 失败 {len(fail)}"]
    for r in fail:
        lines.append(f"  ❌ {r['ep']}片段{r['seg']}: {r.get('err')}")
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[-6:]))
    print(f"日志: {log}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
