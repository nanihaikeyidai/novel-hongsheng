# -*- coding: utf-8 -*-
"""P16 地下车库场景图后期：去右下角 AI 水印 + 微调色（压暗降饱和，贴近深蓝近黑车漆）。"""
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
SEG = ROOT / "05-workflow" / "ep05" / "营救陆沉" / "红绳片段16"
SRC = SEG / "验收" / "Japanese_anime_cel_shaded_movi_2026-11-05T14-44-43.png"
OUT_DIR = ROOT / "05-images" / "场景"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def remove_watermark(bgr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    h, w, _ = bgr.shape
    # 水印实测 bbox ≈ (1428,805)-(1526,858)，外扩 10px
    x0, y0, x1, y1 = 1416, 792, w, h
    mask = np.zeros((h, w), np.uint8)
    mask[y0:y1, x0:x1] = 255
    out = cv2.inpaint(bgr, mask, 9, cv2.INPAINT_TELEA)
    # inpaint 后暗部会被抹平，用邻近地面的颗粒噪声补一点纹理
    rng = np.random.default_rng(7)
    patch = out[y0:y1, x0:x1].astype(np.float32)
    noise = rng.normal(0, 3.2, (patch.shape[0], patch.shape[1], 1)).astype(np.float32)
    out[y0:y1, x0:x1] = np.clip(patch + noise, 0, 255).astype(np.uint8)
    return out, mask


def grade(bgr: np.ndarray) -> np.ndarray:
    f = bgr.astype(np.float32) / 255.0
    # 压暗 + 提一点对比（低照度地下空间）
    f = np.power(f, 1.10)
    f = np.clip((f - 0.5) * 1.06 + 0.5, 0, 1)
    # 降饱和（车漆过亮偏紫 → 深蓝近黑）
    hsv = cv2.cvtColor((f * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] *= 0.88
    hsv[..., 2] *= 1.03
    out = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR)
    # 冷色调微偏（暗部加青蓝，高光不动）
    b, g, r = cv2.split(out.astype(np.float32))
    lum = out.mean(axis=2) / 255.0
    wgt = (1.0 - lum) * 0.10
    b = np.clip(b * (1 + wgt), 0, 255)
    g = np.clip(g * (1 + wgt * 0.5), 0, 255)
    r = np.clip(r * (1 - wgt * 0.7), 0, 255)
    return cv2.merge([b, g, r]).astype(np.uint8)


def main() -> None:
    bgr = cv2.imdecode(np.fromfile(str(SRC), dtype=np.uint8), cv2.IMREAD_COLOR)
    print("src", bgr.shape)
    clean, _ = remove_watermark(bgr)
    cv2.imencode(".png", clean)[1].tofile(str(SEG / "验收" / "_车库v3_去水印.png"))

    final = grade(clean)
    out = OUT_DIR / "场景_EP05_地下车库_日漫电影感_v3.png"
    cv2.imencode(".png", final)[1].tofile(str(out))
    print("saved", out, final.shape)

    # 上传包用 jpg（金鱼参考图）
    up = SEG / "上传包" / "image3_garage_anime_v3.jpg"
    cv2.imencode(".jpg", final, [int(cv2.IMWRITE_JPEG_QUALITY), 94])[1].tofile(str(up))
    print("saved", up)


if __name__ == "__main__":
    main()
