#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 候选声学对比.json 画成一张横向对比图（只需 Pillow）。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--baseline-hz", type=float, default=113.0)
    args = ap.parse_args()

    rows = json.loads(Path(args.data).read_text(encoding="utf-8"))
    rows = [r for r in rows if "error" not in r]
    W, H = 1180, 90 + len(rows) * 56 + 70
    im = Image.new("RGB", (W, H), "#1b2028")
    d = ImageDraw.Draw(im)
    f_title, f_row, f_small = font(24), font(17), font(14)

    d.text((28, 20), "P09「晚安」重配音 · 候选声学对比（原片基线 113 Hz）", font=f_title, fill="#e8eef7")
    d.text((28, 54), "F0 越低 = 越低沉    |    气声比越高 = 气流越多    |    音色相关越接近 1.000 = 越贴原片音色", font=f_small, fill="#8fa3bd")

    x0, x1 = 300, 830
    scale = (x1 - x0) / 240.0  # 0–240 Hz

    def hz_x(v: float) -> int:
        return int(x0 + max(0.0, min(240.0, v)) * scale)

    # 基线
    bx = hz_x(args.baseline_hz)
    d.line([(bx, 78), (bx, H - 55)], fill="#e05a5a", width=2)
    d.text((bx + 6, 80), f"原片 {args.baseline_hz:.0f}Hz", font=f_small, fill="#e07b7b")

    colors = {
        "A": "#e08a5a", "E": "#e08a5a",  # text 情绪（音高被抬高）
        "B": "#5aa9e0", "F": "#5aa9e0",  # vector
        "C": "#8f7ad6", "H": "#62c9a0",  # 原片音色
        "D": "#8894a6", "G": "#c9b45a",  # baseline / reference_audio
        "W": "#4fc3c9",  # 气声后期层
    }
    for i, r in enumerate(rows):
        y = 100 + i * 56
        name = r["file"].replace(".wav", "")
        f0 = r["f0_median_hz"] or 0
        c = colors.get(name[0], "#8894a6")
        d.text((28, y + 6), name, font=f_row, fill="#e8eef7")
        d.rounded_rectangle((x0, y + 8, x1, y + 30), radius=6, fill="#2a323e")
        d.rounded_rectangle((x0, y + 8, hz_x(f0), y + 30), radius=6, fill=c)
        d.text((hz_x(f0) + 8, y + 9), f"{f0:.0f} Hz", font=f_small, fill=c)
        d.text((x1 + 22, y + 9),
               f"气声 {r.get('hf_ratio_db', 0):.0f}dB · 音色 {r['timbre_corr_vs_ref']:.3f} · {r['voiced_s']:.2f}s",
               font=f_small, fill="#9fb2c9")

    d.line([(28, H - 52), (W - 28, H - 52)], fill="#3a4553", width=1)
    d.text((28, H - 40),
           "第三轮主推 W_L_whisper：F0 114Hz（≈原片）· 气声比 -9.7dB（原片 -26.8dB）· 电平 -5.5dB · 0.74s 慢吐",
           font=f_small, fill="#4fc3c9")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    print("saved", out, im.size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
