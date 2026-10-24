#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第 8 轮（2026-09-23）：把三个生成器 --dry-run 的原始输出，组装成
人类可审校的《Step 5 校对线稿提示词全集》Markdown。

只做文本组装：不调接口、不生图、不改动任何 Step 4 交付物。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "05-workflow" / "output"
STAMP = sys.argv[1] if len(sys.argv) > 1 else "20260923_223832"

SOURCES = [
    ("EP01", OUT / f"step5_r8_prompts_ep01_{STAMP}.txt"),
    ("EP02–EP03", OUT / f"step5_r8_prompts_ep0203_{STAMP}.txt"),
    ("EP04–EP05", OUT / f"step5_r8_prompts_ep0405_{STAMP}.txt"),
]

SEP = re.compile(r"^={20,}\s*$")
HEAD = re.compile(r"^\[(?P<tag>[^\]]+)\]\s*→\s*(?P<file>.+?)\s*$")


def parse(path: Path):
    """返回 [(tag, target_file, [prompt_lines]), ...]"""
    blocks = []
    cur = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.rstrip("\r")
        if SEP.match(line):
            if cur:
                blocks.append(cur)
            cur = None
            continue
        m = HEAD.match(line.strip())
        if m:
            if cur:
                blocks.append(cur)
            cur = [m.group("tag"), m.group("file"), []]
            continue
        if cur is not None:
            cur[2].append(line)
    if cur:
        blocks.append(cur)
    # 去掉尾部空白行
    out = []
    for tag, f, lines in blocks:
        while lines and not lines[-1].strip():
            lines.pop()
        out.append((tag, f, lines))
    return out


def layout_of(lines):
    for ln in lines:
        if ln.startswith("六格节拍"):
            return "2×3 六宫格"
        if ln.startswith("九格节拍"):
            return "3×3 九宫格"
    joined = "\n".join(lines)
    if "九宫格" in joined:
        return "九宫格"
    if "六宫格" in joined:
        return "六宫格"
    return "—"


def counts(lines):
    cells = 0
    for ln in lines:
        if re.match(r"^\d+\.\s", ln.strip()):
            cells += 1
    cells_txt = ""
    for ln in lines:
        if "格节拍" in ln:
            m = re.search(r"格1↔(?:镜头|SHOT)\s*1", ln)
            if m:
                break
    return cells


groups = []
for label, path in SOURCES:
    if not path.exists():
        print(f"!! 缺少原始日志：{path}")
        continue
    groups.append((label, path, parse(path)))

total = sum(len(b) for _, _, b in groups)

md = []
md.append("# 《红绳》Step 5 校对线稿提示词全集（第 8 轮 / 2026-09-23）\n")
md.append("> **生成方式**：三个生成器 `--dry-run` 真实运行输出（退出码均为 0），由 "
          "`05-images/scripts/build_r8_prompt_dump.py` 组装；**未调用生图接口、未生成任何图片**。")
md.append("> **核心原则**：线稿是对 Step 4 视频提示词的视觉校对——本文件即校对对象本身，"
          "可在无图片的情况下先行人工审校。")
md.append(f"> **条目数**：{total}（EP01 6 + EP02 14 + EP03 16 + EP04 16 + EP05 16 = 68）\n")
md.append("---\n")
md.append("## 一、条目总表\n")
md.append("| # | 集 | 片段标签 | 版式 | 节拍格数 | 目标文件 |")
md.append("|---|---|---|---|---|---|")
idx = 0
for label, _, blocks in groups:
    for tag, f, lines in blocks:
        idx += 1
        md.append(f"| {idx} | {label} | {tag} | {layout_of(lines)} | {counts(lines)} | `{f}` |")
md.append("")

md.append("---\n")
md.append("## 二、逐条提示词全文\n")
md.append("> 每条提示词均可直接投喂生图接口；格式已固定为“16:9 横版 / 黑白灰线稿 + 彩色制作标注”。\n")
n = 0
for label, _, blocks in groups:
    md.append(f"### {label}\n")
    for tag, f, lines in blocks:
        n += 1
        md.append(f"#### {n}. {tag} → `{f}`\n")
        md.append(f"```text\n" + "\n".join(lines).strip() + "\n```\n")

target = OUT / f"Step5_全部校对线稿提示词_第8轮_{STAMP[:8]}.md"
target.write_text("\n".join(md), encoding="utf-8")
print(f"✅ 写入 {target}")
print(f"   条目 {n} 条 / 字数 {len(''.join(md))}")
