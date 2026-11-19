# -*- coding: utf-8 -*-
"""EP06 6-1a 云端金鱼 v3 成片验收：规格 + 四段专项拼图 + 8 帧总览 + 音轨。

不烧币、不提交任何生成任务。
用法：python check_ep06_6-1a_jinyu_v3.py [video_path]

v3 验收判据（从 David 2026-11-13 原话逐条反推，G15）：
  1) 「先是挡风玻璃里面视角」→ 首镜能否看到仪表盘/方向盘/车内两人，且透过玻璃看到前方蓝隼？
  2) 「然后左右两个方向跳出车，安娜在主驾」→ 是否一人左一人右分落两侧，主驾是灰帽白口罩的安娜？
  3) 「人和背景运动不一致」→ 人物翻滚/车速/柱与车道线后退速度是否同一运动系统，有无背景凝滞？
  4) 「参考武戏提示词模板」→ 切镜是否只改机位、动作是否有因果连续、节奏是否实时高速？
  5) 「蓝隼使用脚踢车」→ 是否是腿/靴接触车头，不是拳击？
  6) 「把车踢到一边，空中还旋转」→ 车是否横向飞出、四轮离地、空中整周旋转？
  7) 「车落地爆炸」→ 落地后是否有明显爆炸闪光/冲击环/黑烟？
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
SEG = ROOT / "05-workflow" / "ep06" / "6-1a_跳车掀车"
VIDEO = Path(sys.argv[1]) if len(sys.argv) > 1 else SEG / "视频草稿" / "EP06_6-1a_金鱼_v3.mp4"
WORK = Path(r"C:\Users\Administrator\WorkBuddy\2026-10-23-12-30-36\_p04a_work\ep06")
WORK.mkdir(parents=True, exist_ok=True)


def run(args: list[str]) -> bytes:
    return subprocess.run(args, capture_output=True).stdout


def sheet(cap, times, name, cols=4, tw=400, th=225):
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

    # 8 帧总览（与 v1/v2 同口径，便于并排比对）
    sheet(cap, [0.5, 2.5, 4.5, 6.0, 8.0, 10.5, 13.0, 14.5],
          "jinyu_v3_sheet.jpg", cols=2, tw=400, th=225)

    # 专项 A：首镜挡风玻璃车内 POV（判据 1）
    sheet(cap, [0.2, 0.8, 1.4, 2.0, 2.4, 3.0],
          "jinyu_v3_windshield_sheet.jpg", cols=3, tw=420, th=236)

    # 专项 B：左右跳车 + 人景运动一致性（判据 2/3/4）
    sheet(cap, [2.6, 3.2, 3.8, 4.4, 5.0, 5.6, 6.2, 6.8],
          "jinyu_v3_bailout_sheet.jpg", cols=4, tw=400, th=225)

    # 专项 C：脚踢 + 空中旋转（判据 5/6）
    sheet(cap, [7.5, 8.2, 8.8, 9.4, 10.0, 10.6, 11.2, 11.8],
          "jinyu_v3_kick_spin_sheet.jpg", cols=4, tw=400, th=225)

    # 专项 D：落地爆炸（判据 7）
    sheet(cap, [11.5, 12.2, 12.8, 13.4, 14.0, 14.6],
          "jinyu_v3_explosion_sheet.jpg", cols=3, tw=420, th=236)

    cap.release()

    # 音轨逐秒能量 + 全局响度（G13：由体检决定是否替换音轨）
    if a:
        raw = run(["ffmpeg", "-v", "quiet", "-i", str(VIDEO),
                   "-ac", "1", "-ar", "16000", "-f", "s16le", "-"])
        if raw:
            x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            print(f"audio RMS: {20*np.log10(np.sqrt((x**2).mean())+1e-9):.1f} dB")
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
