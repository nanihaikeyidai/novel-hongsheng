# -*- coding: utf-8 -*-
"""EP06 6-1a 云端金鱼 v2 成片验收：规格 + 抽帧拼图 + 方向/动态专项 + 音轨。

不烧币、不提交任何生成任务。
用法：python check_ep06_6-1a_jinyu_v2.py [video_path]

v2 验收重点（用户 2026-11-13 四项要求）：
  1) 车头正对蓝隼、两者同框，间距逐帧缩短（DIRECTION LOCK）
  2) 跳车时车仍在加速、撞向蓝隼（SPEED LOCK）
  3) 蓝隼一拳把整车掀翻离地，不是压凹车头后侧倒
  4) 动态强、速度快（速度线 / 运动模糊 / 切镜短 / 镜头跟拍）
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
SEG = ROOT / "05-workflow" / "ep06" / "6-1a_跳车掀车"
VIDEO = Path(sys.argv[1]) if len(sys.argv) > 1 else SEG / "视频草稿" / "EP06_6-1a_金鱼_v2.mp4"
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

    import cv2
    import numpy as np
    from PIL import Image, ImageDraw

    cap = cv2.VideoCapture(str(VIDEO))

    # 8 帧总览拼图（对齐 v1，便于并排比对）
    times = [0.5, 2.5, 4.5, 6.0, 8.0, 10.5, 13.0, 14.5]
    frames = []
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        if ok:
            frames.append((t, Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))))
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
        out = WORK / "jinyu_v2_sheet.jpg"
        sheet.save(out, quality=90)
        print(f"sheet  : {out}")

    # 方向/动态专项：前 8 秒每 1 秒一帧，看车头与蓝隼的间距是否逐帧缩短
    axis_times = [0.3, 1.3, 2.3, 3.3, 4.3, 5.3, 6.3, 7.3, 8.3, 9.3, 10.3, 11.3]
    axis = []
    for t in axis_times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        if ok:
            axis.append((t, Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))))
    cap.release()
    if axis:
        AW, AH = 360, 200
        cols = 3
        rows = (len(axis) + cols - 1) // cols
        sheet2 = Image.new("RGB", (AW * cols, (AH + 22) * rows), "white")
        d2 = ImageDraw.Draw(sheet2)
        for i, (t, im) in enumerate(axis):
            im = im.resize((AW, AH))
            x, y = (i % cols) * AW, (i // cols) * (AH + 22)
            sheet2.paste(im, (x, y))
            d2.text((x + 6, y + AH + 3), f"t={t:.1f}s", fill="black")
        out2 = WORK / "jinyu_v2_direction_sheet.jpg"
        sheet2.save(out2, quality=90)
        print(f"direction sheet: {out2}  ({len(axis)} frames)")

    # 音轨逐秒能量 + 全局响度
    if a:
        raw = run(["ffmpeg", "-v", "quiet", "-i", str(VIDEO),
                   "-ac", "1", "-ar", "16000", "-f", "s16le", "-"])
        if raw:
            x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            rms = 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
            print(f"audio RMS: {rms:.1f} dB")
            for i in range(0, 15):
                seg = x[i * 16000:(i + 1) * 16000]
                if len(seg):
                    print(f"  {i:02d}-{i+1:02d}s  "
                          f"{20*np.log10(np.sqrt((seg**2).mean())+1e-9):6.1f} dB")
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
