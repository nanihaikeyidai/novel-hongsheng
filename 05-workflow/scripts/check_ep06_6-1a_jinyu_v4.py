# -*- coding: utf-8 -*-
"""EP06 6-1a 云端金鱼 v4 成片验收：规格 + 四段专项拼图 + 背景不动量化 + 音轨。

不烧币、不提交任何生成任务。
用法：python check_ep06_6-1a_jinyu_v4.py [video_path]

v4 验收判据（从 David 2026-11-14 原话逐条反推，G15；禁止沿用 v3 验收表）：
  1) 「不用表达跳车动作」→ 全片有没有人离座／腾空／落地？
  2) 「只表达开门动作准备跳的东西」→ 两扇前门是否推开、人是否还在座位上？
  3) 「镜头切蓝隼脸部邪恶笑容特写」→ 是否有一格脸部大特写、笑容明确狂妄？
  4) 「再切到装过来的车」→ 是否出现车头朝蓝隼逼近的新外部机位？
  5) 「旁边背景不用动」→ Shot 5 柱子／灯管／停车线是否逐帧同坐标（另有量化指标）？
  6) 「看隼正面对着车不是侧面」→ 蓝隼是否双肩平齐、墨镜对称、正对镜头？
  7) 「安娜在主驾」（上一版要求未撤销）→ 首镜／开门镜里方向盘是否在她正前方？
  8) 「还是控制不住」→ 全片是否只剩门开／笑／车距三类变化，没有碰撞／踢击／翻转／爆炸？
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
SEG = ROOT / "05-workflow" / "ep06" / "6-1a_跳车掀车"
VIDEO = Path(sys.argv[1]) if len(sys.argv) > 1 else SEG / "视频草稿" / "EP06_6-1a_金鱼_v4.mp4"
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


def background_stillness(cap, times):
    """判据 5 量化：Shot 5 上部背景区（柱子/灯管/停车线）相邻帧灰度平均绝对差。

    数值越小＝背景越静止；仅作客观参考，最终以拼图目检为准。
    """
    import cv2
    import numpy as np
    imgs = []
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        if ok:
            g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
            h = g.shape[0]
            imgs.append(g[:int(h * 0.45), :].astype(np.float32))  # 上部背景带
    if len(imgs) < 2:
        print("background stillness: NOT ENOUGH FRAMES")
        return
    diffs = [float(np.abs(imgs[i] - imgs[i - 1]).mean()) for i in range(1, len(imgs))]
    print(f"background stillness (upper 45% band, mean |delta| 0-255): "
          f"{[round(d, 2) for d in diffs]}  mean={sum(diffs)/len(diffs):.2f}")


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

    # 8 帧总览（与 v1/v2/v3 同口径，便于并排比对）
    sheet(cap, [0.5, 2.5, 4.5, 6.0, 8.0, 10.5, 13.0, 14.5],
          "jinyu_v4_sheet.jpg", cols=2, tw=400, th=225)

    # 专项 A：首镜挡风玻璃车内 POV + 蓝隼正面（判据 6/7）
    sheet(cap, [0.2, 0.8, 1.4, 2.0, 2.4],
          "jinyu_v4_windshield_sheet.jpg", cols=3, tw=420, th=236)

    # 专项 B：两扇门打开 + 人仍在座（判据 1/2/7）
    sheet(cap, [2.6, 3.2, 3.8, 4.4, 5.0, 5.6, 6.2, 6.8, 7.4, 7.9],
          "jinyu_v4_doors_sheet.jpg", cols=4, tw=400, th=225)

    # 专项 C：蓝隼脸部邪恶笑容特写（判据 3/6）
    sheet(cap, [8.0, 8.5, 9.0, 9.5, 10.0, 10.4],
          "jinyu_v4_smirk_sheet.jpg", cols=3, tw=420, th=236)

    # 专项 D：车迎面撞来 + 背景不动（判据 4/5/6/8）
    bg_times = [10.6, 11.2, 11.8, 12.4, 13.0, 13.6, 14.2, 14.8]
    sheet(cap, bg_times, "jinyu_v4_car_bg_sheet.jpg", cols=4, tw=400, th=225)
    background_stillness(cap, bg_times)
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

    # 离线 ASR：0 台词段若识别出人声需复盘（G13）
    try:
        from faster_whisper import WhisperModel
        # 优先本地缓存快照：直接 WhisperModel("small") 会走 HF 校验，
        # 本机代理常返 502 导致体检假失败（2026-11-14 v4 实测）。
        cache = (Path.home() / ".cache" / "huggingface" / "hub" /
                 "models--Systran--faster-whisper-small" / "snapshots")
        snaps = sorted(x for x in cache.iterdir() if x.is_dir()) if cache.exists() else []
        src = str(snaps[-1]) if snaps else "small"
        model = WhisperModel(src, device="cpu", compute_type="int8")
        segs, _ = model.transcribe(str(VIDEO), beam_size=5)
        found = [s.text for s in segs if s.text.strip()]
        print(f"ASR model={src} segments = {len(found)} {found[:5]}")
    except Exception as exc:  # noqa: BLE001
        print(f"ASR skipped: {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
