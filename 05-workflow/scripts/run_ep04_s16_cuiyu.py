# -*- coding: utf-8 -*-
"""提交 EP04 片段16 翠羽社汇报到 RunningHub 金鱼 AI 应用。"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

RUNNINGHUB_SCRIPTS = Path(r"C:\Users\Administrator\.codex\skills\runninghub\scripts")
sys.path.insert(0, str(RUNNINGHUB_SCRIPTS))

from runninghub import download_file, fix_mov_to_mp4, poll_task, require_api_key  # noqa: E402
from runninghub_app import apply_modifications, get_node_info, submit_task  # noqa: E402

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
APP_ID = "2093984226331938818"
SEG_DIR = ROOT / "05-workflow" / "ep04" / "红绳片段16_翠羽社汇报"
PROMPT = SEG_DIR / "动作流_H3纯提示词.txt"
OUTPUT = SEG_DIR / "视频草稿" / "E04-16_翠羽社汇报_未审核草稿.mp4"

ANNA = ROOT / "05-workflow" / "归档素材" / "人物" / "安娜_人设.png"
RESTER = ROOT / "05-workflow" / "归档素材" / "人物" / "雷斯特_人设.png"
SCENE = ROOT / "05-images" / "场景" / "场景_翠羽社大厅_日漫电影感.png"
FIRST_FRAME = SEG_DIR / "首帧图.png"
ANNA_VOICE = ROOT / "人物参考音色" / "安娜.wav"

IMAGE_SLOTS = ("51", "49", "50", "43", "19", "23")
AUDIO_SLOTS = ("48", "14", "15")
IMAGES = (ANNA, RESTER, SCENE, FIRST_FRAME)
AUDIOS = (ANNA_VOICE,)


def validate_prompt(prompt: str) -> None:
    labels = (
        "subject_definitions:",
        "summary:",
        "retention_analysis:",
        "detailed_description:",
        "overall_soundscape:",
        "non_diegetic_music:",
    )
    positions = [prompt.find(label) for label in labels]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        raise ValueError("H3 六段结构缺失或顺序错误")
    if not prompt.startswith("subject_definitions:"):
        raise ValueError("主提示词未从 subject_definitions: 开始")
    if re.search(r"\(S\d+\)\s*<d>", prompt):
        raise ValueError("检测到重复说话人标签")
    audio_ids = {int(value) for value in re.findall(r"<Audio (\d+)>", prompt)}
    if audio_ids != set(range(1, len(AUDIOS) + 1)):
        raise ValueError(f"音频标签不一致：{sorted(audio_ids)}")
    if len(re.findall(r"<d>\[Chinese\]", prompt)) != 1:
        raise ValueError("当前片段应只有一条中文对白事件")


def probe_media(video: Path) -> dict:
    result = subprocess.run(
        (
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(video),
        ),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def normalize_for_phone(video: Path) -> None:
    temp = video.with_suffix(".phone.mp4")
    subprocess.run(
        (
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(video),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(temp),
        ),
        check=True,
    )
    temp.replace(video)


def extract_last_frame(video: Path, image: Path) -> None:
    subprocess.run(
        (
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-sseof",
            "-0.25",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-update",
            "1",
            str(image),
        ),
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suffix", default="", help="输出文件名后缀")
    args = parser.parse_args()

    missing = [path for path in (PROMPT, *IMAGES, *AUDIOS) if not path.exists()]
    if missing:
        print("缺失文件:", *(str(path) for path in missing), sep="\n  ")
        return 1

    prompt = PROMPT.read_text(encoding="utf-8").strip()
    validate_prompt(prompt)
    api_key = require_api_key(os.environ.get("RUNNINGHUB_API_KEY"))

    node_args = (
        f"263:text={prompt}",
        "252:aspect_ratio=16:9 (Widescreen)",
        "252:megapixels=0.5",
        "259:value=15",
        "283:value=1",
    )
    file_args = [
        f"{IMAGE_SLOTS[index]}:image={path}" for index, path in enumerate(IMAGES)
    ]
    file_args += [
        f"{AUDIO_SLOTS[index]}:audio={path}" for index, path in enumerate(AUDIOS)
    ]

    print(
        f"\n=== EP04 片段16 翠羽社汇报 ===\n"
        f"提示词 {len(prompt)} 字 · 参考图 {len(IMAGES)} 张 · 音频 {len(AUDIOS)} 条"
        f" · 15秒 · 0.5MP · 16:9",
        flush=True,
    )
    for index, path in enumerate(IMAGES, start=1):
        print(f"  @图片{index} -> {path.name}", flush=True)
    for index, path in enumerate(AUDIOS, start=1):
        print(f"  <Audio {index}> -> {path.name}", flush=True)

    nodes = apply_modifications(
        api_key,
        get_node_info(api_key, APP_ID),
        node_args,
        file_args,
    )
    data = submit_task(api_key, APP_ID, nodes)
    task_id = str(data["taskId"])
    print(f"taskId = {task_id}", flush=True)

    final = poll_task(api_key, task_id)
    results = final.get("results") or []
    media_results = [
        item for item in results if item.get("url") or item.get("outputUrl")
    ]
    if not media_results:
        raise RuntimeError("任务完成但没有媒体结果")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    output = OUTPUT.with_name(f"{OUTPUT.stem}{args.suffix}{OUTPUT.suffix}")
    url = media_results[0].get("url") or media_results[0].get("outputUrl")
    download_file(url, str(output))
    fix_mov_to_mp4(str(output))
    normalize_for_phone(output)

    exit_frame = SEG_DIR / f"末帧图{args.suffix}.png"
    extract_last_frame(output, exit_frame)
    metadata = probe_media(output)
    video = next(
        stream for stream in metadata["streams"] if stream["codec_type"] == "video"
    )
    audio = [
        stream for stream in metadata["streams"] if stream["codec_type"] == "audio"
    ]
    duration = float(metadata["format"]["duration"])
    usage = final.get("usage") or {}

    print(
        f"已保存 {output} · {duration:.2f}s · "
        f"{video.get('width')}x{video.get('height')} · {len(audio)} 条音轨 · {usage}",
        flush=True,
    )
    receipt = {
        "segment": "16",
        "taskId": task_id,
        "status": final.get("status"),
        "usage": usage,
        "prompt": str(PROMPT),
        "images": [str(path) for path in IMAGES],
        "audios": [str(path) for path in AUDIOS],
        "saved": str(output),
        "exitFrame": str(exit_frame),
        "duration": duration,
        "size": [video.get("width"), video.get("height")],
        "audioStreams": len(audio),
    }
    (SEG_DIR / f"RH任务回执{args.suffix}.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
