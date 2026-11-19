# -*- coding: utf-8 -*-
"""EP06 6-1a 镜头理解 6 宫格：裁 16:9 / 去工具水印 / 去红色尾灯 / 拼 2x3 加中文标签。

用法：python make_ep06_6-1a_storyboard_grid.py
输入：ep06/6-1a_跳车掀车/分镜确认_6宫格/ 下 ImageGen 产出的原始 png（按时间戳映射）
输出：01..06 单格 png（16:9 已清理） + EP06_6-1a_镜头理解_6宫格.png
"""
from __future__ import annotations

import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
DIR = ROOT / "05-workflow" / "ep06" / "6-1a_跳车掀车" / "分镜确认_6宫格"
PREFIX = "16_9_宽银幕电影分镜_高精度日漫青春电影感_细腻赛璐璐人_"

# 最终采用的 6 格（按时间顺序）；另两张废稿移到 _废稿/ 留对照
SHOTS = [
    ("01_挡风玻璃车内POV.png", PREFIX + "2026-11-13T23-48-10.png",
     "挡风玻璃车内 POV", "蓝隼正面对车 · 背景静止"),
    ("02_安娜主驾开门准备.png", PREFIX + "2026-11-13T23-49-19.png",
     "安娜（主驾·左）推门", "只开门准备 · 人仍在座"),
    ("03_陆沉副驾开门准备.png", PREFIX + "2026-11-13T23-51-56.png",
     "陆沉（副驾·右）推门", "双门同开 · 无跳车动作"),
    ("04_蓝隼邪恶笑容特写.png", PREFIX + "2026-11-13T23-50-09.png",
     "蓝隼脸部邪恶笑容特写", "完全正面 · 墨镜保留 · 无侧身"),
    ("05_切车迎面撞来.png", PREFIX + "2026-11-13T23-52-29.png",
     "切：车迎面撞过来", "车后高位固定机位 · 背景锁定"),
    ("06_撞击前一瞬.png",
     "以这张输入图为唯一基准做最小改动_保持同一张电影分镜的连续性_2026-11-13T23-53-28.png",
     "撞击前一瞬（同一机位）", "只有车变大 · 背景逐格同坐标"),
]
DRAFTS = [
    PREFIX + "2026-11-13T23-49-40.png",  # 镜像双联（两个陆沉）
    PREFIX + "2026-11-13T23-50-35.png",  # 尾灯带红
]

CELL_W, CELL_H = 720, 405      # 16:9 画面区
LABEL_H = 54
GAP, PAD = 12, 24
TITLE_H, FOOT_H = 90, 52
BG = (12, 20, 28)
LABEL_BG = (20, 31, 42)
ACCENT = (63, 132, 240)
TXT = (236, 242, 248)
SUB = (190, 206, 220)


def imread_u(path: Path) -> np.ndarray:
    """中文路径安全读取（cv2.imread 在 Windows 中文路径会返回 None）。"""
    return cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)


def imwrite_u(path: Path, img: np.ndarray) -> None:
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise RuntimeError(f"编码失败：{path}")
    buf.tofile(str(path))


def dered(bgr: np.ndarray) -> np.ndarray:
    """把红色尾灯压成冷灰（黄黑警示条不受影响）：G04 后期层处理。"""
    b, g, r = cv2.split(bgr)
    mask = ((r > g * 1.22) & (r > b * 1.30) & (r > 70))
    if not mask.any():
        return bgr
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1].astype(np.float32)
    sat[mask] *= 0.12
    hsv[:, :, 1] = np.clip(sat, 0, 255).astype(np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def clean_one(src: Path, dst: Path) -> Image.Image:
    img = imread_u(src)
    if img is None:
        raise RuntimeError(f"读取失败：{src}")
    h, w = img.shape[:2]
    # 3:2 -> 16:9 居中裁上下；工具右下角水印正好落在裁掉的区域里
    target_h = int(round(w * 9 / 16))
    top = (h - target_h) // 2
    img = img[top:top + target_h, :, :]
    img = dered(img)
    imwrite_u(dst, img)
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).resize(
        (CELL_W, CELL_H), Image.LANCZOS
    )


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for name in (("msyhbd.ttc" if bold else "msyh.ttc"), "simhei.ttf", "arial.ttf"):
        p = Path(r"C:\Windows\Fonts") / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def main() -> int:
    (DIR / "_废稿").mkdir(exist_ok=True)
    for name in DRAFTS:
        p = DIR / name
        if p.exists():
            shutil.move(str(p), str(DIR / "_废稿" / name))

    panels: list[Image.Image] = []
    for out_name, src_name, _, _ in SHOTS:
        src = DIR / src_name
        if not src.exists():
            raise RuntimeError(f"缺少源图：{src}")
        panels.append(clean_one(src, DIR / out_name))
        print(f"✓ {out_name}")

    W = PAD * 2 + CELL_W * 3 + GAP * 2
    H = TITLE_H + PAD + (CELL_H + LABEL_H) * 2 + GAP + FOOT_H + PAD
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    f_title = font(30, bold=True)
    f_sub = font(17)
    f_num = font(19, bold=True)
    f_lab = font(23, bold=True)
    f_labsub = font(16)

    d.text((PAD, 22), "EP06 · 6-1a｜镜头理解确认 · 6 宫格", font=f_title, fill=TXT)
    d.text((PAD, 60),
           "开门准备 → 蓝隼邪恶笑容特写 → 车迎面撞来 ｜ 背景锁死不动 ｜ 蓝隼始终正面对车 ｜ 仅出图，未生成视频",
           font=f_sub, fill=SUB)

    for i, (panel, (_, _, title, sub)) in enumerate(zip(panels, SHOTS)):
        row, col = divmod(i, 3)
        x = PAD + col * (CELL_W + GAP)
        y = TITLE_H + PAD + row * (CELL_H + LABEL_H + GAP)
        sheet.paste(panel, (x, y))
        d.rectangle([x, y + CELL_H, x + CELL_W, y + CELL_H + LABEL_H], fill=LABEL_BG)
        d.rounded_rectangle([x + 12, y + CELL_H + 11, x + 46, y + CELL_H + 43],
                            radius=6, fill=ACCENT)
        d.text((x + 21, y + CELL_H + 15), str(i + 1), font=f_num, fill=(255, 255, 255))
        d.text((x + 58, y + CELL_H + 5), title, font=f_lab, fill=TXT)
        d.text((x + 58, y + CELL_H + 31), sub, font=f_labsub, fill=SUB)

    d.text((PAD, H - FOOT_H - 8),
           "用户原话：不表达跳车／只开门准备／切蓝隼邪恶笑容特写／再切撞过来的车／旁边背景不用动／隼正面对着车不是侧面",
           font=f_sub, fill=SUB)

    out = DIR / "EP06_6-1a_镜头理解_6宫格.png"
    sheet.save(out)
    print(f"✓ 宫格 {out}  {sheet.size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
