# -*- coding: utf-8 -*-
"""提交 EP04 片段11d4系列到 RunningHub 金鱼云端。"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

RUNNINGHUB_SCRIPTS = Path(r"C:\Users\Administrator\.codex\skills\runninghub\scripts")
sys.path.insert(0, str(RUNNINGHUB_SCRIPTS))

from runninghub import download_file, fix_mov_to_mp4, poll_task, require_api_key  # noqa: E402
from runninghub_app import apply_modifications, get_node_info, submit_task  # noqa: E402

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
SEG_DIR = ROOT / "05-workflow" / "ep04" / "红绳片段11d4_世界的代价"
OLD_SEG_DIR = ROOT / "05-workflow" / "ep04" / "审讯线_新剧情_10c后_20261020"
REF_DIR = OLD_SEG_DIR / "参考图"
OUT_DIR = SEG_DIR / "视频草稿"

APP_ID = "2093984226331938818"
IMAGE_SLOTS = ("51", "49", "50", "43")
AUDIO_SLOT = "48"

LAOHAN = REF_DIR / "老韩_正脸.png"
INTERROGATION = ROOT / "05-images" / "场景" / "场景_ND审问室_日漫v3.png"
ND_GATE = ROOT / "05-images" / "场景" / "场景_ND东郊分部大门_薄暮_日漫电影感.png"
LAOHAN_VOICE = ROOT / "05-workflow" / "归档素材" / "人物参考音色" / "老韩.wav"
D3_EXIT = REF_DIR / "11d3_末帧.png"

SEGMENTS = OrderedDict(
    [
        (
            "11d4a",
            {
                "title": "世界的代价",
                "prompt": SEG_DIR / "11d4a_世界的代价_H3纯提示词.txt",
                "images": [LAOHAN, ND_GATE, INTERROGATION, D3_EXIT],
                "audios": [LAOHAN_VOICE],
            },
        ),
        (
            "11d4b",
            {
                "title": "帮助我们找到他",
                "prompt": SEG_DIR / "11d4b_帮助我们找到他_H3纯提示词.txt",
                "images": [LAOHAN, INTERROGATION, REF_DIR / "11d4a_末帧.png"],
                "audios": [LAOHAN_VOICE],
            },
        ),
    ]
)


def validate_prompt(prompt: str, image_count: int, audio_count: int) -> None:
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

    pictures = {int(v) for v in re.findall(r"<Picture (\d+)>", prompt)}
    subjects = {int(v) for v in re.findall(r"<Subject (\d+)>", prompt)}
    audios = {int(v) for v in re.findall(r"<Audio (\d+)>", prompt)}
    if pictures != set(range(1, image_count + 1)):
        raise ValueError(f"Picture 标签不一致：{sorted(pictures)} / {image_count}")
    if not subjects or subjects != set(range(1, max(subjects) + 1)):
        raise ValueError(f"Subject 标签编号不连续：{sorted(subjects)}")
    if audios != set(range(1, audio_count + 1)):
        raise ValueError(f"Audio 标签不一致：{sorted(audios)} / {audio_count}")


def run_ffmpeg_frame(video: Path, image: Path) -> None:
    image.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
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
        ],
        check=True,
    )


def normalize_for_phone(video: Path) -> None:
    temp = video.with_suffix(".phone.mp4")
    subprocess.run(
        [
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
        ],
        check=True,
    )
    temp.replace(video)


def probe_media(video: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(video),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def run_segment(api_key: str, seg_id: str, conf: dict, suffix: str = "") -> Path:
    prompt_path = Path(conf["prompt"])
    images = [Path(path) for path in conf["images"]]
    audios = [Path(path) for path in conf["audios"]]
    missing = [path for path in (prompt_path, *images, *audios) if not path.exists()]
    if missing:
        raise FileNotFoundError("\n".join(str(path) for path in missing))

    prompt = prompt_path.read_text(encoding="utf-8").strip()
    validate_prompt(prompt, len(images), len(audios))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUT_DIR / f"E04-{seg_id}_{conf['title']}{suffix}_未审核草稿.mp4"
    exit_frame = REF_DIR / f"{seg_id}_末帧{suffix}.png"

    node_args = [
        f"263:text={prompt}",
        "252:aspect_ratio=16:9 (Widescreen)",
        "252:megapixels=0.5",
        "259:value=15",
        "283:value=1",
    ]
    file_args = [
        f"{IMAGE_SLOTS[index]}:image={image}" for index, image in enumerate(images)
    ]
    file_args.append(f"{AUDIO_SLOT}:audio={audios[0]}")

    print(
        f"\n=== {seg_id} {conf['title']} ===\n"
        f"提示词 {len(prompt)} 字 · 参考图 {len(images)} 张 · 音频 {len(audios)} 条"
        " · 15秒 · 0.5MP",
        flush=True,
    )
    for index, image in enumerate(images, start=1):
        print(f"  @图片{index} -> {image.name}", flush=True)
    print(f"  <Audio 1> -> {audios[0].name}", flush=True)

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
    url = media_results[0].get("url") or media_results[0].get("outputUrl")
    download_file(url, str(output))
    fix_mov_to_mp4(str(output))
    normalize_for_phone(output)
    run_ffmpeg_frame(output, exit_frame)

    metadata = probe_media(output)
    videos = [s for s in metadata["streams"] if s["codec_type"] == "video"]
    audios_out = [s for s in metadata["streams"] if s["codec_type"] == "audio"]
    duration = float(metadata["format"]["duration"])
    usage = final.get("usage") or {}
    print(
        f"已保存 {output} · {duration:.2f}s · "
        f"{videos[0].get('width')}x{videos[0].get('height')} · "
        f"{len(audios_out)} 条音轨 · {usage}",
        flush=True,
    )

    receipt = {
        "segment": seg_id,
        "taskId": task_id,
        "status": final.get("status"),
        "usage": usage,
        "prompt": str(prompt_path),
        "images": [str(path) for path in images],
        "audios": [str(path) for path in audios],
        "saved": str(output),
        "exitFrame": str(exit_frame),
        "duration": duration,
        "size": [videos[0].get("width"), videos[0].get("height")],
        "audioStreams": len(audios_out),
    }
    (SEG_DIR / f"RH任务回执_{seg_id}{suffix}.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--segments",
        nargs="+",
        choices=list(SEGMENTS),
        default=list(SEGMENTS),
        help="要提交的片段编号",
    )
    parser.add_argument("--suffix", default="", help="输出和末帧文件名后缀")
    args = parser.parse_args()
    api_key = require_api_key(os.environ.get("RUNNINGHUB_API_KEY"))
    for seg_id in args.segments:
        run_segment(api_key, seg_id, SEGMENTS[seg_id], args.suffix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
