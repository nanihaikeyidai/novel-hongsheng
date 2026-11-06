#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""气声化（贴耳耳语）后期层：0 币耗、纯 DSP、不改变台词起音点。

IndexTTS 2.5 没有 whisper 开关，模型侧的 [breath] 标记效果不稳定。
这里直接补一层「声带没闭合」的物理特征：

1. 谐波软化：原声与 3.4kHz 低通版混合，削弱清晰咬字/胸腔共鸣；
2. 气流噪声：带通 500–7000Hz 的 1/f 着色噪声，用原声 25ms 能量包络调制，
   只在发声时存在，并在字间保留极轻的连续气流（低于 trim 阈值，不漂起音点）；
3. 近讲 EQ：切 90Hz 以下胸腔、300Hz -2dB 去厚、2.5kHz -1dB 去"喊"感、
   7kHz +2.5dB 抬气声细节；
4. 整体电平由 replace_line.py 的 --level-offset-db 控制（不要再在这里压，
   否则响度对齐会把它拉回去）。

用法：
    python whisperize.py --input 候选音频/H_origvoice_cold.wav \
        --output 候选音频/W_whisper.wav --breath 0.38 --soft 0.55
"""
from __future__ import annotations

import argparse
import math
import wave
from pathlib import Path

import numpy as np

SR = 48000


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        assert w.getframerate() == SR, f"需 48kHz: {path}"
        ch = w.getnchannels()
        d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    d = d.reshape(-1, ch)
    return d.mean(axis=1) if ch == 2 else d.reshape(-1)


def write_wav(path: Path, x: np.ndarray) -> None:
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x ** 2))) if len(x) else 1e-9


def _fft_len(n: int) -> int:
    return 1 << max(1, (n - 1).bit_length())


def lowpass(x: np.ndarray, cutoff: float, order: int = 4) -> np.ndarray:
    n = len(x)
    N = _fft_len(n)
    F = np.fft.rfft(x, N)
    f = np.fft.rfftfreq(N, 1 / SR)
    F = F / (1 + (f / cutoff) ** order)
    return np.fft.irfft(F, N)[:n]


def eq_curve(x: np.ndarray) -> np.ndarray:
    """贴耳近讲 EQ，单位 dB，最后转成线性增益。"""
    N = _fft_len(len(x))
    f = np.fft.rfftfreq(N, 1 / SR)
    db = np.zeros_like(f)
    # 高通 90Hz（cos 过渡），切掉胸腔厚度
    t = np.clip(f / 90.0, 0, 1)
    db += -26 * (1 - 0.5 * (1 - np.cos(np.pi * t)))
    for center, width, gain in ((300, 190, -2.0), (2500, 900, -1.0),
                                (7000, 2600, 2.5), (13500, 3000, -3.0)):
        db += gain * np.exp(-((f - center) / width) ** 2)
    F = np.fft.rfft(x, N) * (10 ** (db / 20))
    return np.fft.irfft(F, N)[:len(x)]


def colored_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    """500–7000Hz 平滑带通 + 1/f^0.6 着色的气流噪声，归一化到单位 RMS。"""
    N = _fft_len(n)
    F = np.fft.rfft(rng.normal(0, 1, N))
    f = np.fft.rfftfreq(N, 1 / SR)
    lo, hi, roll = 500.0, 7000.0, 400.0
    # 平滑阶跃：用两段 cos 过渡
    a = np.clip((f - (lo - roll)) / (2 * roll), 0, 1)
    b = np.clip(((hi + roll) - f) / (2 * roll), 0, 1)
    rise = 0.5 - 0.5 * np.cos(np.pi * a)
    fall = 0.5 - 0.5 * np.cos(np.pi * b)
    band = rise * fall
    color = 1.0 / np.maximum(f, 80.0) ** 0.6
    F *= band * color
    y = np.fft.irfft(F, N)[:n]
    return y / max(rms(y), 1e-9)


def envelope(x: np.ndarray) -> np.ndarray:
    """25ms 窗 / 5ms 跳的 RMS 包络，插值回采样点并归一化。"""
    win, hop = int(0.025 * SR), int(0.005 * SR)
    idx = range(0, max(1, len(x) - win), hop)
    e = np.array([rms(x[i:i + win]) for i in idx])
    if not len(e):
        return np.ones_like(x)
    e = np.convolve(e, np.ones(5) / 5, mode="same")
    grid = np.arange(len(e)) * hop
    ef = np.interp(np.arange(len(x)), grid, e, left=e[0], right=e[-1])
    ef /= max(float(ef.max()), 1e-9)
    # 字间保留 5% 连续气流（低于 trim_silence 的 8% 阈值，不会前移起音点）
    return 0.95 * ef + 0.05


def whisperize(x: np.ndarray, breath: float, soft: float,
               seed: int = 20261106) -> np.ndarray:
    body = (1 - soft) * x + soft * lowpass(x, 3400)
    base = rms(body)
    noise = colored_noise(len(x), np.random.default_rng(seed)) * envelope(x)
    noise *= base / max(rms(noise), 1e-9)
    y = eq_curve(body * 0.82 + noise * breath)
    # 保持与输入相同的有效响度，电平交给 replace_line.py 统一控制
    y *= base / max(rms(y), 1e-9)
    pk = float(np.abs(y).max())
    if pk > 0.95:
        y *= 0.95 / pk
    return y


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--breath", type=float, default=0.35,
                    help="气声层相对原声 RMS 的比例，0.25 轻 / 0.5 明显")
    ap.add_argument("--soft", type=float, default=0.55,
                    help="谐波软化比例 0–1，越高越不像正常发声")
    ap.add_argument("--seed", type=int, default=20261106)
    args = ap.parse_args()
    src, dst = Path(args.input), Path(args.output)
    dst.parent.mkdir(parents=True, exist_ok=True)
    x = read_wav(src)
    y = whisperize(x, args.breath, args.soft, args.seed)
    write_wav(dst, y)
    print(f"{dst.name}: {len(y)/SR:.3f}s  breath={args.breath:.2f} soft={args.soft:.2f} "
          f"RMS {20*math.log10(rms(x)):.1f}->{20*math.log10(rms(y)):.1f} dB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
