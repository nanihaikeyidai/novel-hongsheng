#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""候选音频客观对比：时长 / 响度 / 基频 / 语速 / 尾音走向。

不判断"好不好听"，只给出可量化差异，供人工试听前筛掉明显跑偏的版本。
"""
from __future__ import annotations

import argparse
import json
import wave
from pathlib import Path

import numpy as np

SR = 48000


def read(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
        if w.getnchannels() == 2:
            d = d.reshape(-1, 2).mean(axis=1)
        if w.getframerate() != SR:
            raise RuntimeError(f"{path.name} 采样率 {w.getframerate()}，需先转 48k")
    return d


def voiced_frames(x: np.ndarray):
    win, hop = int(0.040 * SR), int(0.010 * SR)
    for i in range(0, len(x) - win, hop):
        seg = x[i:i + win]
        e = float(np.sqrt(np.mean(seg ** 2)))
        yield i, seg, e


def f0_autocorr(seg: np.ndarray) -> float:
    s = seg - seg.mean()
    if np.sqrt(np.mean(s ** 2)) < 1e-4:
        return 0.0
    s = s * np.hanning(len(s))
    ac = np.correlate(s, s, "full")[len(s) - 1:]
    if ac[0] <= 0:
        return 0.0
    lo, hi = int(SR / 380), int(SR / 75)
    hi = min(hi, len(ac) - 1)
    if hi <= lo:
        return 0.0
    lag = lo + int(np.argmax(ac[lo:hi]))
    # 抛物线插值
    if 0 < lag < len(ac) - 1:
        y0, y1, y2 = ac[lag - 1], ac[lag], ac[lag + 1]
        den = y0 - 2 * y1 + y2
        if den != 0:
            lag += 0.5 * (y0 - y2) / den
    return SR / lag if lag > 0 else 0.0


def breathiness(vf: list) -> tuple[float, float, float]:
    """气声三指标：高频/低频能量比(dB)、周期性、谱平坦度。

    耳语的物理特征是声带不完全闭合 → 谐波结构弱、非周期噪声多、
    高频气流占比升高。三者可用来判断"有没有真的变气声"，而不是只看音量。
    """
    win = 1024
    hf, lf, flat, per = [], [], [], []
    f = np.fft.rfftfreq(win, 1 / SR)
    for _, s, _ in vf:
        seg = s[:win]
        if len(seg) < win:
            continue
        p = np.abs(np.fft.rfft(seg * np.hanning(win))) ** 2
        lf.append(p[(f >= 80) & (f < 2000)].sum())
        hf.append(p[(f >= 2000) & (f <= 8000)].sum())
        m = p[(f >= 80) & (f <= 8000)]
        flat.append(float(np.exp(np.log(m + 1e-12).mean()) / (m.mean() + 1e-12)))
        z = seg - seg.mean()
        ac = np.correlate(z, z, "full")[len(z) - 1:]
        lo, hi = int(SR / 380), min(int(SR / 75), len(ac) - 1)
        if hi > lo and ac[0] > 0:
            per.append(float(ac[lo:hi].max() / ac[0]))
    ratio = 10 * np.log10((np.mean(hf) + 1e-12) / (np.mean(lf) + 1e-12)) if hf else 0.0
    return (round(float(ratio), 1),
            round(float(np.median(per)), 3) if per else 0.0,
            round(float(np.mean(flat)), 4) if flat else 0.0)


def band_spectrum(x: np.ndarray, n_bands: int = 24) -> np.ndarray:
    """平均对数频带能量谱，用来粗比音色（不追求精确 MFCC）。"""
    win, hop = 2048, 512
    edges = np.logspace(np.log10(80), np.log10(5000), n_bands + 1)
    freqs = np.fft.rfftfreq(win, 1 / SR)
    acc = np.zeros(n_bands)
    cnt = 0
    for i in range(0, len(x) - win, hop):
        seg = x[i:i + win]
        if np.sqrt(np.mean(seg ** 2)) < 0.004:
            continue
        p = np.abs(np.fft.rfft(seg * np.hanning(win))) ** 2
        for b in range(n_bands):
            m = (freqs >= edges[b]) & (freqs < edges[b + 1])
            acc[b] += p[m].mean() if m.any() else 0.0
        cnt += 1
    if cnt == 0:
        return np.zeros(n_bands)
    return 10 * np.log10(acc / cnt + 1e-12)


def analyze(path: Path, ref_spec: np.ndarray | None = None) -> dict:
    x = read(path)
    frames = list(voiced_frames(x))
    peak = float(np.max(np.abs(x)))
    ethr = max(0.005, peak * 0.045)
    vf = [(i, s, e) for i, s, e in frames if e > ethr]
    if not vf:
        return {"file": path.name, "error": "无有效有声帧"}
    f0s = np.array([f for f in (f0_autocorr(s) for _, s, _ in vf) if 75 <= f <= 380])
    energies = np.array([e for _, _, e in vf])
    hf_db, periodicity, flatness = breathiness(vf)
    t_first, t_last = vf[0][0] / SR, vf[-1][0] / SR + 0.040
    # 尾音走向：最后 25% 有声帧 vs 前 25%
    k = max(1, len(f0s) // 4)
    f0_head = float(np.median(f0s[:k])) if len(f0s) >= k else 0.0
    f0_tail = float(np.median(f0s[-k:])) if len(f0s) >= k else 0.0
    return {
        "file": path.name,
        "total_s": round(len(x) / SR, 3),
        "voiced_s": round(t_last - t_first, 3),
        # 「晚安」固定 2 字，用有效发声时长折算语速，便于横向比较"快/慢"
        "zi_per_s": round(2.0 / max(t_last - t_first, 1e-6), 2),
        "onset_s": round(t_first, 3),
        "f0_median_hz": round(float(np.median(f0s)), 1) if len(f0s) else None,
        "f0_head_hz": round(f0_head, 1),
        "f0_tail_hz": round(f0_tail, 1),
        "f0_tail_minus_head_hz": round(f0_tail - f0_head, 1),
        "rms_db": round(20 * np.log10(max(float(np.sqrt(np.mean(x ** 2))), 1e-9)), 1),
        "voiced_rms_db": round(20 * np.log10(max(float(np.median(energies)), 1e-9)), 1),
        "peak": round(peak, 3),
        "hf_ratio_db": hf_db,
        "periodicity": periodicity,
        "spectral_flatness": flatness,
        "timbre_corr_vs_ref": (
            round(float(np.corrcoef(band_spectrum(x), ref_spec)[0, 1]), 3)
            if ref_spec is not None else None
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--ref", default="", help="参考音色 wav，计算频谱相关系数")
    args = ap.parse_args()
    d = Path(args.dir)
    files = sorted(d.glob("*.wav"))
    ref_spec = band_spectrum(read(Path(args.ref))) if args.ref else None
    rows = [analyze(f, ref_spec) for f in files]
    print(f"{'候选':<26}{'总长':>7}{'有效':>7}{'起始':>7}{'F0中位':>9}{'尾-头':>9}{'RMS':>8}"
          f"{'气声dB':>8}{'周期':>7}{'平坦':>7}{'音色相关':>10}")
    for r in rows:
        if "error" in r:
            print(r["file"], r["error"])
            continue
        corr = "" if r["timbre_corr_vs_ref"] is None else f"{r['timbre_corr_vs_ref']:.3f}"
        print(f"{r['file']:<26}{r['total_s']:>7.2f}{r['voiced_s']:>7.2f}{r['onset_s']:>7.2f}"
              f"{str(r['f0_median_hz']):>9}{r['f0_tail_minus_head_hz']:>9.1f}{r['rms_db']:>8.1f}"
              f"{r.get('hf_ratio_db', 0):>8.1f}{r.get('periodicity', 0):>7.3f}"
              f"{r.get('spectral_flatness', 0):>7.4f}{corr:>10}")
    if args.out:
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print("saved", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
