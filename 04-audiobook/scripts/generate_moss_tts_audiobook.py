#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
红绳有声书 - MOSS-TTS 多角色有声书生成脚本

使用 MOSS-TTS-Local-Transformer-v1.5，基于 JSON 有声剧本生成多角色音频。
支持 zero-shot 音色克隆、连续同角色自动合并、参考音频自动裁剪。

运行环境：
    激活 D:\HermesWorkspace\MOSS-TTS\.venv 后执行：
        cd D:\HermesWorkspace\ai小说\红绳\04-audiobook
        python scripts\generate_moss_tts_audiobook.py

如果 huggingface.co 访问困难，可设置镜像：
        set HF_ENDPOINT=https://hf-mirror.com
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Optional

import torch
import torchaudio
from transformers import AutoModel, AutoProcessor

# ---------------------------------------------------------------------------
# 默认配置（可通过命令行覆盖）
# ---------------------------------------------------------------------------
DEFAULT_PROJECT_ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳\04-audiobook")
DEFAULT_CHAPTER_DIR = DEFAULT_PROJECT_ROOT / "ch01_红绳伞"
DEFAULT_MODEL_DIR = Path(r"D:\HermesWorkspace\models\MOSS-TTS-Local-Transformer-v1.5")
DEFAULT_REF_DIR = DEFAULT_PROJECT_ROOT / "参考音色"

# 角色 -> 参考音频文件名
# 注：第一章高中时代使用“青年林晓/青年林明”，后续章节可按时间线切换。
DEFAULT_VOICE_MAP: dict[str, str] = {
    "旁白": "旁白.wav",
    "林明": "青年林明.wav",
    "林晓": "青年林晓.wav",
    "李想": "李想.wav",
    "王老师": "王老师.wav",
    "李老师": "李老师.wav",
    "陈小雨": "陈小雨.wav",
    "妈妈": "妈妈.wav",
    "周芳": "周芳.wav",
    "小学林明": "小学林明.wav",
    "小学林晓": "小学林晓.wav",
}

DEFAULT_FALLBACK_VOICE = "旁白"
DEFAULT_MAX_REF_SECONDS = 12.0
DEFAULT_SILENCE_SECONDS = 0.25
DEFAULT_MAX_GROUP_CHARS = 180  # 单段生成文本上限，超过则按句切分


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def setup_torch() -> None:
    """禁用有问题的 cuDNN SDPA backend，启用备选后端。"""
    torch.backends.cuda.enable_cudnn_sdp(False)
    torch.backends.cuda.enable_flash_sdp(True)
    torch.backends.cuda.enable_mem_efficient_sdp(True)
    torch.backends.cuda.enable_math_sdp(True)


def resolve_attn_implementation(device: torch.device, dtype: torch.dtype) -> str:
    import importlib.util

    if (
        device.type == "cuda"
        and importlib.util.find_spec("flash_attn") is not None
        and dtype in {torch.float16, torch.bfloat16}
    ):
        major, _ = torch.cuda.get_device_capability()
        if major >= 8:
            return "flash_attention_2"
    if device.type == "cuda":
        return "sdpa"
    return "eager"


def discover_script_json(chapter_dir: Path) -> Path:
    """在章节目录中自动查找 *_有声小说.json。"""
    candidates = list(chapter_dir.glob("*_有声小说.json"))
    if not candidates:
        raise FileNotFoundError(f"在 {chapter_dir} 中未找到 *_有声小说.json")
    if len(candidates) > 1:
        print(f"[WARN] 找到多个剧本文件，将使用第一个: {candidates[0]}")
    return candidates[0]


def load_script(json_path: Path, selected_indices: Optional[list[int]] = None) -> list[dict]:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    lines = data["chapters"][0]["lines"]
    if selected_indices is not None:
        lines = [lines[i] for i in selected_indices if 0 <= i < len(lines)]
    return lines


def split_text_at_boundaries(text: str, max_chars: int) -> list[str]:
    """按句末标点将长文本切分成多个较短的片段。"""
    if len(text) <= max_chars:
        return [text]
    # 优先在句号、问号、感叹号、换行处切分
    splits = re.split(r"([。！？\n])", text)
    parts: list[str] = []
    current = ""
    for i in range(0, len(splits) - 1, 2):
        sentence = splits[i] + (splits[i + 1] if i + 1 < len(splits) else "")
        if len(current) + len(sentence) > max_chars and current:
            parts.append(current.strip())
            current = sentence
        else:
            current += sentence
    if current.strip():
        parts.append(current.strip())
    if not parts:
        parts = [text]
    return parts


def group_consecutive_lines(lines: list[dict], max_chars: int = DEFAULT_MAX_GROUP_CHARS) -> list[tuple[str, str]]:
    """合并同一角色的连续台词；若合并后过长则按句切分。"""
    groups: list[tuple[str, str]] = []
    for line in lines:
        char = line.get("character") or DEFAULT_FALLBACK_VOICE
        content = str(line.get("content", "")).strip()
        if not content:
            continue
        if groups and groups[-1][0] == char:
            merged = groups[-1][1] + "\n" + content
            if len(merged) > max_chars:
                # 把当前组按句切分后再追加
                chunks = split_text_at_boundaries(groups[-1][1], max_chars)
                groups[-1] = (char, chunks[0])
                groups.extend((char, c) for c in chunks[1:])
                groups.append((char, content))
            else:
                groups[-1] = (char, merged)
        else:
            groups.append((char, content))

    # 最后再过一遍，确保没有超长组
    final: list[tuple[str, str]] = []
    for char, text in groups:
        if len(text) > max_chars:
            final.extend((char, c) for c in split_text_at_boundaries(text, max_chars))
        else:
            final.append((char, text))
    return final


def load_reference_codes(
    processor,
    ref_dir: Path,
    voice_map: dict[str, str],
    max_seconds: float = DEFAULT_MAX_REF_SECONDS,
) -> dict[str, torch.Tensor]:
    """预编码所有参考音色，并裁剪过长片段。"""
    target_sr = int(processor.model_config.sampling_rate)
    n_vq = int(processor.model_config.n_vq)
    codes_map: dict[str, torch.Tensor] = {}

    for char, filename in voice_map.items():
        path = ref_dir / filename
        if not path.exists():
            print(f"[WARN] 参考音频缺失，跳过: {path}")
            continue

        wav, sr = torchaudio.load(str(path))
        if wav.shape[0] > 1:
            wav = wav.mean(dim=0, keepdim=True)
        if int(sr) != target_sr:
            wav = torchaudio.functional.resample(wav, int(sr), target_sr)

        max_samples = int(target_sr * max_seconds)
        if wav.shape[-1] > max_samples:
            wav = wav[:, :max_samples]

        encoded = processor.encode_audios_from_wav([wav], sampling_rate=target_sr, n_vq=n_vq)
        codes_map[char] = encoded[0]
        print(f"[INFO] 参考音色 [{char}] -> {filename}: {encoded[0].shape[0]} frames")

    if DEFAULT_FALLBACK_VOICE not in codes_map:
        raise RuntimeError(f"缺少默认 fallback 参考音色: {DEFAULT_FALLBACK_VOICE}")

    return codes_map


def estimate_max_new_tokens(text: str) -> int:
    """粗略估算所需音频 token 数（中文约 3 token/字），上限 4096。"""
    zh_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    other_chars = len(text) - zh_chars
    tokens = int(zh_chars * 3.1 + other_chars * 0.9 + 200)
    return min(max(tokens, 256), 4096)


def save_mp3_with_ffmpeg(wav_path: Path, mp3_path: Path) -> bool:
    """如果系统有 ffmpeg，把 wav 转成 128kbps mp3。"""
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


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="红绳有声书 - MOSS-TTS 多角色生成")
    parser.add_argument("--chapter-dir", type=Path, default=DEFAULT_CHAPTER_DIR,
                        help="章节目录，包含 *_有声小说.json")
    parser.add_argument("--json", type=Path, default=None,
                        help="显式指定剧本 JSON 路径")
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR,
                        help="MOSS-TTS-Local-Transformer-v1.5 模型目录")
    parser.add_argument("--ref-dir", type=Path, default=DEFAULT_REF_DIR,
                        help="参考音色目录")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="输出目录，默认与章节目录相同")
    parser.add_argument("--output-name", type=str, default=None,
                        help="输出文件名前缀，默认 红绳_第XX章_moss_tts")
    parser.add_argument("--indices", type=str, default="all",
                        help="要生成的行号，如 '0,1,2,5-10'，默认 all（完整章节）")
    parser.add_argument("--max-ref-sec", type=float, default=DEFAULT_MAX_REF_SECONDS,
                        help="参考音频最长使用前几秒")
    parser.add_argument("--silence", type=float, default=DEFAULT_SILENCE_SECONDS,
                        help="段落间静音时长（秒）")
    parser.add_argument("--max-group-chars", type=int, default=DEFAULT_MAX_GROUP_CHARS,
                        help="同角色合并后的最大字数")
    parser.add_argument("--no-mp3", action="store_true",
                        help="不生成 MP3")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu",
                        help="计算设备")
    parser.add_argument("--dtype", type=str, default="bfloat16", choices=["bfloat16", "float16", "float32"],
                        help="模型精度")
    return parser.parse_args()


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


def main() -> None:
    args = parse_args()
    setup_torch()

    chapter_dir = args.chapter_dir.resolve()
    json_path = args.json.resolve() if args.json else discover_script_json(chapter_dir)
    output_dir = (args.output_dir.resolve() if args.output_dir else chapter_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 输出文件名
    if args.output_name:
        stem = args.output_name
    else:
        stem = chapter_dir.name.replace("ch", "第").replace("_", "") + "_moss_tts"
        # 尝试从 JSON 文件名提取“第XX章”
        m = re.search(r"第(\d+)[章回]", json_path.stem)
        if m:
            stem = f"红绳_第{int(m.group(1)):02d}章_moss_tts"

    out_wav = output_dir / f"{stem}.wav"
    out_meta = output_dir / f"{stem}_meta.json"
    segments_dir = output_dir / f"{stem}_segments"
    segments_dir.mkdir(exist_ok=True)

    device = torch.device(args.device)
    dtype = getattr(torch, args.dtype)
    print(f"[INFO] 设备: {device}, 精度: {dtype}")
    print(f"[INFO] 剧本: {json_path}")
    print(f"[INFO] 输出: {output_dir}")

    selected_indices = parse_indices(args.indices)
    lines = load_script(json_path, selected_indices)
    groups = group_consecutive_lines(lines, max_chars=args.max_group_chars)
    print(f"[INFO] 共 {len(lines)} 行台词 -> 合并为 {len(groups)} 个生成组")

    print("[INFO] 加载 Processor...")
    processor = AutoProcessor.from_pretrained(
        str(args.model_dir),
        trust_remote_code=True,
    )
    if hasattr(processor, "audio_tokenizer"):
        processor.audio_tokenizer = processor.audio_tokenizer.to(device)

    print("[INFO] 预编码参考音色...")
    ref_codes = load_reference_codes(processor, args.ref_dir, DEFAULT_VOICE_MAP, max_seconds=args.max_ref_sec)

    print("[INFO] 加载 TTS 模型...")
    attn_impl = resolve_attn_implementation(device, dtype)
    print(f"[INFO] Attention: {attn_impl}")
    model = AutoModel.from_pretrained(
        str(args.model_dir),
        trust_remote_code=True,
        torch_dtype=dtype,
        attn_implementation=attn_impl,
    ).to(device)
    model.eval()
    print(f"[INFO] 模型已加载，显存占用: {torch.cuda.memory_allocated()/1e9:.2f} GB")

    sample_rate = int(processor.model_config.sampling_rate)
    silence = torch.zeros(2, int(sample_rate * args.silence), dtype=torch.float32)
    final_audio: list[torch.Tensor] = []
    generated_segments: list[dict[str, Any]] = []

    start_time = time.time()
    with torch.no_grad():
        for idx, (char, text) in enumerate(groups):
            codes = ref_codes[char] if char in ref_codes else ref_codes[DEFAULT_FALLBACK_VOICE]
            print(f"[{idx + 1}/{len(groups)}] [{char}] {text.replace(chr(10), ' ')[:60]}{'...' if len(text) > 60 else ''}")

            user_msg = processor.build_user_message(
                text=text,
                reference=[codes],
                language="Chinese",
            )
            batch = processor([[user_msg]], mode="generation")
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            outputs = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=estimate_max_new_tokens(text),
                do_sample=True,
                audio_temperature=1.7,
                audio_top_p=0.8,
                audio_top_k=25,
                audio_repetition_penalty=1.0,
            )

            messages = list(processor.decode(outputs))
            audio = messages[0].audio_codes_list[0]
            if audio.ndim == 1:
                audio = audio.unsqueeze(0)
            audio = audio.detach().cpu().to(torch.float32)
            if audio.shape[0] == 1:
                audio = audio.repeat(2, 1)

            # 保存单段
            seg_path = segments_dir / f"{idx:04d}_{char}.wav"
            torchaudio.save(str(seg_path), audio, sample_rate)

            final_audio.append(audio)
            final_audio.append(silence.clone())

            generated_segments.append({
                "index": idx,
                "character": char,
                "text": text,
                "reference": DEFAULT_VOICE_MAP.get(char, DEFAULT_VOICE_MAP[DEFAULT_FALLBACK_VOICE]),
                "segment_path": str(seg_path),
                "samples": audio.shape[-1],
                "duration_seconds": round(audio.shape[-1] / sample_rate, 3),
            })

    if final_audio and final_audio[-1].abs().max() == 0:
        final_audio.pop()
    full_waveform = torch.cat(final_audio, dim=-1)
    torchaudio.save(str(out_wav), full_waveform, sample_rate)
    elapsed = time.time() - start_time

    # 生成 MP3
    mp3_ok = False
    if not args.no_mp3:
        mp3_path = out_wav.with_suffix(".mp3")
        mp3_ok = save_mp3_with_ffmpeg(out_wav, mp3_path)

    meta = {
        "model": str(args.model_dir),
        "json_source": str(json_path),
        "reference_dir": str(args.ref_dir),
        "voice_map": DEFAULT_VOICE_MAP,
        "selected_indices": selected_indices,
        "sample_rate": sample_rate,
        "total_samples": full_waveform.shape[-1],
        "total_duration_seconds": round(full_waveform.shape[-1] / sample_rate, 3),
        "generation_elapsed_seconds": round(elapsed, 2),
        "segments": generated_segments,
    }
    with out_meta.open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n[DONE] 合并音频: {out_wav}")
    print(f"[DONE] 总时长: {meta['total_duration_seconds']}s | 生成耗时: {meta['generation_elapsed_seconds']}s")
    if mp3_ok:
        print(f"[DONE] MP3: {out_wav.with_suffix('.mp3')}")
    print(f"[DONE] 元数据: {out_meta}")
    print(f"[DONE] 分段文件: {segments_dir}")


if __name__ == "__main__":
    main()
