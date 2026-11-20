#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""S04 v12 后期修音：根治金鱼乱序重复台词，出拳后零人声。

问题：金鱼 v10 音轨 ASR 三段乱序重复（0.6-7.8「让我看看你变强了没有」/
7.8-12.1「安娜好久不见」/12.1-14.1 又一遍），出拳(8.5s)后仍在说话。
用户 2026-11-19：「男主出拳后，应该马上被踢飞，不应该继续说话」。方案同 v10：台词贴回台词特写期 4-8s，出拳后零人声。

方案（画面完全不动，0 视频积分）：
  1) demucs 消 v12 全部人声 → 环境音底（保留电光/踢击/撞柱/窒息音效）
  2) 干净台词 A_cold_smirk.wav（3.95s）贴到台词特写期 4.0s 起 → 7.95s 结束
     —— 台词在出拳(8.5s)前说完，出拳后全程零人声
  3) numpy 直接混音（不用 pydub gain，避免历史 0.02x 静音坑）
  4) ffmpeg 合成回画面：48kHz AAC + faststart
  5) faster-whisper 复核：应仅 1 段台词且 <8.5s

用法：python postfix_ep06_s04_v12_audio.py
"""
from __future__ import annotations

import subprocess
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
SEG = ROOT / "05-workflow" / "ep06" / "全本批量_梅林"
SRC = SEG / "视频草稿" / "EP06_S04_v12_金鱼_正面台词两步出拳踢胸口.mp4"
LINE = ROOT / "05-workflow" / "重配音实验室" / "cases" / "S04_蓝隼好久不见" / "候选音频" / "A_cold_smirk.wav"
OUT = SEG / "视频草稿" / "EP06_S04_v12_金鱼_修音_出拳后无人声.mp4"
TMP = SEG / "视频草稿" / "_v12_postfix"

LINE_START = 4.0      # 台词特写 Shot 2 起点（s）
LINE_GAIN_DB = -2.0   # 台词略降 2dB（源 -16.3dB → 目标接近主推成片 -20.2dB）


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def main():
    if not SRC.exists():
        raise SystemExit(f"源视频不存在: {SRC}")
    if not LINE.exists():
        raise SystemExit(f"台词源不存在: {LINE}")
    TMP.mkdir(parents=True, exist_ok=True)

    # 1) 提音轨（demucs CLI 读 mp4 报 torchcodec DLL，必须先提 WAV）
    wav = TMP / "audio.wav"
    print("[1/5] 提音轨...", flush=True)
    r = run(["ffmpeg", "-y", "-i", str(SRC), "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", str(wav)])
    if r.returncode != 0:
        raise RuntimeError("提音轨失败: " + r.stderr[-500:])

    # 2) demucs 消人声 → 环境音底
    nv = TMP / "no_vocals.wav"
    print("[2/5] demucs 消人声（保留环境音）...", flush=True)
    import numpy as np
    import soundfile as sf
    import torch
    from demucs.pretrained import get_model
    from demucs.apply import apply_model

    model = get_model("htdemucs")
    model.eval()
    sr = model.samplerate
    data, fsr = sf.read(str(wav), dtype="float32")
    if data.ndim == 1:
        data = data[None, :]
    else:
        data = data.T
    with torch.no_grad():
        sources = apply_model(model, torch.tensor(data[None, ...]), device="cpu", progress=False)[0].numpy()
    names = list(model.sources)
    nvwav = sum(sources[names.index(n)] for n in ("other", "drums", "bass"))
    sf.write(str(nv), nvwav.T, sr)
    print(f"  no_vocals 写出 sr={sr} shape={nvwav.shape}", flush=True)

    # 3) numpy 混音：环境音底 + 干净台词贴到 LINE_START
    print("[3/5] 叠加干净台词...", flush=True)
    bed, bed_sr = sf.read(str(nv), dtype="float32")
    if bed.ndim == 1:
        bed = np.stack([bed, bed], axis=1)
    line, line_sr = sf.read(str(LINE), dtype="float32")
    if line.ndim == 1:
        line = np.stack([line, line], axis=1)
    if line_sr != bed_sr:
        # 重采样台词到环境音底采样率（线性插值，够用）
        n = int(len(line) * bed_sr / line_sr)
        line = np.interp(
            np.linspace(0, len(line) - 1, n), np.arange(len(line)), line[:, 0]
        )
        line = np.stack([line, line], axis=1)
    # demucs 在开头瞬移段残留一声「呵呵」(0.62-1.62s)，局部渐隐压掉——
    # 该段本应只有电光音效，压掉不留空档（电光音效本身在该段有能量）。
    MUTE_A, MUTE_B = 0.4, 2.0
    fade = int(0.15 * bed_sr)
    a, b = int(MUTE_A * bed_sr), int(MUTE_B * bed_sr)
    bed[a:a + fade] *= __import__("numpy").linspace(1, 0, fade)[:, None]
    bed[b - fade:b] *= __import__("numpy").linspace(0, 1, fade)[:, None]
    bed[a + fade:b - fade] = 0.0

    gain = 10 ** (LINE_GAIN_DB / 20.0)
    line = line * gain
    start = int(LINE_START * bed_sr)
    end = min(start + len(line), len(bed))
    mix = bed.copy()
    mix[start:end, :] += line[: end - start, :]
    # 限幅防削顶
    peak = float(np.max(np.abs(mix)))
    if peak > 0.99:
        mix = mix * (0.99 / peak)
    mixed = TMP / "mixed.wav"
    sf.write(str(mixed), mix, bed_sr)
    print(f"  台词区间 {LINE_START:.1f}-{end/bed_sr:.2f}s ({(end-start)/bed_sr:.2f}s) gain={gain:.3f} peak={peak:.3f}", flush=True)

    # 4) 合成回画面
    print("[4/5] 合成回画面...", flush=True)
    r = run([
        "ffmpeg", "-y", "-i", str(SRC), "-i", str(mixed),
        "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0",
        "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "128k",
        "-shortest", "-movflags", "+faststart", str(OUT),
    ])
    if r.returncode != 0:
        raise RuntimeError("ffmpeg 合成失败: " + r.stderr[-500:])
    print(f"  已输出 {OUT.name} ({OUT.stat().st_size//1024} KB)", flush=True)

    # 5) ASR 复核
    print("[5/5] ASR 复核...", flush=True)
    from faster_whisper import WhisperModel
    cache = Path.home() / ".cache" / "huggingface" / "hub" / "models--Systran--faster-whisper-small" / "snapshots"
    snaps = sorted(x for x in cache.iterdir() if x.is_dir()) if cache.exists() else []
    m = WhisperModel(str(snaps[-1]) if snaps else "small", device="cpu", compute_type="int8")
    segs, info = m.transcribe(str(OUT), beam_size=5, vad_filter=True, language="zh")
    speech = [s for s in segs if s.text.strip()]
    print(f"  lang={info.language} 台词段={len(speech)}")
    for s in speech:
        print(f"    [{s.start:.2f}-{s.end:.2f}] {s.text.strip()}")
    late = [s for s in speech if s.start >= 8.5]
    print("结果:", "✅ 出拳后零人声" if not late else f"⚠️ 出拳后仍有 {len(late)} 段")
    print("完成:", OUT, flush=True)


if __name__ == "__main__":
    main()
