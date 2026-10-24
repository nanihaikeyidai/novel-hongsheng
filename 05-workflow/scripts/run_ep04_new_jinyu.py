# -*- coding: utf-8 -*-
"""按新审讯对白连续提交 RunningHub 金鱼 AI 应用。"""
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
SEG_DIR = ROOT / "05-workflow" / "ep04" / "审讯线_新剧情_10c后_20261020"
REF_DIR = SEG_DIR / "参考图"
OUT_DIR = SEG_DIR / "视频草稿"
QA_DIR = SEG_DIR / "QA"

APP_ID = "2093984226331938818"
IMAGE_SLOTS = ("51", "49", "50", "43")
AUDIO_SLOTS = ("48", "14")

LUCHEN = REF_DIR / "陆沉_正脸.png"
LAOHAN = REF_DIR / "老韩_正脸.png"
SCENE = ROOT / "05-images" / "场景" / "场景_ND审问室_日漫v3.png"
VOICE_DIR = ROOT / "05-workflow" / "归档素材" / "人物参考音色"
LUCHEN_VOICE = VOICE_DIR / "陆沉.wav"
LAOHAN_VOICE = VOICE_DIR / "老韩.wav"

SEGMENTS = OrderedDict(
    [
        (
            "11c",
            {
                "title": "赤瞳",
                "prompt": REF_DIR.parent / "11c_赤瞳_H3纯提示词.txt",
                "exit_ref": REF_DIR / "11b_末帧.png",
                "audios": [LAOHAN_VOICE],
            },
        ),
        (
            "11c2",
            {
                "title": "母亲死因",
                "prompt": REF_DIR.parent / "11c2_母亲死因_H3纯提示词.txt",
                "exit_ref": REF_DIR / "11c_末帧.png",
                "audios": [LUCHEN_VOICE, LAOHAN_VOICE],
            },
        ),
        (
            "11d",
            {
                "title": "交易",
                "prompt": REF_DIR.parent / "11d_交易_H3纯提示词.txt",
                "exit_ref": REF_DIR / "11c2_末帧.png",
                "audios": [LAOHAN_VOICE],
            },
        ),
        (
            "11d2",
            {
                "title": "凭什么相信",
                "prompt": REF_DIR.parent / "11d2_凭什么相信_H3纯提示词.txt",
                "exit_ref": REF_DIR / "11d_末帧.png",
                "audios": [LUCHEN_VOICE, LAOHAN_VOICE],
            },
        ),
        (
            "11e",
            {
                "title": "门外",
                "prompt": REF_DIR.parent / "11e_门外_H3纯提示词.txt",
                "exit_ref": REF_DIR / "11d2_末帧.png",
                "audios": [LAOHAN_VOICE],
            },
        ),
    ]
)


def validate_prompt(prompt: str, audio_count: int) -> None:
    labels = [
        "subject_definitions:",
        "summary:",
        "retention_analysis:",
        "detailed_description:",
        "overall_soundscape:",
        "non_diegetic_music:",
    ]
    positions = [prompt.find(label) for label in labels]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        raise ValueError("H3 六段结构缺失或顺序错误")
    if not prompt.startswith("subject_definitions:"):
        raise ValueError("主提示词未从 subject_definitions: 开始")
    declared_audio = {int(value) for value in re.findall(r"<Audio (\d+)>", prompt)}
    if declared_audio != set(range(1, audio_count + 1)):
        raise ValueError(
            f"音频标签不一致：声明 {sorted(declared_audio)}，绑定 {audio_count} 条"
        )
    if re.search(r"\(S\d+\)\s*<d>", prompt):
        raise ValueError("检测到重复说话人标签")
    references = set(re.findall(r"<(?:Subject|Picture|Audio) (\d+)>", prompt))
    for kind in ("Subject", "Picture", "Audio"):
        declared = {int(value) for value in re.findall(rf"<{kind} (\d+)>", prompt)}
        missing = {value for value in declared if not re.search(rf"<{kind} {value}>", prompt)}
        if not declared:
            continue
        expected = set(range(1, max(declared) + 1))
        if declared != expected:
            raise ValueError(f"{kind} 标签编号不连续：{sorted(declared)}")
    if not references:
        raise ValueError("提示词没有引用标签")


def extract_last_frame(video: Path, image: Path) -> None:
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


def normalize_for_phone(video: Path) -> Path:
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
    return video


def run_segment(api_key: str, seg_id: str, conf: dict, suffix: str = "") -> Path:
    prompt_path = Path(conf["prompt"])
    exit_ref = Path(conf["exit_ref"])
    previous_segment = {
        "11c2": "11c",
        "11d": "11c2",
        "11d2": "11d",
        "11e": "11d2",
    }.get(seg_id)
    if suffix and previous_segment:
        previous_exit = REF_DIR / f"{previous_segment}_末帧{suffix}.png"
        if previous_exit.exists():
            exit_ref = previous_exit
    audios = [Path(path) for path in conf["audios"]]
    images = [LUCHEN, LAOHAN, SCENE, exit_ref]

    missing = [path for path in [prompt_path, *images, *audios] if not path.exists()]
    if missing:
        raise FileNotFoundError("\n".join(str(path) for path in missing))

    prompt = prompt_path.read_text(encoding="utf-8").strip()
    validate_prompt(prompt, len(audios))

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
        f"{IMAGE_SLOTS[index]}:image={image}"
        for index, image in enumerate(images)
    ]
    file_args += [
        f"{AUDIO_SLOTS[index]}:audio={audio}"
        for index, audio in enumerate(audios)
    ]

    print(
        f"\n=== {seg_id} {conf['title']} ===\n"
        f"提示词 {len(prompt)} 字 · 参考图 {len(images)} 张 · 音频 {len(audios)} 条"
        f" · 15秒 · 0.5MP",
        flush=True,
    )
    for index, image in enumerate(images, start=1):
        print(f"  @图片{index} -> {image.name}", flush=True)
    for index, audio in enumerate(audios, start=1):
        print(f"  <Audio {index}> -> {audio.name}", flush=True)

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
    if not results:
        raise RuntimeError("任务完成但未返回文件")

    usage = final.get("usage") or {}
    print(f"状态: {final.get('status')} · 消耗: {usage}", flush=True)
    media_results = [item for item in results if item.get("url") or item.get("outputUrl")]
    if not media_results:
        raise RuntimeError("任务结果中没有媒体文件")

    url = media_results[0].get("url") or media_results[0].get("outputUrl")
    download_file(url, str(output))
    fix_mov_to_mp4(str(output))
    normalize_for_phone(output)
    extract_last_frame(output, exit_frame)

    metadata = probe_media(output)
    audio_streams = [s for s in metadata.get("streams", []) if s.get("codec_type") == "audio"]
    video_streams = [s for s in metadata.get("streams", []) if s.get("codec_type") == "video"]
    duration = float(metadata.get("format", {}).get("duration", 0))
    print(
        f"已保存 {output.name} · {duration:.2f}s · "
        f"{video_streams[0].get('width')}x{video_streams[0].get('height')} · "
        f"{len(audio_streams)} 条音轨",
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
        "saved": [str(output)],
        "exitFrame": str(exit_frame),
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
        help="要提交的片段编号；默认提交全部",
    )
    parser.add_argument("--suffix", default="", help="输出和末帧文件名后缀")
    args = parser.parse_args()

    api_key = require_api_key(os.environ.get("RUNNINGHUB_API_KEY"))
    for seg_id in args.segments:
        run_segment(api_key, seg_id, SEGMENTS[seg_id], args.suffix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
