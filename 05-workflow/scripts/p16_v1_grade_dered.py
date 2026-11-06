# -*- coding: utf-8 -*-
"""P16 v1 后期调色：压掉过量的红色警报污染（只作用于红色相区），保留冷荧光主光。

不重新生成、不消耗币。输出 *_去红光.mp4，音轨原样复制。
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

SEG = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep05\营救陆沉\红绳片段16")
SRC = SEG / "视频草稿" / "片段16_P16_金鱼草稿_v1.mp4"
TMP = SEG / "验收" / "_grade_tmp"
OUT = SEG / "视频草稿" / "片段16_P16_金鱼草稿_v1_去红光.mp4"

RED_S_KEEP = 0.46      # 红色相区饱和度保留比例
RED_V_KEEP = 0.96
GLOBAL_S = 0.92
COOL_R = 0.965
COOL_B = 1.02


def grade_frame(bgr: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    red = ((h <= 13) | (h >= 166)) & (s >= 50)
    s[red] *= RED_S_KEEP
    v[red] *= RED_V_KEEP
    s *= GLOBAL_S
    out = cv2.cvtColor(
        np.clip(cv2.merge([h, s, v]), 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR
    ).astype(np.float32)
    out[..., 2] *= COOL_R   # R
    out[..., 0] *= COOL_B   # B
    return np.clip(out, 0, 255).astype(np.uint8)


def main() -> int:
    if not (TMP.exists() and any(TMP.glob("*.jpg"))):
        if TMP.exists():
            shutil.rmtree(TMP)
        TMP.mkdir(parents=True, exist_ok=True)
        cap = cv2.VideoCapture(str(SRC))
        i = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            cv2.imencode(".jpg", grade_frame(frame),
                         [int(cv2.IMWRITE_JPEG_QUALITY), 96])[1].tofile(
                str(TMP / f"{i:05d}.jpg"))
            i += 1
        cap.release()
        print(f"已处理 {i} 帧", flush=True)

    n = len(list(TMP.glob("*.jpg")))
    print(f"帧序列 {n} 张", flush=True)

    cmd = [
        "ffmpeg", "-v", "error", "-y",
        "-framerate", "24", "-i", "%05d.jpg",
        "-i", str(SRC),
        "-map", "0:v:0", "-map", "1:a?",
        "-c:v", "libx264", "-crf", "17", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest",
        str(OUT),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(TMP))
    if r.returncode != 0:
        print(r.stderr[-1500:], file=sys.stderr)
        return 1
    print("saved", OUT, round(OUT.stat().st_size / 1024 / 1024, 1), "MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
