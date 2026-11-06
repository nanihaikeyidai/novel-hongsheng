#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第四轮声线整形：更低沉 + 更快 + 带戏谑笑意，仍保住气声耳语。

三个互不冲突的物理轴（都在 48kHz 单声道 PCM 上做，0 币耗）：

1. 降音高（保时长）：ffmpeg `asetrate = SR * R` → `aresample = SR` → `atempo = 1/R`
   把 F0 乘 R（R = 2^(semitones/12)，负数=降调），时长补回原值；
   再叠一个 `atempo = tempo` 做真正的语速加快。
   **注意**：沈默是 14 岁少年音（David 规范），P09 例外只允许「低沉带进攻性」，
   所以半音只在 -1.0 ~ -2.5 之间取，绝不压到成年男声的 80Hz 区。
2. 气声层：复用 whisperize.py， softening 调低以保住笑意咬字；
3. 笑意 / 低沉 EQ：
   - 微笑语音的声学标志是 F2 上移 → 2.6kHz / 4.8kHz 轻微抬升；
   - 低沉厚度 → 140Hz 抬升 + 700Hz 去薄，与 90Hz 高通不冲突。
   必须在 whisperize 之后叠，否则会被 whisperize 的近讲 EQ 抵消。

用法：
    python voice_shaper.py --input 候选音频/M_smirk_text.wav \
      --output 候选音频/X_deep_smirk.wav \
      --semitones -1.8 --tempo 1.18 --smile 0.8 --breath 0.32 --soft 0.42
"""
from __future__ import annotations

import argparse
import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from whisperize import (SR, rms, read_wav, write_wav, whisperize, _fft_len)


def pitch_tempo(src: Path, dst: Path, semitones: float, tempo: float) -> None:
    """保时长降调 + 加速，输出 48k 单声道 PCM wav。"""
    r = 2.0 ** (semitones / 12.0)
    # asetrate 改名义采样率 → 音高×r、时长÷r；aresample 回 SR；
    # atempo=1/r 把时长补回，再乘 tempo 得到目标语速。
    atempo = (1.0 / r) * tempo
    assert 0.5 <= atempo <= 2.0, f"atempo 超范围: {atempo}"
    af = (f"asetrate={int(round(SR * r))},aresample={SR},"
          f"atempo={atempo:.6f}")
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(src),
         "-af", af, "-ac", "1", "-ar", str(SR),
         "-c:a", "pcm_s16le", str(dst)],
        check=True,
    )


def shape_eq(x: np.ndarray, smile: float, depth: float) -> np.ndarray:
    """低沉厚度 + 微笑共振峰，单位 dB。"""
    N = _fft_len(len(x))
    f = np.fft.rfftfreq(N, 1 / SR)
    db = np.zeros_like(f)
    # 低沉：抬 140Hz 基频区、压 700Hz 薄亮区
    db += depth * 2.0 * np.exp(-((f - 140) / 95) ** 2)
    db -= depth * 1.0 * np.exp(-((f - 700) / 320) ** 2)
    # 笑意：嘴角拉开 → F2 区与高频轻抬（不是"变响"，只改音色）
    db += smile * 2.0 * np.exp(-((f - 2600) / 1050) ** 2)
    db += smile * 1.0 * np.exp(-((f - 4800) / 1700) ** 2)
    F = np.fft.rfft(x, N) * (10 ** (db / 20))
    return np.fft.irfft(F, N)[:len(x)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--semitones", type=float, default=-1.8,
                    help="降调半音数（负值），少年音下限建议 -1.0~-2.5")
    ap.add_argument("--tempo", type=float, default=1.18,
                    help="语速倍数，>1 加快")
    ap.add_argument("--smile", type=float, default=0.8,
                    help="笑意 EQ 强度 0–1.2，抬 F2 区；0=无笑意")
    ap.add_argument("--depth", type=float, default=1.0,
                    help="低沉厚度 EQ 强度 0–1.2")
    ap.add_argument("--breath", type=float, default=0.32,
                    help="气声层比例（沿用 whisperize）")
    ap.add_argument("--soft", type=float, default=0.42,
                    help="谐波软化；比第三轮 0.55 低，保住笑意咬字")
    ap.add_argument("--seed", type=int, default=20261106)
    args = ap.parse_args()

    src, dst = Path(args.input), Path(args.output)
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.stem + "._pt.wav")
    try:
        pitch_tempo(src, tmp, args.semitones, args.tempo)
        x = read_wav(tmp)
        y = whisperize(x, args.breath, args.soft, args.seed)
        y = shape_eq(y, args.smile, args.depth)
        # 不在这里压电平：replace_line.py 的 RMS 对齐会抵消，轻声由它控制
        y *= rms(x) / max(rms(y), 1e-9)
        pk = float(np.abs(y).max())
        if pk > 0.95:
            y *= 0.95 / pk
        write_wav(dst, y)
    finally:
        tmp.unlink(missing_ok=True)

    with wave.open(str(src), "rb") as w:
        src_s = w.getnframes() / w.getframerate()
    print(f"{dst.name}: {src_s:.3f}s -> {len(y)/SR:.3f}s | "
          f"{args.semitones:+.1f}st tempo={args.tempo:.2f} "
          f"smile={args.smile:.2f} depth={args.depth:.2f} "
          f"breath={args.breath:.2f} soft={args.soft:.2f} | "
          f"RMS {20*math.log10(rms(x)):.1f}->{20*math.log10(rms(y)):.1f} dB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
