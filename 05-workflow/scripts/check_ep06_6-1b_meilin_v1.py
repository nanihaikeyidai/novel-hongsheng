# -*- coding: utf-8 -*-
"""EP06 6-1b 拦车甩车 梅林 v1 必要验收：规格 + 分段拼图 + 音轨 / ASR 体检。

不提交生成任务；按 2026-11-15 口径不落盘复盘/开发说明，结论只在对话里给。

用户原话反推（G15）：
  1) 蓝隼单手把车拦停 → 0-2.5s 是否只有一只手接触车头、车停住？
  2) 手向右一甩把车甩出去 → 2.5-7s 车是否被甩向画面右侧并离地？
  3) 撞到旁边柱子 → 7-9.5s 车是否撞上画面右侧水泥柱、柱体崩裂？
  4) 安娜镜头战斗姿势 → 11.5-15s 是否安娜起身摆架势、指间有短刃？
  5) 蓝隼不摘墨镜、冷蓝灰、0 台词。

用法：python check_ep06_6-1b_meilin_v1.py [video_path]
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
SEG = ROOT / "05-workflow" / "ep06" / "6-1b_拦车甩车"
VIDEO = Path(sys.argv[1]) if len(sys.argv) > 1 else SEG / "视频草稿" / "EP06_6-1b_梅林_v1.mp4"
WORK = Path(r"C:\Users\Administrator\WorkBuddy\2026-10-23-12-30-36\_p04a_work\ep06")
WORK.mkdir(parents=True, exist_ok=True)


def run(args: list[str]) -> bytes:
    return subprocess.run(args, capture_output=True).stdout


def sheet(cap, times, name, cols=3, tw=420, th=236):
    import cv2
    from PIL import Image, ImageDraw
    frames = []
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        if ok:
            frames.append((t, Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))))
    if not frames:
        return None
    rows = (len(frames) + cols - 1) // cols
    out = Image.new("RGB", (tw * cols, (th + 24) * rows), "white")
    d = ImageDraw.Draw(out)
    for i, (t, im) in enumerate(frames):
        x, y = (i % cols) * tw, (i // cols) * (th + 24)
        out.paste(im.resize((tw, th)), (x, y))
        d.text((x + 6, y + th + 4), f"t={t:.1f}s", fill="black")
    dest = WORK / name
    out.save(dest, quality=90)
    print(f"sheet  : {dest}  ({len(frames)} frames)")
    return dest


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
          f"{a.get('channels')}ch" if a else "audio  : NO AUDIO STREAM")

    import cv2
    import numpy as np
    cap = cv2.VideoCapture(str(VIDEO))

    sheet(cap, [0.5, 1.5, 2.2, 3.0, 4.2, 5.2, 6.2, 7.2, 8.2, 9.2,
                10.2, 11.2, 12.2, 13.2, 14.2, 14.9],
          "ep06_6-1b_sheet.jpg", cols=4, tw=400, th=225)

    # A 拦停（判据 1）
    sheet(cap, [0.2, 0.8, 1.4, 2.0, 2.4], "ep06_6-1b_block_sheet.jpg")
    # B 向右甩车（判据 2）
    sheet(cap, [2.6, 3.2, 3.8, 4.6, 5.4, 6.2, 6.8], "ep06_6-1b_swing_sheet.jpg")
    # C 撞柱（判据 3）
    sheet(cap, [7.0, 7.6, 8.2, 8.8, 9.4], "ep06_6-1b_impact_sheet.jpg")
    # D 蓝隼收势 + 安娜战斗姿势（判据 4/5）
    sheet(cap, [9.6, 10.4, 11.2, 11.8, 12.4, 13.2, 14.0, 14.7],
          "ep06_6-1b_anna_sheet.jpg", cols=4, tw=400, th=225)
    cap.release()

    if a:
        raw = run(["ffmpeg", "-v", "quiet", "-i", str(VIDEO),
                   "-ac", "1", "-ar", "16000", "-f", "s16le", "-"])
        if raw:
            x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            print(f"audio RMS: {20*np.log10(np.sqrt((x**2).mean())+1e-9):.1f} dB")
        vol = subprocess.run(
            ["ffmpeg", "-v", "info", "-i", str(VIDEO), "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True,
        ).stderr.decode("utf-8", "replace")
        for line in vol.splitlines():
            if "mean_volume" in line or "max_volume" in line:
                print("  " + line.strip())

    try:
        from faster_whisper import WhisperModel
        cache = (Path.home() / ".cache" / "huggingface" / "hub" /
                 "models--Systran--faster-whisper-small" / "snapshots")
        snaps = sorted(x for x in cache.iterdir() if x.is_dir()) if cache.exists() else []
        src = str(snaps[-1]) if snaps else "small"
        model = WhisperModel(src, device="cpu", compute_type="int8")
        segs, _ = model.transcribe(str(VIDEO), beam_size=5)
        found = [(round(s.start, 1), round(s.end, 1), round(s.no_speech_prob, 2),
                  round(s.avg_logprob, 2), s.text.strip())
                 for s in segs if s.text.strip()]
        print(f"ASR segments = {len(found)}")
        for f in found:
            print("   ", f)
    except Exception as exc:  # noqa: BLE001
        print(f"ASR skipped: {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
