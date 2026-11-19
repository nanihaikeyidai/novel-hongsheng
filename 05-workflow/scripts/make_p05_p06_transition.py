# -*- coding: utf-8 -*-
"""EP05 · 05 → 06a 过渡段：ND 研究所深夜远景 + 打字机音效 + 逐字字幕。

用户 2026-11-07：「05 到06a 插入一段过渡段，给一个ND研究所的远景，
旁边打字机音效打出字幕，ND研究所 / 23：15」

全流程本地后期，0 RH 金币、0 视频生成：
  1) ImageGen 出的远景图 → 去右下角「AI生成」水印（亮像素 mask + inpaint）
     → 温和赛璐璐化（P16 配方）→ 冷蓝微调 → 1664×928
  2) numpy 合成打字机击键 / 回车铃 / 夜风底噪，48kHz 立体声
  3) PIL 逐帧绘制缓推背景 + 逐字字幕 + 闪烁光标，rawvideo 管道喂 ffmpeg
  4) 输出 H.264 / 1664×928 / 24fps / 5.0s / 48kHz AAC / faststart

产物目录：ep05/营救陆沉/红绳片段05/过渡段_05-06_ND研究所/
"""
from __future__ import annotations

import math
import subprocess
import wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

WORK = Path(r"C:\Users\Administrator\WorkBuddy\2026-10-23-12-30-36\_p04a_work")
GEN_IMG = WORK / "nd_gen" / "Redraw_as_a_completely_NEW_ext_2026-11-07T06-10-48.png"
TMP = WORK / "nd_gen"
OUT_DIR = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep05\营救陆沉\红绳片段05\过渡段_05-06_ND研究所")
OUT_IMG = OUT_DIR / "ND研究所_远景_日漫化.png"
OUT_WAV = TMP / "typewriter.wav"
OUT_MP4 = OUT_DIR / "P05-06_过渡_ND研究所_2315.mp4"

W, H = 1664, 928
FPS = 24
DUR = 5.0
NFRAMES = int(FPS * DUR)
SR = 48000

FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
LINE1 = "ND研究所"
LINE2 = "23：15"
# 逐字出现时刻（秒），与击键音共用同一时间轴
T1 = [0.80, 1.02, 1.24, 1.46, 1.68]
T2 = [2.45, 2.66, 2.87, 3.08, 3.29]
T_CARRIAGE = 2.12


def load_rgb(p: Path) -> np.ndarray:
    with open(p, "rb") as f:
        return np.array(Image.open(f).convert("RGB"))


def remove_watermark(rgb: np.ndarray) -> np.ndarray:
    """右下角「AI生成 / WORKBUDDY」：只抹高亮低饱和的水印笔画，保留湿地纹理。"""
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    h, w = bgr.shape[:2]
    x0, y0 = int(w * 0.88), int(h * 0.90)
    roi = bgr[y0:h, x0:w]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    bright = (hsv[:, :, 2] > 135) & (hsv[:, :, 1] < 90)
    mask_roi = (bright.astype(np.uint8) * 255)
    mask_roi = cv2.dilate(mask_roi, np.ones((3, 3), np.uint8), iterations=2)
    mask = np.zeros((h, w), np.uint8)
    mask[y0:h, x0:w] = mask_roi
    out = cv2.inpaint(bgr, mask, 5, cv2.INPAINT_TELEA)
    return cv2.cvtColor(out, cv2.COLOR_BGR2RGB)


def celify(rgb: np.ndarray) -> np.ndarray:
    """温和赛璐璐（P16 配方）：双边滤波 + 16 级量化 + 细墨线 + 冷蓝灰微调。"""
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    sm = cv2.bilateralFilter(bgr, 7, 40, 40)
    step = 255 / 15
    q = np.clip(np.round(sm.astype(np.float32) / step) * step, 0, 255).astype(np.uint8)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    edge = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 30, 90)
    m = (edge > 0).astype(np.float32)[..., None]
    q = np.clip(q.astype(np.float32) * (1 - 0.24 * m), 0, 255).astype(np.uint8)
    out = cv2.addWeighted(q, 0.74, bgr, 0.26, 0)
    out[:, :, 0] = np.clip(out[:, :, 0].astype(np.int16) + 4, 0, 255).astype(np.uint8)
    out[:, :, 2] = np.clip(out[:, :, 2].astype(np.int16) - 3, 0, 255).astype(np.uint8)
    out = cv2.resize(out, (W, H), interpolation=cv2.INTER_LANCZOS4)
    return cv2.cvtColor(out, cv2.COLOR_BGR2RGB)


def vignette(rgb: np.ndarray, strength: float = 0.34) -> np.ndarray:
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = W / 2, H / 2
    r = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2) / math.sqrt(2)
    a = np.clip(1 - strength * (r ** 1.7), 0, 1).astype(np.float32)[..., None]
    return np.clip(rgb.astype(np.float32) * a * 0.92, 0, 255).astype(np.uint8)


def prepare_background() -> np.ndarray:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img = celify(remove_watermark(load_rgb(GEN_IMG)))
    img = vignette(img)
    Image.fromarray(img).save(OUT_IMG)
    print(f"background -> {OUT_IMG} ({img.shape[1]}x{img.shape[0]})", flush=True)
    return img


def _click(seed: int, dur: float = 0.075) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    snap = noise * np.exp(-t / 0.0055)
    thud = 0.55 * np.sin(2 * np.pi * (165 + seed % 7 * 9) * t) * np.exp(-t / 0.013)
    tick = 0.42 * np.sin(2 * np.pi * 2350 * t) * np.exp(-t / 0.0035)
    return (0.46 * snap + thud + tick) * np.exp(-t / 0.05)


def _carriage() -> np.ndarray:
    dur = 0.42
    n = int(SR * dur)
    t = np.arange(n) / SR
    rng = np.random.default_rng(77)
    slide = rng.normal(0, 1, n) * np.exp(-t / 0.055) * 0.25
    clack = 0.45 * np.sin(2 * np.pi * 620 * t) * np.exp(-t / 0.05)
    bell = 0.30 * np.sin(2 * np.pi * 1580 * t) * np.exp(-t / 0.19)
    return slide + clack + bell


def build_audio() -> None:
    n = int(SR * DUR)
    buf = np.zeros(n, np.float32)
    rng = np.random.default_rng(2026)
    # 极轻夜风 / 电流底噪
    t = np.arange(n) / SR
    wind = rng.normal(0, 1, n)
    k = np.convolve(wind, np.ones(64) / 64, mode="same")
    buf += 0.006 * k + 0.004 * np.sin(2 * np.pi * 52 * t)
    # 击键
    for i, ts in enumerate(T1 + T2):
        s = int(ts * SR)
        y = _click(i + 1) * (0.85 if i < len(T1) else 0.78)
        buf[s:s + len(y)] += y
    # 回车换行
    s = int(T_CARRIAGE * SR)
    y = _carriage()
    buf[s:s + len(y)] += y
    # 轻混响（两次短延迟）
    rev = np.zeros_like(buf)
    for d, g in ((0.043, 0.20), (0.091, 0.11)):
        dd = int(d * SR)
        rev[dd:] += buf[:-dd] * g
    buf += rev
    # 首尾淡入淡出 + 峰值归一
    fade = int(0.12 * SR)
    buf[:fade] *= np.linspace(0, 1, fade)
    buf[-fade:] *= np.linspace(1, 0, fade)
    buf *= 0.62 / max(np.max(np.abs(buf)), 1e-6)
    stereo = np.stack([buf, buf * 0.985], axis=1)
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(OUT_WAV), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    print(f"audio -> {OUT_WAV} ({DUR}s, 48kHz stereo)", flush=True)


def draw_text(d: ImageDraw.ImageDraw, xy, text, font, fill, stroke):
    d.text(xy, text, font=font, fill=fill, stroke_width=3, stroke_fill=stroke)


def render(bg: np.ndarray) -> None:
    f1 = ImageFont.truetype(FONT_BOLD, 74)
    f2 = ImageFont.truetype(FONT_BOLD, 60)
    base = Image.fromarray(bg)
    x0, y1, y2 = 132, 676, 782
    fg = (232, 241, 248)
    fg2 = (196, 220, 236)
    stroke = (8, 14, 22)

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(OUT_WAV),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", "-t", str(DUR),
        str(OUT_MP4),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for i in range(NFRAMES):
        t = i / FPS
        # 缓慢推近 1.00 → 1.065，中心轻微上移
        scale = 1.0 + 0.065 * (t / DUR)
        nw, nh = int(W * scale), int(H * scale)
        big = base.resize((nw, nh), Image.Resampling.LANCZOS)
        cx = nw // 2
        cy = int(nh * (0.50 - 0.012 * (t / DUR)))
        left = max(0, min(nw - W, cx - W // 2))
        top = max(0, min(nh - H, cy - H // 2))
        frame = big.crop((left, top, left + W, top + H)).convert("RGB")

        d = ImageDraw.Draw(frame)
        n1 = sum(1 for ts in T1 if t >= ts)
        n2 = sum(1 for ts in T2 if t >= ts)
        if n1:
            draw_text(d, (x0, y1), LINE1[:n1], f1, fg, stroke)
        if n2:
            draw_text(d, (x0 + 6, y2), LINE2[:n2], f2, fg2, stroke)
        # 闪烁光标跟在最后一行已出文字之后
        if 0.72 <= t <= 4.62 and int(t * 4) % 2 == 0:
            if n2:
                w2 = d.textlength(LINE2[:n2], font=f2)
                cx2, cy2 = x0 + 6 + w2 + 10, y2 + 8
                d.rectangle((cx2, cy2, cx2 + 5, cy2 + 50), fill=fg2)
            elif n1:
                w1 = d.textlength(LINE1[:n1], font=f1)
                cx1, cy1 = x0 + w1 + 10, y1 + 10
                d.rectangle((cx1, cy1, cx1 + 5, cy1 + 62), fill=fg)

        # 首尾淡入淡出（接 P05a 末帧 / P06a 首帧）
        fade = 0.0
        if t < 0.35:
            fade = 1 - t / 0.35
        elif t > DUR - 0.35:
            fade = (t - (DUR - 0.35)) / 0.35
        if fade > 0:
            arr = np.asarray(frame).astype(np.float32) * (1 - fade)
            frame = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg failed rc={rc}")
    print(f"video -> {OUT_MP4} ({OUT_MP4.stat().st_size // 1024} KB)", flush=True)


def main() -> int:
    bg = prepare_background()
    build_audio()
    render(bg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
