# -*- coding: utf-8 -*-
"""EP06 6-1a 云端金鱼 v1 成片验收：抽帧拼图 + 规格 + 音轨 + ASR 人声检查。

不烧币、不提交任何生成任务。
用法：python check_ep06_6-1a_jinyu_v1.py [video_path]
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
SEG = ROOT / "05-workflow" / "ep06" / "6-1a_跳车掀车"
VIDEO = Path(sys.argv[1]) if len(sys.argv) > 1 else SEG / "视频草稿" / "EP06_6-1a_金鱼_v1.mp4"
WORK = Path(r"C:\Users\Administrator\WorkBuddy\2026-10-23-12-30-36\_p04a_work\ep06")
WORK.mkdir(parents=True, exist_ok=True)


def run(args: list[str]) -> bytes:
    return subprocess.run(args, capture_output=True).stdout


def main() -> int:
    if not VIDEO.exists():
        print(f"NOT FOUND: {VIDEO}")
        return 1

    meta = json.loads(run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(VIDEO),
    ]) or b"{}")
    streams = meta.get("streams") or []
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    a = next((s for s in streams if s.get("codec_type") == "audio"), {})
    dur = float(meta.get("format", {}).get("duration") or 0)
    print(f"file   : {VIDEO.name}  {VIDEO.stat().st_size // 1024} KB")
    print(f"video  : {v.get('codec_name')} {v.get('width')}x{v.get('height')} "
          f"{v.get('r_frame_rate')} fps, {dur:.2f}s")
    print(f"audio  : {a.get('codec_name')} {a.get('sample_rate')}Hz "
          f"{a.get('channels')}ch" if a else "audio  : ❌ NO AUDIO STREAM")

    # 抽 8 帧（0.5s 起，覆盖 5 镜）
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw

    cap = cv2.VideoCapture(str(VIDEO))
    times = [0.5, 2.5, 4.5, 6.0, 8.0, 10.5, 13.0, 14.5]
    frames = []
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        if ok:
            frames.append((t, Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))))
    cap.release()
    print(f"frames : sampled {len(frames)} / {len(times)}")

    if frames:
        TW, TH = 400, 225
        cols = 2
        rows = (len(frames) + cols - 1) // cols
        sheet = Image.new("RGB", (TW * cols, (TH + 24) * rows), "white")
        d = ImageDraw.Draw(sheet)
        for i, (t, im) in enumerate(frames):
            im = im.resize((TW, TH))
            x, y = (i % cols) * TW, (i // cols) * (TH + 24)
            sheet.paste(im, (x, y))
            d.text((x + 6, y + TH + 4), f"t={t:.1f}s", fill="black")
        out = WORK / "jinyu_v1_sheet.jpg"
        sheet.save(out, quality=90)
        print(f"sheet  : {out}")

    # 音轨能量 + 人声频段
    if a:
        raw = run(["ffmpeg", "-v", "quiet", "-i", str(VIDEO),
                   "-ac", "1", "-ar", "16000", "-f", "s16le", "-"])
        if raw:
            x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            rms = 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
            print(f"audio RMS: {rms:.1f} dB")
        vol = subprocess.run(
            ["ffmpeg", "-v", "info", "-i", str(VIDEO), "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True,
        ).stderr.decode("utf-8", "replace")
        for line in vol.splitlines():
            if "mean_volume" in line or "max_volume" in line:
                print("  " + line.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
