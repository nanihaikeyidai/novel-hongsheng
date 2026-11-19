# -*- coding: utf-8 -*-
"""EP06 6-1a 云端金鱼 v6 必要验收：规格 + 四段专项拼图 + 音轨 / ASR 体检。

不烧币、不提交任何生成任务；按 2026-11-15 新口径**不落盘复盘／开发说明文档**，
结论只在对话里给，交付列表只放视频。拼图只作内部目检，不进交付列表。

用法：python check_ep06_6-1a_jinyu_v6.py [video_path]

本轮用户原话逐条反推（G15，禁止沿用 v5 验收表）：
  1) 陆沉不是在后座在副驾 → 车内 POV 里两人是否同排（陆沉在右前、仪表盘在膝前）？
  2) 开门跳车动作一气呵成 → 4.5-7.0s 是否一个不切镜的连续动作，门开到两人离车？
  3) 安娜拉着陆沉 → 是否有抓腕／拉过中控的动作，两人始终连在一起？
  4) 和陆沉从主驾跳出 → 两人是否都从**同一扇左前主驾门**出去（不是左右分头）？
  5) 抱着地上滚了几圈缓解冲击力 → 7.0-11.5s 是否抱团落地滚 2-3 圈、收势护住？
  6) 未撤回：加速撞／车轮镜头／蓝隼邪恶笑容特写且完全正面／冷蓝灰日漫／0 台词。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
SEG = ROOT / "05-workflow" / "ep06" / "6-1a_跳车掀车"
VIDEO = Path(sys.argv[1]) if len(sys.argv) > 1 else SEG / "视频草稿" / "EP06_6-1a_金鱼_v6.mp4"
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

    # 8 帧总览
    sheet(cap, [0.5, 2.4, 3.8, 5.2, 7.0, 9.5, 12.0, 14.5],
          "jinyu_v6_sheet.jpg", cols=2, tw=400, th=225)

    # 专项 A：车内 POV → 两人同排 + 副驾（判据 1/6）
    sheet(cap, [0.2, 0.6, 1.0, 1.4, 1.8, 2.0],
          "jinyu_v6_pov_seats_sheet.jpg")

    # 专项 B：开门 → 抓腕 → 同侧跃出，一气呵成（判据 2/3/4）
    sheet(cap, [4.5, 4.9, 5.3, 5.7, 6.1, 6.5, 6.9],
          "jinyu_v6_exit_sheet.jpg")

    # 专项 C：抱团落地滚几圈卸力（判据 5）
    sheet(cap, [7.0, 7.6, 8.2, 8.8, 9.4, 10.0, 10.6, 11.2],
          "jinyu_v6_roll_sheet.jpg", cols=4, tw=400, th=225)

    # 专项 D：蓝隼正轴特写（判据 6，G21）
    sheet(cap, [2.0, 2.3, 2.6, 2.9, 3.2],
          "jinyu_v6_smirk_sheet.jpg")

    # 专项 E：车轮镜头 + 末段撞车（判据 6）
    sheet(cap, [3.3, 3.6, 3.9, 4.2, 4.4],
          "jinyu_v6_wheel_sheet.jpg")
    sheet(cap, [11.5, 12.2, 12.9, 13.6, 14.3, 14.8],
          "jinyu_v6_final_car_sheet.jpg")
    cap.release()

    # 音轨响度体检（G13：由体检决定是否加增益／换轨）
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

    # 离线 ASR：0 台词段若识别出人声需处理（G13）
    try:
        from faster_whisper import WhisperModel
        cache = (Path.home() / ".cache" / "huggingface" / "hub" /
                 "models--Systran--faster-whisper-small" / "snapshots")
        snaps = sorted(x for x in cache.iterdir() if x.is_dir()) if cache.exists() else []
        src = str(snaps[-1]) if snaps else "small"
        model = WhisperModel(src, device="cpu", compute_type="int8")
        segs, _ = model.transcribe(str(VIDEO), beam_size=5)
        found = [s.text.strip() for s in segs if s.text.strip()]
        print(f"ASR segments = {len(found)} {found[:5]}")
    except Exception as exc:  # noqa: BLE001
        print(f"ASR skipped: {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
