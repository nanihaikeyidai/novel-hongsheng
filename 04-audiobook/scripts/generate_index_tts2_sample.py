#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于 Index-TTS2 JSON 片段生成对比音频。

依赖：
    pip install index-tts          # 或从源码安装 https://github.com/index-tts/index-tts
    下载 Index-TTS2 权重到 --model-dir

用法示例：
    python scripts/generate_index_tts2_sample.py \
        --json ch01_红绳伞/红绳_第01章_index_tts2_sample.json \
        --model-dir D:/HermesWorkspace/models/index-tts2 \
        --output ch01_红绳伞/红绳_第01章_index_tts2_sample.wav
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import torch
    import torchaudio
except ImportError as e:  # pragma: no cover
    raise ImportError("请先安装 torch / torchaudio") from e


def import_index_tts():
    try:
        from indextts.infer_v2 import IndexTTS2  # type: ignore
        return IndexTTS2
    except ImportError as e:
        print("[ERROR] 未找到 index-tts 包。请先安装：")
        print("        pip install index-tts")
        print("    或参考 https://github.com/index-tts/index-tts 从源码安装。")
        raise e


def save_mp3_with_ffmpeg(wav_path: Path, mp3_path: Path) -> bool:
    if shutil.which("ffmpeg") is None:
        return False
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-y",
                "-i", str(wav_path),
                "-ar", "48000",
                "-ac", "2",
                "-b:a", "128k",
                str(mp3_path),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except Exception as e:
        print(f"[WARN] MP3 转换失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Index-TTS2 片段生成")
    parser.add_argument("--json", "-j", required=True, type=Path, help="Index-TTS2 JSON 路径")
    parser.add_argument("--model-dir", "-m", required=True, type=Path, help="Index-TTS2 模型目录")
    parser.add_argument("--cfg", default="config.yaml", help="模型配置文件名")
    parser.add_argument("--output", "-o", type=Path, default=None, help="输出 WAV/MP3 路径")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--fp16", action="store_true", help="使用 FP16 推理")
    parser.add_argument("--keep-wav", action="store_true", help="保留 WAV 不转 MP3")
    args = parser.parse_args()

    IndexTTS2 = import_index_tts()

    data: dict[str, Any] = json.loads(args.json.read_text(encoding="utf-8"))
    segments = data["segments"]
    ref_dir = args.json.parent / data.get("reference_dir", "参考音色")
    silence_sec = float(data.get("silence_seconds", 0.25))

    if args.output is None:
        args.output = args.json.with_suffix(".wav")
    out_wav = args.output.with_suffix(".wav")
    out_mp3 = args.output.with_suffix(".mp3")

    cfg_path = args.model_dir / args.cfg
    if not cfg_path.exists():
        raise FileNotFoundError(f"未找到配置文件: {cfg_path}")

    print(f"[INFO] 加载 Index-TTS2: {args.model_dir}")
    tts = IndexTTS2(
        cfg_path=str(cfg_path),
        model_dir=str(args.model_dir),
        use_fp16=args.fp16,
        use_cuda_kernel=False,
        use_deepspeed=False,
    )

    sample_rate: int | None = None
    final_audio: list[torch.Tensor] = []
    silence: torch.Tensor | None = None

    for idx, seg in enumerate(segments, 1):
        ref_audio = ref_dir / seg["reference_audio"]
        text = seg["text"].strip()
        char = seg.get("character") or "旁白"
        print(f"[{idx}/{len(segments)}] [{char}] {text[:50]}{'...' if len(text) > 50 else ''}")

        seg_wav = out_wav.parent / f"{out_wav.stem}_seg{idx:02d}.wav"
        tts.infer(
            spk_audio_prompt=str(ref_audio),
            text=text,
            output_path=str(seg_wav),
        )

        wav, sr = torchaudio.load(str(seg_wav))
        if wav.shape[0] > 1:
            wav = wav.mean(dim=0, keepdim=True)
        if sample_rate is None:
            sample_rate = int(sr)
            silence = torch.zeros(1, int(sample_rate * silence_sec))
        elif int(sr) != sample_rate:
            wav = torchaudio.functional.resample(wav, int(sr), sample_rate)

        final_audio.append(wav)
        if silence is not None:
            final_audio.append(silence.clone())

    if final_audio and final_audio[-1].abs().max() == 0:
        final_audio.pop()

    full = torch.cat(final_audio, dim=-1)
    if full.shape[0] == 1:
        full = full.repeat(2, 1)
    torchaudio.save(str(out_wav), full, sample_rate or 48000)
    print(f"[DONE] WAV: {out_wav} | 时长: {full.shape[-1] / (sample_rate or 48000):.1f}s")

    if not args.keep_wav:
        if save_mp3_with_ffmpeg(out_wav, out_mp3):
            out_wav.unlink()
            print(f"[DONE] MP3: {out_mp3}")


if __name__ == "__main__":
    main()
