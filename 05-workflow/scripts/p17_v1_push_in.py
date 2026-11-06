# -*- coding: utf-8 -*-
"""P17 v1 不烧币补救：蓝隼镜头（6.0–9.0s）做缓慢推近，提升压迫/邪气。其余帧原样。"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

SEG = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep05\营救陆沉\红绳片段17")
SRC = SEG / "视频草稿" / "片段17_P17_金鱼草稿_v1.mp4"
TMP = SEG / "验收" / "_push_tmp"
OUT = SEG / "视频草稿" / "片段17_P17_金鱼草稿_v1_蓝隼压迫增强.mp4"

FPS = 24
PUSH_START = int(6.0 * FPS)
PUSH_END = int(9.0 * FPS)
ZOOM_TO = 1.12
CX, CY = 0.50, 0.46          # 推近中心（蓝隼脸部）


def push(frame: np.ndarray, t: float) -> np.ndarray:
    h, w = frame.shape[:2]
    zoom = 1.0 + (ZOOM_TO - 1.0) * t
    cw, ch = int(w / zoom), int(h / zoom)
    cx, cy = int(w * CX), int(h * CY)
    x0 = max(0, min(w - cw, cx - cw // 2))
    y0 = max(0, min(h - ch, cy - ch // 2))
    return cv2.resize(frame[y0:y0 + ch, x0:x0 + cw], (w, h), interpolation=cv2.INTER_LANCZOS4)


def main() -> int:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(SRC))
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if PUSH_START <= i <= PUSH_END:
            t = (i - PUSH_START) / max(1, (PUSH_END - PUSH_START))
            t = t * t * (3 - 2 * t)          # smoothstep
            frame = push(frame, t)
        cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 96])[1].tofile(
            str(TMP / f"{i:05d}.jpg"))
        i += 1
    cap.release()
    print(f"处理 {i} 帧（推近 {PUSH_START}-{PUSH_END}）", flush=True)

    cmd = [
        "ffmpeg", "-v", "error", "-y",
        "-framerate", str(FPS), "-i", "%05d.jpg",
        "-i", str(SRC),
        "-map", "0:v:0", "-map", "1:a?",
        "-c:v", "libx264", "-crf", "17", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest",
        str(OUT),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(TMP))
    if r.returncode != 0:
        print(r.stderr[-1200:], file=sys.stderr)
        return 1
    print("saved", OUT, round(OUT.stat().st_size / 1024 / 1024, 1), "MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
