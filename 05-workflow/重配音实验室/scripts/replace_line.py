#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""时间窗重配音：把新台词贴回原成片的指定时间窗，画面/总时长完全不动。

用法：
    python replace_line.py --case cases/P09_晚安/case.json --line-audio 候选音频/A_text_threat.wav \
        --out 成片/P09_晚安_威胁版_v1.mp4 --preset dry

要点：
- 原音轨在台词窗内做 30ms 边缘平滑压低（保留环境底噪，不硬切出咔哒）；
- 新台词自动去掉首尾静音、按窗口可容长度做 atempo 微调、响度对齐到原片台词 RMS；
- `--level-offset-db` 可让新台词比原片更轻（悄悄话用 -5 ~ -8dB），这是"轻声"的真正开关；
- 输出 48kHz AAC + faststart（沿用 David 技巧文档第七节）。
- 纯后期，0 币耗，不重跑视频模型。
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parents[1]
SR = 48000


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(" ".join(cmd[:8]) + "\n" + r.stderr[-1200:])


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        assert w.getframerate() == SR, f"采样率不是 {SR}: {path}"
        ch = w.getnchannels()
        d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    return d.reshape(-1, ch)


def write_wav(path: Path, data: np.ndarray) -> None:
    d = np.clip(data, -1.0, 1.0)
    pcm = (d * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2 if data.ndim == 2 and data.shape[1] == 2 else 1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.asarray(x) ** 2))) if len(x) else 1e-9


def trim_silence(x: np.ndarray, thresh_ratio: float = 0.08, pad_ms: int = 35) -> np.ndarray:
    """按 10ms 帧能量切掉首尾静音，留一点气口。"""
    mono = x.mean(axis=1) if x.ndim == 2 else x
    hop = SR // 100
    n = len(mono) // hop
    e = np.array([rms(mono[i * hop:(i + 1) * hop]) for i in range(n)])
    if not len(e) or e.max() < 1e-5:
        return x
    thr = max(e.max() * thresh_ratio, 1e-4)
    idx = np.nonzero(e > thr)[0]
    a = max(0, int(idx[0] * hop - pad_ms * SR / 1000))
    b = min(len(mono), int((idx[-1] + 1) * hop + pad_ms * SR / 1000))
    return x[a:b]


def detect_voice_span(x: np.ndarray, a0: float, a1: float,
                      pad: float = 0.30) -> tuple[float, float]:
    """在原片 ASR 台词窗附近用 20ms 帧能量找真实起止点。

    ASR 时间戳常有 0.2–0.3s 偏移，直接拿它当放置点会音画错位（本案例实测
    ASR 4.07–4.77，真实有声 4.28–4.92）。以能量包络为准。
    """
    mono = x.mean(axis=1) if x.ndim == 2 else x
    hop = int(0.020 * SR)
    lo = max(0, int((a0 - pad) * SR))
    hi = min(len(mono), int((a1 + pad) * SR))
    e = np.array([rms(mono[i:i + hop]) for i in range(lo, hi - hop, hop)])
    if not len(e) or e.max() < 1e-4:
        return a0, a1
    idx = np.nonzero(e > max(e.max() * 0.06, 1e-4))[0]
    return lo / SR + idx[0] * hop / SR, lo / SR + (idx[-1] + 2) * hop / SR


def fit_duration(path: Path, max_seconds: float) -> Path:
    """超过窗口就无损保音高地轻微加速（atempo）。"""
    x = read_wav(path)
    cur = len(x) / SR
    if cur <= max_seconds:
        return path
    factor = cur / max_seconds
    if factor > 1.6:
        raise RuntimeError(f"新台词 {cur:.2f}s 远长于窗口 {max_seconds:.2f}s，请调 duration_factor")
    # 放到临时目录，避免污染候选音频目录（会被对比脚本重复统计）
    out = Path(tempfile.gettempdir()) / (path.stem + "_voicelab_fit.wav")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(path),
         "-af", f"atempo={factor:.4f}", "-ar", str(SR), "-ac", "1", str(out)])
    print(f"  atempo {factor:.3f} -> {read_wav(out).shape[0] / SR:.3f}s", flush=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--line-audio", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--preset", choices=["dry", "phone"], default="dry")
    ap.add_argument("--peak", type=float, default=0.92)
    ap.add_argument("--level-offset-db", type=float, default=0.0,
                    help="台词相对原片响度的偏移，负值=更轻（悄悄话用 -5~-8）")
    ap.add_argument("--bed", type=float, default=0.06,
                    help="窗口内保留的原环境底噪比例，轻声台词建议 0.02-0.04")
    args = ap.parse_args()

    case_path = Path(args.case)
    if not case_path.is_absolute():
        case_path = (LAB / case_path).resolve()
    base = case_path.parent
    case = json.loads(case_path.read_text(encoding="utf-8"))
    src = Path(case["source_video"])
    cfg_w0, cfg_w1 = (float(v) for v in case["window"])
    a0, a1 = (float(v) for v in case["original_line_asr"])
    line = Path(args.line_audio)
    if not line.is_absolute():
        line = (base / line).resolve()
    out = Path(args.out)
    if not out.is_absolute():
        out = (base / out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    work = base / "验收" / "_work"
    work.mkdir(parents=True, exist_ok=True)

    # 1) 原片参数与音轨
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(src)], capture_output=True, text=True
    ).stdout.strip()
    duration = float(probe)
    orig_wav = work / "orig_track.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vn",
         "-ac", "2", "-ar", str(SR), "-t", f"{duration:.6f}", str(orig_wav)])
    orig = read_wav(orig_wav)
    total = len(orig)
    print(f"原片 {duration:.3f}s / 音轨 {total / SR:.3f}s / {orig.shape}", flush=True)

    # 自动对齐：以原片真实能量起音点为准，不信 ASR 时间戳
    v0, v1 = detect_voice_span(orig, a0, a1)
    # 允许 case 把窗口向后放宽（耳语慢吐需要更长气口）；hard_end 是下一句硬边界。
    # 不写 hard_end 的旧 case 行为与原来一致。
    w0 = max(cfg_w0, v0 - 0.10)
    w1 = min(float(case.get("hard_end", cfg_w1 + 0.10)),
             max(cfg_w1, v1 + 0.10))
    print(f"对齐: ASR窗 {a0:.2f}-{a1:.2f}s → 实测有声 {v0:.2f}-{v1:.2f}s "
          f"(偏移 {v0 - a0:+.2f}s) | 替换窗 {w0:.2f}-{w1:.2f}s", flush=True)

    # 2) 新台词统一格式 + 可选电话带通 + 去静音
    clean = work / "line_clean.wav"
    af = []
    if args.preset == "phone":
        af = ["highpass=f=260", "lowpass=f=3500", "acompressor=threshold=-20dB:ratio=2:attack=5:release=120"]
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(line), "-ac", "1", "-ar", str(SR)]
    if af:
        cmd += ["-af", ",".join(af)]
    cmd.append(str(clean))
    run(cmd)
    new = trim_silence(read_wav(clean).reshape(-1))
    write_wav(work / "line_trim.wav", new)
    fit = fit_duration(work / "line_trim.wav", (w1 - v0) - 0.02)
    new = read_wav(fit).reshape(-1)
    print(f"新台词 {len(new) / SR:.3f}s (preset={args.preset})", flush=True)

    # 3) 响度对齐到原片台词窗
    orig_line = orig[int(v0 * SR):int(v1 * SR)].mean(axis=1)
    target = rms(orig_line)
    cur = rms(new)
    gain = (target / max(cur, 1e-9)) * (10 ** (args.level_offset_db / 20))
    new = new * gain
    pk = float(np.abs(new).max())
    if pk > args.peak:
        new = new * (args.peak / pk)
    print(f"响度: 原片台词窗 {20 * math.log10(target):.1f} dB, "
          f"新台词 {20 * math.log10(cur):.1f} dB -> 增益 {gain:.2f}x "
          f"(电平偏移 {args.level_offset_db:+.1f} dB)", flush=True)

    # 4) 窗口内原音轨压低（30ms 平滑边），叠加新台词
    mixed = orig.copy()
    s, e = int(w0 * SR), int(w1 * SR)
    win_len = e - s
    fade = int(0.030 * SR)
    env = np.ones(win_len, dtype=np.float32)
    env[:fade] = np.linspace(0, 1, fade)
    env[-fade:] = np.linspace(1, 0, fade)
    mixed[s:e] *= (1.0 - env[:, None])  # 原语音压到 0，环境窗内随新台词一起被替换
    # 窗口两端保留极轻的原环境底噪，避免"真空"感
    mixed[s:e] += orig[s:e] * (float(args.bed) * env[:, None])

    start = int(v0 * SR)  # 与原片真实起音点对齐，口型不漂
    n = min(len(new), total - start)
    edge = int(0.020 * SR)
    gain_env = np.ones(n, dtype=np.float32)
    gain_env[:edge] = np.linspace(0, 1, edge)
    gain_env[-edge:] = np.linspace(1, 0, edge)
    mixed[start:start + n] += (new[:n] * gain_env)[:, None]

    mix_wav = work / "mixed_track.wav"
    write_wav(mix_wav, mixed)

    # 5) 合成（画面直接 copy）
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-i", str(mix_wav),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         # 不加 -shortest：音频可能比视频短十几毫秒，加了会截掉最后一帧画面
         "-movflags", "+faststart", str(out)])
    print(f"输出 {out}  {out.stat().st_size / 1024 / 1024:.1f} MB", flush=True)

    # 6) 独立试听音频（全片混音）
    listen = out.with_name(out.stem + "_音轨.m4a")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(mix_wav),
         "-c:a", "aac", "-b:a", "160k", str(listen)])
    print(f"试听 {listen.name}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
