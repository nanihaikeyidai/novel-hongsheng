#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""本地梅林出片：demucs AI 消人声（根治自生成音轨乱说话/日语）。

配方（2026-11-18 验证成功）：
  1) ffmpeg 提音轨为 WAV（demucs CLI 读 mp4 会报 libtorchcodec DLL 缺失，必须走 WAV）
  2) demucs Python API 分离（soundfile 读 numpy 喂模型，完全不碰 torchcodec CLI）
  3) no_vocals = other + drums + bass；写回 WAV
  4) ffmpeg 合成回画面（48kHz AAC + faststart）
  5) faster-whisper 复核 ASR 应为 0 段

用法：
  python remove_vocals.py --input 成片.mp4 [--out 成片_无人声.mp4] [--check]
不传 --out 时输出为 <输入名>_无人声.mp4 同目录。
"""
import argparse
import subprocess
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def extract_wav(src: Path, wav: Path):
    r = run(["ffmpeg", "-y", "-i", str(src), "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", str(wav)])
    if r.returncode != 0:
        raise RuntimeError("ffmpeg 提音轨失败: " + r.stderr[-500:])
    print("  [1/4] 音轨已提取:", wav.name)


def separate(wav: Path, no_vocals: Path, vocals: Path):
    import numpy as np
    import soundfile as sf
    import torch
    from demucs.pretrained import get_model
    from demucs.apply import apply_model

    model = get_model("htdemucs")
    model.eval()
    sr = model.samplerate
    data, file_sr = sf.read(str(wav), dtype="float32")
    if data.ndim == 1:
        data = data[None, :]
    else:
        data = data.T
    tensor = torch.tensor(data[None, ...])
    with torch.no_grad():
        sources = apply_model(model, tensor, device="cpu", progress=False)
    sources = sources[0].numpy()
    names = list(model.sources)
    nv = sum(sources[names.index(n)] for n in ("other", "drums", "bass"))
    vo = sources[names.index("vocals")]
    sf.write(str(no_vocals), nv.T, sr)
    sf.write(str(vocals), vo.T, sr)
    print("  [2/4] demucs 分离完成: no_vocals + vocals")


def mux(src: Path, no_vocals: Path, out: Path):
    r = run([
        "ffmpeg", "-y", "-i", str(src), "-i", str(no_vocals),
        "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0",
        "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "128k",
        "-shortest", "-movflags", "+faststart", str(out),
    ])
    if r.returncode != 0:
        raise RuntimeError("ffmpeg 合成失败: " + r.stderr[-500:])
    print("  [3/4] 已合成回画面:", out.name)


def check_asr(out: Path):
    from pathlib import Path as P
    from faster_whisper import WhisperModel
    cache = P.home() / ".cache" / "huggingface" / "hub" / "models--Systran--faster-whisper-small" / "snapshots"
    snaps = sorted(x for x in cache.iterdir() if x.is_dir()) if cache.exists() else []
    m = WhisperModel(str(snaps[-1]) if snaps else "small", device="cpu", compute_type="int8")
    segs, info = m.transcribe(str(out), beam_size=5, vad_filter=True)
    speech = [s for s in segs if s.text.strip()]
    print(f"  [4/4] ASR 复核: lang={info.language} 有文本段={len(speech)}")
    for s in speech[:8]:
        print(f"        {s.start:.1f}-{s.end:.1f} {s.text!r}")
    return len(speech)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="待消人声的 mp4")
    ap.add_argument("--out", default=None, help="输出 mp4（默认 <名>_无人声.mp4）")
    ap.add_argument("--check", action="store_true", help="跑完做 ASR 复核")
    a = ap.parse_args()

    src = Path(a.input).resolve()
    if not src.exists():
        sys.exit("输入不存在: " + str(src))
    out = Path(a.out).resolve() if a.out else src.with_name(src.stem + "_无人声.mp4")
    tmp = src.parent / ("_" + src.stem + "_voc")
    tmp.mkdir(exist_ok=True)

    print("消人声:", src.name, "->", out.name)
    wav = tmp / "audio.wav"
    nv = tmp / "no_vocals.wav"
    vo = tmp / "vocals.wav"
    extract_wav(src, wav)
    separate(wav, nv, vo)
    mux(src, nv, out)
    if a.check:
        n = check_asr(out)
        print("结果:", "✅ 零说话" if n == 0 else f"⚠️ 仍有 {n} 段说话")
    print("完成:", out)


if __name__ == "__main__":
    main()
