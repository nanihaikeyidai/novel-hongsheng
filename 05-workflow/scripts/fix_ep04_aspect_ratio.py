#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正 EP04 视频提示词的画幅声明，使其符合 AGENTS.md〈成片画幅规范（强制）〉。

规则原文：**最终视频统一 16:9 横屏**：提示词【画面质感】写 `16:9横屏，2K级高清`。

实测违规范围（2026-09-17）：
- `05-workflow/ep04/红绳片段01~16/视频提示词.md` 共 16 处【画面质感】写 `9:16竖屏`
- `05-workflow/ep04/制作文档/视频提示词清单.md` 内 16 处同文件正文副本

替换规则（仅作用于【画面质感】行，逐行、幂等、保留原换行与编码）：
    `9:16竖屏，2K级高清`  →  `16:9横屏，2K级高清`

用法：
    python fix_ep04_aspect_ratio.py --dry-run   # 只报告
    python fix_ep04_aspect_ratio.py             # 实际写入
"""
import argparse
import re
from datetime import datetime
from pathlib import Path

PROJECT = Path(r"D:/HermesWorkspace/ai小说/红绳")
EP04 = PROJECT / "05-workflow" / "ep04"
LOG_DIR = PROJECT / "05-workflow" / "output"

BAD = "9:16竖屏"
GOOD = "16:9横屏"


def targets():
    files = sorted(EP04.glob("红绳片段*/视频提示词.md"))
    extra = EP04 / "制作文档" / "视频提示词清单.md"
    if extra.exists():
        files.append(extra)
    return files


def fix_text(text: str):
    """返回 (新文本, 改动条数)；只改【画面质感】所在行。"""
    lines = text.split("\n")
    n = 0
    for i, ln in enumerate(lines):
        if "【画面质感】" in ln and BAD in ln:
            lines[i] = ln.replace(BAD, GOOD)
            n += 1
    return "\n".join(lines), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    report = [f"EP04 画幅声明修正  {'(dry-run)' if args.dry_run else '(写入)'}  "
              f"{datetime.now():%Y-%m-%d %H:%M:%S}", "=" * 66]

    total_files = total_hits = 0
    for p in targets():
        raw = p.read_bytes()
        text = raw.decode("utf-8")
        new, n = fix_text(text)
        rel = p.relative_to(PROJECT).as_posix()
        if n:
            total_files += 1
            total_hits += n
            report.append(f"  ✏ {rel}  改动 {n} 处")
            if not args.dry_run:
                p.write_bytes(new.encode("utf-8"))
        else:
            report.append(f"  ✓ {rel}  无需改动")

    report += [
        "=" * 66,
        f"文件: {total_files}  行: {total_hits}",
        f"规则: 【画面质感】行内 `{BAD}` → `{GOOD}`",
    ]
    out = "\n".join(report)
    print(out)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    (LOG_DIR / f"fix_ep04_aspect_{stamp}.log").write_text(out + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
