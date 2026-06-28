#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
红绳有声书 - Index-TTS2 多角色有声书生成脚本

读取 MOSS-TTS 格式的 JSON 剧本，用 Index-TTS2 逐段/逐角色合成，
最后合并为完整 MP3/WAV。

依赖：
    F:\ComfyUI_V6.0\Index-tts-2.0-Windows-NVIDIA 下的 env/python.exe
    并设置 PYTHONPATH 到 Index-TTS2 根目录。

示例：
    cd F:\ComfyUI_V6.0\Index-tts-2.0-Windows-NVIDIA
    set PYTHONPATH=F:\ComfyUI_V6.0\Index-tts-2.0-Windows-NVIDIA
    env\python.exe D:\HermesWorkspace\ai小说\红绳\04-audiobook\scripts\generate_index_tts2_audiobook.py \
        --json D:\HermesWorkspace\ai小说\红绳\04-audiobook\ch01_红绳伞\红绳_第01章_有声小说.json \
        --model-dir F:\ComfyUI_V6.0\Index-tts-2.0-Windows-NVIDIA\checkpoints \
        --output D:\HermesWorkspace\ai小说\红绳\04-audiobook\ch01_红绳伞\红绳_第01章_index_tts2.mp3
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

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
        print("[ERROR] 未找到 index-tts 包。请使用 Index-TTS2 自带的 Python 环境，")
        print("        并设置 PYTHONPATH 到 Index-TTS2 根目录。")
        raise e


# 角色 -> 参考音频文件名（相对于参考音色目录）
DEFAULT_VOICE_MAP = {
    "旁白": "旁白.wav",
    "林明": "青年林明.wav",
    "林晓": "青年林晓.wav",
    "李想": "李想.wav",
    "王老师": "王老师.wav",
    "李老师": "李老师.wav",
    "陈老师": "李老师.wav",
    "陈小雨": "陈小雨.wav",
    "妈妈": "妈妈.wav",
    "周芳": "周芳.wav",
}
DEFAULT_FALLBACK_VOICE = "旁白"
DEFAULT_SILENCE_SECONDS = 0.25
DEFAULT_MAX_GROUP_CHARS = 240  # 合并连续同角色时的最大字数


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


def group_consecutive_lines(
    lines: list[dict],
    voice_map: dict[str, str],
    fallback: str,
    max_chars: int = DEFAULT_MAX_GROUP_CHARS,
) -> list[tuple[str, str, dict]]:
    """
    合并连续同角色/同类型的台词，减少 Index-TTS2 调用次数。
    返回 [(character_or_type, text, original_line), ...]。
    """
    def resolve_key(line: dict) -> str:
        return line.get("character") or fallback

    groups: list[tuple[str, str, dict]] = []
    for line in lines:
        key = resolve_key(line)
        text = str(line.get("content", "")).strip()
        if not text:
            continue
        if groups and groups[-1][0] == key:
            merged = groups[-1][1] + "\n" + text
            if len(merged) > max_chars:
                # 当前组已经够长，另起新组
                groups.append((key, text, line))
            else:
                groups[-1] = (key, merged, groups[-1][2])
        else:
            groups.append((key, text, line))
    return groups


def parse_indices(spec: str) -> Optional[list[int]]:
    if spec.strip().lower() == "all":
        return None
    indices: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            indices.update(range(int(a), int(b) + 1))
        elif part:
            indices.add(int(part))
    return sorted(indices)


def main():
    parser = argparse.ArgumentParser(description="红绳有声书 - Index-TTS2 完整章节生成")
    parser.add_argument("--json", "-j", required=True, type=Path, help="MOSS-TTS 格式 JSON 剧本")
    parser.add_argument("--model-dir", "-m", required=True, type=Path, help="Index-TTS2 checkpoints 目录")
    parser.add_argument("--cfg", default="config.yaml", help="模型配置文件名")
    parser.add_argument("--ref-dir", "-r", type=Path, default=None, help="参考音色目录（默认与 JSON 同级的 ../参考音色）")
    parser.add_argument("--output", "-o", type=Path, default=None, help="输出文件，默认与 JSON 同名 .wav/.mp3")
    parser.add_argument("--indices", default="all", help="要生成的行号，如 0-99 或 0,1,5-10")
    parser.add_argument("--silence", type=float, default=DEFAULT_SILENCE_SECONDS, help="段间静音秒数")
    parser.add_argument("--max-group-chars", type=int, default=DEFAULT_MAX_GROUP_CHARS, help="合并同角色最大字数")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--fp16", action="store_true", help="使用 FP16 推理")
    parser.add_argument("--no-mp3", action="store_true", help="不生成 MP3")
    parser.add_argument("--keep-wav", action="store_true", help="保留中间 WAV")
    parser.add_argument(
        "--narration-emo-text",
        default="成熟稳重，深夜电台风格，温暖低沉，娓娓道来，带有轻微忧郁感",
        help="旁白段落的情感文本提示（留空则关闭情感控制）",
    )
    args = parser.parse_args()

    IndexTTS2 = import_index_tts()

    data: dict[str, Any] = json.loads(args.json.read_text(encoding="utf-8"))
    lines = data["chapters"][0]["lines"]

    selected = parse_indices(args.indices)
    if selected is not None:
        lines = [lines[i] for i in selected if 0 <= i < len(lines)]

    ref_dir = args.ref_dir
    if ref_dir is None:
        ref_dir = (args.json.parent / "../参考音色").resolve()
    else:
        ref_dir = ref_dir.resolve()

    if args.output is None:
        args.output = args.json.with_name(args.json.stem.replace("_有声小说", "") + "_index_tts2.wav")
    out_wav = args.output.with_suffix(".wav")
    out_mp3 = args.output.with_suffix(".mp3")
    out_meta = out_wav.with_suffix(".meta.json")
    segments_dir = out_wav.parent / f"{out_wav.stem}_segments"
    segments_dir.mkdir(parents=True, exist_ok=True)

    cfg_path = args.model_dir / args.cfg
    if not cfg_path.exists():
        raise FileNotFoundError(f"未找到配置文件: {cfg_path}")

    print(f"[INFO] 加载 Index-TTS2: {args.model_dir}")
    tts = IndexTTS2(
        cfg_path=str(cfg_path),
        model_dir=str(args.model_dir),
        use_fp16=args.fp16,
        device=args.device,
        use_cuda_kernel=False,
        use_deepspeed=False,
    )

    groups = group_consecutive_lines(lines, DEFAULT_VOICE_MAP, DEFAULT_FALLBACK_VOICE, args.max_group_chars)
    print(f"[INFO] 共 {len(lines)} 行 -> 合并为 {len(groups)} 个生成组")

    sample_rate: Optional[int] = None
    silence: Optional[torch.Tensor] = None
    final_audio: list[torch.Tensor] = []
    generated_segments: list[dict[str, Any]] = []

    for idx, (char_key, text, original_line) in enumerate(groups, 1):
        ref_file = DEFAULT_VOICE_MAP.get(char_key, DEFAULT_VOICE_MAP[DEFAULT_FALLBACK_VOICE])
        ref_path = ref_dir / ref_file
        if not ref_path.exists():
            print(f"[WARN] 参考音频缺失: {ref_path}，使用 fallback 旁白")
            ref_path = ref_dir / DEFAULT_VOICE_MAP[DEFAULT_FALLBACK_VOICE]

        is_narration = original_line.get("type") == "narration"
        char_display = original_line.get("character") or "旁白"
        print(f"[{idx}/{len(groups)}] [{char_display}] {text.replace(chr(10), ' ')[:60]}{'...' if len(text) > 60 else ''}")

        seg_path = segments_dir / f"{idx:04d}_{char_display}.wav"

        infer_kwargs: dict[str, Any] = {
            "spk_audio_prompt": str(ref_path),
            "text": text,
            "output_path": str(seg_path),
        }
        if is_narration and args.narration_emo_text:
            infer_kwargs["use_emo_text"] = True
            infer_kwargs["emo_text"] = args.narration_emo_text
            print(f"       -> 旁白情感: {args.narration_emo_text}")

        tts.infer(**infer_kwargs)

        wav, sr = torchaudio.load(str(seg_path))
        if wav.shape[0] > 1:
            wav = wav.mean(dim=0, keepdim=True)
        if sample_rate is None:
            sample_rate = int(sr)
            silence = torch.zeros(1, int(sample_rate * args.silence), dtype=torch.float32)
        elif int(sr) != sample_rate:
            wav = torchaudio.functional.resample(wav, int(sr), sample_rate)

        final_audio.append(wav)
        if silence is not None:
            final_audio.append(silence.clone())

        generated_segments.append({
            "index": idx,
            "character": char_display,
            "type": original_line.get("type"),
            "text": text,
            "reference_audio": str(ref_path),
            "segment_path": str(seg_path),
            "samples": wav.shape[-1],
            "duration_seconds": round(wav.shape[-1] / sample_rate, 3),
        })

    if final_audio and final_audio[-1].abs().max() == 0:
        final_audio.pop()

    full = torch.cat(final_audio, dim=-1)
    if full.shape[0] == 1:
        full = full.repeat(2, 1)
    torchaudio.save(str(out_wav), full, sample_rate or 48000)
    total_seconds = full.shape[-1] / (sample_rate or 48000)
    print(f"\n[DONE] WAV: {out_wav} | 总时长: {total_seconds:.1f}s")

    mp3_ok = False
    if not args.no_mp3:
        mp3_ok = save_mp3_with_ffmpeg(out_wav, out_mp3)
        if mp3_ok and not args.keep_wav:
            out_wav.unlink()
            print(f"[DONE] MP3: {out_mp3}")

    meta = {
        "model": str(args.model_dir),
        "json_source": str(args.json),
        "reference_dir": str(ref_dir),
        "voice_map": DEFAULT_VOICE_MAP,
        "selected_indices": selected,
        "sample_rate": sample_rate,
        "total_samples": full.shape[-1],
        "total_duration_seconds": round(total_seconds, 3),
        "narration_emo_text": args.narration_emo_text,
        "segments": generated_segments,
    }
    out_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DONE] 元数据: {out_meta}")
    print(f"[DONE] 分段文件: {segments_dir}")


if __name__ == "__main__":
    main()
