#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 MOSS-TTS 有声小说 JSON 提取片段，生成 Index-TTS2 样本 JSON。

Index-TTS2 JSON 字段：
    - type: narration / dialogue
    - character: 角色名（旁白为 null）
    - text: 待合成文本
    - reference_audio: 参考音频文件名（相对于 reference_dir）
"""

import json
import argparse
from pathlib import Path
from typing import Any


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


def build_index_tts2_json(
    source_json: Path,
    indices: list[int],
    reference_dir: str,
    silence_seconds: float,
    description: str,
) -> dict[str, Any]:
    data = json.loads(source_json.read_text(encoding="utf-8"))
    lines = data["chapters"][0]["lines"]

    segments = []
    for i in indices:
        line = lines[i]
        char = line.get("character")
        ref = DEFAULT_VOICE_MAP.get(char or "旁白", "旁白.wav")
        segments.append({
            "type": line["type"],
            "character": char,
            "text": line["content"].strip(),
            "reference_audio": ref,
        })

    return {
        "title": data.get("title", "红绳"),
        "chapter": data["chapters"][0].get("chapter_title", ""),
        "description": description,
        "reference_dir": reference_dir,
        "silence_seconds": silence_seconds,
        "segments": segments,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path, help="MOSS-TTS JSON 源文件")
    parser.add_argument("--indices", required=True, help="片段行号，如 68-83")
    parser.add_argument("--output", required=True, type=Path, help="输出 Index-TTS2 JSON")
    parser.add_argument("--reference-dir", default="../参考音色", help="参考音频相对目录（默认相对 JSON 所在目录）")
    parser.add_argument("--silence", type=float, default=0.25, help="段落间静音秒数")
    parser.add_argument("--description", default="", help="片段说明")
    args = parser.parse_args()

    start, end = (int(x) for x in args.indices.split("-", 1))
    indices = list(range(start, end + 1))

    desc = args.description or f"片段：第{start}-{end}行，含对话与旁白"
    result = build_index_tts2_json(
        args.source, indices, args.reference_dir, args.silence, desc
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成 {args.output}，共 {len(indices)} 段")


if __name__ == "__main__":
    main()
