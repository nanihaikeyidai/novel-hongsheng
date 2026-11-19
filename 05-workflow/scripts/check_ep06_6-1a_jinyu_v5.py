# -*- coding: utf-8 -*-
"""EP06 6-1a 云端金鱼 v5 成片验收：规格 + 六段专项拼图 + 加速/背景量化 + 音轨。

不烧币、不提交任何生成任务。
用法：python check_ep06_6-1a_jinyu_v5.py [video_path]

v5 验收判据（从用户 2026-11-14 原话逐条反推，G15；禁止沿用 v4 验收表）：
  1) 动作太慢了，动作要快 → 门是否一下弹开（≤0.5s 内到 45°）？
  2) 车速也要快 → 车头/蓝隼在相邻帧是否明显变大？
  3) 加速撞的感觉 → 后半段运动能量是否大于前半段（是加速不是匀速）？
  4) 要夸张点增加速度感 → 速度线/轮毂放射拖影/地面拖影/发衣后扬/短切镜？
  5) 给一个车轮加速的镜头 → 6.2-8.2s 是否有独立车轮特写、轮子明显飞转？
  6) 现在是慢吞吞开过去 → 有没有驶过/越过蓝隼/横向平移？是否停在撞击前？
  7) 不用表达跳车（未撤销） → 有人离座/腾空/落地吗？
  8) 只开门准备（未撤销） → 两扇前门推开且臀部仍在座椅上？
  9) 切蓝隼邪恶笑容特写（未撤销） → 有脸部大特写？
 10) 隼正面对着车不是侧面（未撤销） → 双耳同框/墨镜等宽/双肩平齐？
 11) 旁边背景不用动（未撤销） → 柱子灯管停车线逐帧同坐标（G22 量化）？
 12) 安娜在主驾（未撤销） → 方向盘在她正前方？
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
SEG = ROOT / "05-workflow" / "ep06" / "6-1a_跳车掀车"
VIDEO = Path(sys.argv[1]) if len(sys.argv) > 1 else SEG / "视频草稿" / "EP06_6-1a_金鱼_v5.mp4"
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


def _gray_at(cap, t):
    import cv2
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, fr = cap.read()
    if not ok:
        return None
    return cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)


def background_stillness(cap, times):
    """判据 11 量化（G22）：Shot 6 上部背景带相邻帧灰度平均绝对差。

    速度线只贴车身/地面，上部柱子灯管应仍同坐标；切镜首帧大差值单独剔除。
    """
    import numpy as np
    imgs = []
    for t in times:
        g = _gray_at(cap, t)
        if g is not None:
            h = g.shape[0]
            imgs.append(g[:int(h * 0.40), :].astype(np.float32))
    if len(imgs) < 2:
        print("background stillness: NOT ENOUGH FRAMES")
        return
    diffs = [float(np.abs(imgs[i] - imgs[i - 1]).mean()) for i in range(1, len(imgs))]
    cuts = [d for d in diffs if d > 20]
    rest = [d for d in diffs if d <= 20]
    mean_rest = sum(rest) / len(rest) if rest else float("nan")
    print(f"background stillness (upper 40% band, 0-255): {[round(d, 2) for d in diffs]}")
    print(f"  cut-like diffs (>20, excluded): {[round(d, 2) for d in cuts]}  "
          f"rest mean={mean_rest:.2f}  {'LOCK OK' if mean_rest < 10 else 'CHECK PLEASE'}")


def motion_energy(cap, times):
    """判据 3 粗量化：每个采样点取 t 与 t+0.10s 两帧算整帧灰度差。

    只作「后半段速率是否大于前半段」的客观参考；切镜会放大个别值，
    最终仍以拼图目检为准（G22 不用单一指标下结论）。
    """
    import numpy as np
    vals = []
    for t in times:
        a, b = _gray_at(cap, t), _gray_at(cap, t + 0.10)
        if a is None or b is None:
            continue
        vals.append((t, float(np.abs(a.astype(np.float32) - b.astype(np.float32)).mean())))
    if len(vals) < 4:
        print("motion energy: NOT ENOUGH FRAMES")
        return
    print(f"motion energy (|delta over 0.10s|, 0-255): "
          f"{[(round(t, 1), round(v, 2)) for t, v in vals]}")
    half = len(vals) // 2
    early = sum(v for _, v in vals[:half]) / half
    late = sum(v for _, v in vals[half:]) / (len(vals) - half)
    print(f"  early mean={early:.2f}  late mean={late:.2f}  "
          f"{'ACCELERATING' if late > early * 1.15 else 'NOT CLEARLY ACCELERATING'}")


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

    # 8 帧总览（与 v1-v4 同口径，便于并排比对）
    sheet(cap, [0.5, 2.4, 3.8, 5.2, 7.0, 9.5, 12.0, 14.5],
          "jinyu_v5_sheet.jpg", cols=2, tw=400, th=225)

    # 专项 A：首镜 POV 加速逼近（判据 2/6/12）
    sheet(cap, [0.2, 0.6, 1.0, 1.4, 1.8, 2.0],
          "jinyu_v5_windshield_sheet.jpg", cols=3, tw=420, th=236)

    # 专项 B：门一下弹开 + 人仍在座（判据 1/7/8/12）
    sheet(cap, [2.0, 2.3, 2.6, 2.9, 3.2, 3.5, 3.8, 4.1, 4.4],
          "jinyu_v5_doors_sheet.jpg", cols=3, tw=420, th=236)

    # 专项 C：蓝隼正轴特写（判据 9/10）
    sheet(cap, [4.6, 5.0, 5.4, 5.8, 6.1],
          "jinyu_v5_smirk_sheet.jpg", cols=3, tw=420, th=236)

    # 专项 D：新增车轮加速镜头（判据 4/5）
    sheet(cap, [6.2, 6.6, 7.0, 7.4, 7.8, 8.1],
          "jinyu_v5_wheel_sheet.jpg", cols=3, tw=420, th=236)

    # 专项 E：撞车段 + 背景不动 + 加速量化（判据 3/4/6/11）
    bg_times = [8.4, 9.4, 10.4, 11.4, 12.4, 13.4, 14.4, 14.8]
    sheet(cap, bg_times, "jinyu_v5_car_bg_sheet.jpg", cols=4, tw=400, th=225)
    background_stillness(cap, bg_times)
    motion_energy(cap, [8.5, 9.2, 9.9, 10.6, 11.3, 12.0, 12.7, 13.4, 14.1])
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
