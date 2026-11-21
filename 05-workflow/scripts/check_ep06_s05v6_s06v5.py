# -*- coding: utf-8 -*-
"""EP06 S05 v6 / S06 v5 出片必要验收：规格 + 分段拼图 + 音轨 / ASR 体检。
按 2026-11-15 口径不落盘复盘/开发说明，结论只在对话里给。

S05 v6 用户原话反推（G15）：
  1) 陆沉瞳孔红、不是眼眶红 → 红只出现在两个瞳孔针尖，眼白/眼睑/眼周正常
  2) 蓝隼眼睛不变红 → 墨镜不透光、眼周肤色正常，全片无红眼
  3) 陆沉跑过来进攻、镜头对着陆沉 → Shot2/3 画面主体是陆沉正面冲镜
  4) 台词不乱说/无字幕（G29）

S06 v5 用户原话反推（G15）：
  1) 安娜脚进攻进行中切镜到特写进攻镜头、要连上 → Shot2 高踢 → Shot3 同一次踢的切镜特写
  2) 然后才脱身 → Shot4 才松手落下，脱身后不再进攻
  3) 不是进攻后脱身又进攻才有特写 → 顺序不可颠倒
  4) 台词不乱说/无字幕（G29）

用法：python check_ep06_s05v6_s06v5.py <video_path> <tag>
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

VIDEO = Path(sys.argv[1])
TAG = sys.argv[2] if len(sys.argv) > 2 else VIDEO.stem
WORK = Path(r"C:\Users\Administrator\WorkBuddy\2026-10-23-12-30-36\_p04a_work\ep06")
WORK.mkdir(parents=True, exist_ok=True)


def run(args: list[str]) -> bytes:
    return subprocess.run(args, capture_output=True).stdout


def sheet(cap, times, name, cols=4, tw=420, th=236):
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

    if TAG.startswith("s05"):
        # 全景总览
        sheet(cap, [0.5, 1.5, 2.2, 3.0, 4.0, 5.2, 6.2, 7.2, 8.2, 9.2,
                    10.2, 11.2, 12.2, 13.2, 14.2, 14.9],
              f"{TAG}_sheet.jpg", cols=4, tw=400, th=225)
        # Shot2/3 进攻镜（镜头对着陆沉 + 瞳孔红）
        sheet(cap, [2.0, 2.6, 3.2, 3.8, 4.4, 5.0, 5.6, 6.2],
              f"{TAG}_attack_sheet.jpg", cols=4, tw=420, th=236)
        # Shot5 台词镜（蓝隼眼睛不变红 + 无字幕）
        sheet(cap, [11.0, 11.6, 12.2, 12.8, 13.4, 14.0, 14.6, 14.9],
              f"{TAG}_dialogue_sheet.jpg", cols=4, tw=420, th=236)
    else:
        sheet(cap, [0.5, 1.5, 2.2, 3.0, 4.0, 4.8, 5.4, 6.0, 6.6, 7.2,
                    7.8, 8.4, 9.2, 10.2, 11.2, 12.2, 13.2, 14.2, 14.9],
              f"{TAG}_sheet.jpg", cols=4, tw=400, th=225)
        # 进攻→切镜特写→脱身 顺序
        sheet(cap, [2.0, 2.6, 3.2, 4.0, 4.6, 5.2, 5.8, 6.4, 7.0, 7.6, 8.2, 8.8],
              f"{TAG}_kick_sheet.jpg", cols=4, tw=420, th=236)
    cap.release()

    if a:
        raw = run(["ffmpeg", "-v", "quiet", "-i", str(VIDEO),
                   "-ac", "1", "-ar", "16000", "-f", "s16le", "-"])
        if raw:
            x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            print(f"audio RMS: {20*np.log10(np.sqrt((x**2).mean())+1e-9):.1f} dB")

    try:
        from faster_whisper import WhisperModel
        cache = (Path.home() / ".cache" / "huggingface" / "hub" /
                 "models--Systran--faster-whisper-small" / "snapshots")
        snaps = sorted(x for x in cache.iterdir() if x.is_dir()) if cache.exists() else []
        src = str(snaps[-1]) if snaps else "small"
        model = WhisperModel(src, device="cpu", compute_type="int8")
        segs, _ = model.transcribe(str(VIDEO), beam_size=5)
        found = [(round(s.start, 1), round(s.end, 1), round(s.no_speech_prob, 2),
                  s.text.strip()) for s in segs if s.text.strip()]
        print(f"ASR segments = {len(found)}")
        for f in found:
            print("   ", f)
    except Exception as exc:  # noqa: BLE001
        print(f"ASR skipped: {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
