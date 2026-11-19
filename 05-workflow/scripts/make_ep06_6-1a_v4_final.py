# -*- coding: utf-8 -*-
"""EP06 6-1a v4 归档版后期（G04：提示词层保不住的属性降级到后期层）。

不烧币、不提交任何生成任务。处理三件事：
  1) 逐帧去红：末段车尾被模型补出的红色尾灯，按冷蓝灰定稿压成冷灰
     （只命中高红像素，黄黑柱脚警示条不受影响）。
  2) 音轨手机兼容：AAC 32000Hz → AAC 48000Hz 192k，+6dB 外放增益
     （原片 RMS -35.8dB / max -9.2dB，手机外放易听不见，P16 事故预防）。
  3) faststart + H.264 CRF18 重封，归档位与手机版各一份。

原始生成片保留在 `视频草稿/EP06_6-1a_金鱼_v4.mp4` 不覆盖，留作对照。
v3 归档片按「用户判不合格时旧归档移草稿位」移到视频草稿。

用法：python make_ep06_6-1a_v4_final.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
SEG = ROOT / "05-workflow" / "ep06" / "6-1a_跳车掀车"
ARCHIVE = ROOT / "05-workflow" / "ep06" / "视频归档"
SRC = SEG / "视频草稿" / "EP06_6-1a_金鱼_v4.mp4"
DST = ARCHIVE / "EP06_6-1a_跳车掀车_金鱼_v4.mp4"
PHONE = SEG / "视频草稿" / "EP06_6-1a_金鱼_v4_手机版.mp4"
V3 = ARCHIVE / "EP06_6-1a_跳车掀车_金鱼_v3.mp4"
V3_DRAFT = SEG / "视频草稿" / "EP06_6-1a_金鱼_v3_已迭代_控制不住.mp4"


def red_count(bgr: np.ndarray) -> int:
    b, g, r = cv2.split(bgr)
    return int(((r > g * 1.22) & (r > b * 1.30) & (r > 70)).sum())


def dered(bgr: np.ndarray) -> np.ndarray:
    b, g, r = cv2.split(bgr)
    mask = (r > g * 1.22) & (r > b * 1.30) & (r > 70)
    if not mask.any():
        return bgr
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1].astype(np.float32)
    sat[mask] *= 0.12
    hsv[:, :, 1] = np.clip(sat, 0, 255).astype(np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def main() -> int:
    if not SRC.exists():
        raise SystemExit(f"缺少原始成片：{SRC}")
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(SRC))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"input : {SRC.name} {w}x{h} {fps:.2f}fps {n} frames", flush=True)

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
        "-r", str(fps), "-i", "-",
        "-i", str(SRC),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-af", "volume=6dB", "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
        "-movflags", "+faststart", "-shortest", str(DST),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    assert proc.stdin is not None
    total_red_before = 0
    total_red_after = 0
    affected = 0
    i = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        before = red_count(fr)
        total_red_before += before
        if before:
            affected += 1
        out = dered(fr)
        total_red_after += red_count(out)
        proc.stdin.write(out.tobytes())
        i += 1
        if i % 100 == 0:
            print(f"  {i}/{n} frames", flush=True)
    cap.release()
    proc.stdin.close()
    err = proc.stderr.read().decode("utf-8", "replace") if proc.stderr else ""
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg failed ({rc}): {err[:800]}")
    print(f"frames written: {i} | red pixels {total_red_before} -> {total_red_after} "
          f"| affected frames {affected}", flush=True)

    shutil.copy2(DST, PHONE)
    print(f"archive: {DST}", flush=True)
    print(f"phone  : {PHONE}", flush=True)

    if V3.exists() and not V3_DRAFT.exists():
        shutil.move(str(V3), str(V3_DRAFT))
        print(f"v3 moved out of archive -> {V3_DRAFT}", flush=True)
    elif V3.exists():
        print(f"v3 draft already exists, archive copy left in place: {V3}", flush=True)

    meta = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(DST)],
        capture_output=True,
    ).stdout or b"{}")
    streams = meta.get("streams") or []
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    a = next((s for s in streams if s.get("codec_type") == "audio"), {})
    print(f"verify : {v.get('codec_name')} {v.get('width')}x{v.get('height')} "
          f"{v.get('r_frame_rate')}fps {meta.get('format',{}).get('duration')}s | "
          f"{a.get('codec_name')} {a.get('sample_rate')}Hz {a.get('channels')}ch", flush=True)

    vol = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(DST), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True,
    ).stderr.decode("utf-8", "replace")
    for line in vol.splitlines():
        if "mean_volume" in line or "max_volume" in line:
            print("  " + line.strip(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
