#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""红绳 EP01 v2 生产包完整性核验（2026-08-12 cron）"""
import json, hashlib, re, sys, os
from pathlib import Path

ROOT = Path(r"D:/HermesWorkspace/ai小说/红绳")
ARCH = ROOT / "05-workflow/output/ep01/片段归档"
SB_DIR = ROOT / "05-images/storyboard"
SBV2_DIR = ROOT / "05-images/storyboard-v2"
VP_DIR = ROOT / "05-workflow/output/ep01"

issues = []
ok = []

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()

# ── 1. 归档目录 素材清单 ↔ 文件 一一对应 ──────────────────────
print("== 1. 素材清单校验 ==")
for i in range(1, 9):
    d = ARCH / f"红绳片段{i}"
    if not d.is_dir():
        issues.append(f"片段{i}: 归档目录缺失 {d}")
        continue
    manifest = d / "素材清单.md"
    if not manifest.exists():
        issues.append(f"片段{i}: 缺少 素材清单.md")
        continue
    txt = manifest.read_text(encoding="utf-8")
    # 收集清单中提到的 @图片N / @音频N
    refs = set()
    for m in re.finditer(r"@(图片|音频)(\d+)", txt):
        refs.add(f"@{m.group(1)}{m.group(2)}")
    actual = {p.name.split("_")[0] for p in d.iterdir() if p.is_file() and re.match(r"@(图片|音频)\d+", p.name)}
    missing_in_dir = refs - actual
    extra_in_dir = actual - refs
    if missing_in_dir:
        issues.append(f"片段{i}: 清单提到但目录缺失 → {sorted(missing_in_dir)}")
    if extra_in_dir:
        issues.append(f"片段{i}: 目录存在但清单未登记 → {sorted(extra_in_dir)}")
    if not missing_in_dir and not extra_in_dir:
        ok.append(f"片段{i}: 素材清单与目录 @图片N/@音频N 完全对应（{len(refs)}项）")

# ── 2. 视频提示词文件 & @图片N 映射可解析 ────────────────────
print("== 2. 视频提示词 ==")
for i in range(1, 9):
    f = VP_DIR / f"视频提示词_片段{i:02d}.md"
    if not f.exists():
        issues.append(f"视频提示词_片段{i:02d}.md 缺失")
    else:
        ok.append(f"视频提示词_片段{i:02d}.md 在位")

# ── 3. 线稿文件 ─────────────────────────────────────────────
print("== 3. 线稿文件 ==")
lineart_expected = {
    "04": "@图片5_片段04黑翼破窗.png",
    "05": "@图片6_片段05教室失控.png",
    "06": "@图片6_片段06猎物逼近.png",
    "07": "@图片5_片段07暗刃成形.png",
    "08": "@图片6_片段08红瞳护人.png",
}
for seg, fn in lineart_expected.items():
    p = SB_DIR / fn
    if not p.exists():
        issues.append(f"线稿缺失: {fn}")
    else:
        sz = p.stat().st_size
        ok.append(f"片段{seg}: {fn} 在位 ({sz/1024:.0f} KB)")

# ── 4. 分镜连续性总表 JSON 的 storyboard 路径+哈希 核对 ─────
print("== 4. 连续性总表 哈希核对 ==")
tbl = json.loads((ROOT / "05-workflow/output/ep01/分镜连续性总表.json").read_text(encoding="utf-8"))
for seg in tbl["segments"]:
    sid = seg["id"]
    sb = seg.get("storyboard", {})
    rel = sb.get("path", "")
    exp_hash = sb.get("sha256", "")
    p = ROOT / "05-workflow/output/ep01" / rel
    if not p.exists():
        issues.append(f"总表 片段{sid}: 故事板路径不存在 {rel}")
        continue
    actual = sha256(p)
    if actual == exp_hash:
        ok.append(f"片段{sid}: 哈希一致 [{seg['status']}] {rel}")
    else:
        issues.append(f"片段{sid}: 哈希不一致! 期望 {exp_hash[:16]}… 实际 {actual[:16]}… ({rel})")

print("\n== 结果汇总 ==")
print(f"✅ 通过: {len(ok)}")
for o in ok:
    print("  ", o)
print(f"\n❌ 问题: {len(issues)}")
for i in issues:
    print("  ", i)
sys.exit(1 if issues else 0)
