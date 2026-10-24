# -*- coding: utf-8 -*-
"""分块调用本地 VOSR2，将长视频稳妥放大到 1920x1080。"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

COMFY = "http://127.0.0.1:8188"
COMFY_INPUT = Path(r"F:\Work-Fisher纯净包2026.8.7\ComfyUI\input")
COMFY_OUTPUT = Path(r"F:\Work-Fisher纯净包2026.8.7\ComfyUI\output")


def request_json(path: str, payload: dict | None = None, timeout: int = 60) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        COMFY + path,
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data else "GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_ffmpeg(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


def run_ffprobe(args: list[str]) -> str:
    result = subprocess.run(
        ["ffprobe", "-v", "error", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return result.stdout


def probe_duration(path: Path) -> float:
    output = run_ffprobe(
        [
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    return float(output.strip())


def probe_video(path: Path) -> dict:
    output = run_ffprobe(
        [
            "-show_entries",
            "format=duration,size:stream=index,codec_type,width,height,"
            "r_frame_rate,nb_frames,duration,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ]
    )
    return json.loads(output)


def video_streams(path: Path) -> tuple[dict, dict | None]:
    data = probe_video(path)
    streams = data.get("streams") or []
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if not video:
        raise ValueError(f"{path.name} 缺少视频流")
    return video, audio


def validate_clip(
    path: Path,
    expected_width: int,
    expected_height: int,
    expected_frames: int,
    require_audio: bool = True,
) -> None:
    video, audio = video_streams(path)
    actual_frames = int(video.get("nb_frames") or 0)
    if (video.get("width"), video.get("height")) != (
        expected_width,
        expected_height,
    ):
        raise ValueError(
            f"{path.name} 分辨率错误："
            f"{video.get('width')}x{video.get('height')}"
        )
    if video.get("r_frame_rate") != "30/1":
        raise ValueError(f"{path.name} 帧率错误：{video.get('r_frame_rate')}")
    if actual_frames != expected_frames:
        raise ValueError(f"{path.name} 帧数错误：{actual_frames}，应为 {expected_frames}")
    if require_audio and not audio:
        raise ValueError(f"{path.name} 缺少音轨")


def make_chunk(
    source: Path,
    target: Path,
    start: float,
    duration: float,
    expected_frames: int,
) -> None:
    if target.exists() and target.stat().st_size > 0:
        try:
            validate_clip(target, 960, 544, expected_frames)
            return
        except Exception as exc:
            print(f"  源分块校验失败，将重新切片：{exc}", flush=True)

    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".partial.mp4")
    run_ffmpeg(
        [
            "-ss",
            f"{start:.6f}",
            "-t",
            f"{duration:.6f}",
            "-i",
            str(source),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0?",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "12",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(partial),
        ]
    )
    validate_clip(partial, 960, 544, expected_frames)
    partial.replace(target)


def build_workflow(
    input_name: str,
    prefix: str,
    seed: int,
    frame_rate: float,
    frame_batch: int,
    tile_size: int,
) -> dict:
    return {
        "1": {
            "class_type": "VHS_LoadVideo",
            "inputs": {
                "video": input_name,
                "force_rate": 0,
                "custom_width": 0,
                "custom_height": 0,
                "frame_load_cap": 0,
                "skip_first_frames": 0,
                "select_every_nth": 1,
                "format": "AnimateDiff",
            },
        },
        "2": {
            "class_type": "TESpeedVOSR2Loader",
            "inputs": {
                "model_bundle": "VOSR2",
                "precision": "auto",
                "memory_policy": "resident",
                "torch_compile": False,
                "vae_encode_amp": False,
            },
        },
        "3": {
            "class_type": "TESpeedVOSR2Settings",
            "inputs": {
                "quality_profile": "speed",
                "tile_strategy": "tiled",
                "tile_size": tile_size,
                "tile_overlap": 64,
                "vae_tile_size": 1024,
                "vae_tile_overlap": 32,
                "image_batch": 1,
                "frame_batch": frame_batch,
                "dino_batch": frame_batch,
                "temporal_cache": False,
                "cache_threshold": 0.003,
                "cache_refresh": 4,
                "memory_policy": "resident",
                "color_alignment": "wavelet",
            },
        },
        "4": {
            "class_type": "TESpeedVOSR2Video",
            "inputs": {
                "model": ["2", 0],
                "images": ["1", 0],
                "scale": 2,
                "seed": seed,
                "settings": ["3", 0],
                "frame_batch": frame_batch,
                "temporal_cache": False,
                "cache_threshold": 0.003,
                "cache_refresh": 4,
            },
        },
        "5": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["4", 0],
                "upscale_method": "bicubic",
                "width": 1920,
                "height": 1080,
                "crop": "center",
            },
        },
        "6": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["5", 0],
                "filename_prefix": prefix,
                "format": "video/h264-mp4",
                "pix_fmt": "yuv420p",
                "crf": 16,
                "save_metadata": False,
                "trim_to_audio": True,
                "pingpong": False,
                "save_output": True,
                "frame_rate": frame_rate,
                "loop_count": 0,
                "audio": ["1", 2],
            },
        },
    }


def wait_for_output(prompt_id: str, timeout_seconds: int) -> dict:
    started = time.time()
    while time.time() - started < timeout_seconds:
        time.sleep(15)
        try:
            history = request_json(f"/history/{prompt_id}", timeout=30)
        except Exception as exc:
            print(f"  查询任务状态失败，稍后重试：{exc}", flush=True)
            continue
        if prompt_id not in history:
            elapsed = time.time() - started
            try:
                queue = request_json("/queue", timeout=10)
                running = len(queue.get("queue_running") or [])
                pending = len(queue.get("queue_pending") or [])
            except Exception:
                running = pending = "?"
            print(
                f"  [{elapsed / 60:.1f}min] running={running} pending={pending}",
                flush=True,
            )
            continue

        record = history[prompt_id]
        status = (record.get("status") or {}).get("status_str")
        if status and status != "success":
            detail = json.dumps(record.get("status"), ensure_ascii=False)
            raise RuntimeError(f"VOSR2 任务失败：{detail}")
        return record
    raise TimeoutError(f"VOSR2 任务超时：{prompt_id}")


def find_video_output(record: dict) -> Path:
    for output in (record.get("outputs") or {}).values():
        for item in output.get("gifs") or output.get("videos") or []:
            filename = item.get("filename")
            if not filename:
                continue
            candidate = COMFY_OUTPUT / item.get("subfolder", "") / filename
            if candidate.exists():
                return candidate
    raise FileNotFoundError("历史记录中没有找到 VOSR2 输出视频")


def process_chunk(
    source_chunk: Path,
    upscaled_chunk: Path,
    input_name: str,
    prefix: str,
    seed: int,
    frame_rate: float,
    frame_batch: int,
    tile_size: int,
    timeout_seconds: int,
    expected_frames: int,
) -> None:
    shutil.copy2(source_chunk, COMFY_INPUT / input_name)
    workflow = build_workflow(
        input_name,
        prefix,
        seed,
        frame_rate,
        frame_batch,
        tile_size,
    )
    response = request_json("/prompt", {"prompt": workflow}, timeout=120)
    prompt_id = response.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"提交失败：{response}")
    print(f"  prompt_id={prompt_id}", flush=True)

    record = wait_for_output(prompt_id, timeout_seconds)
    result = find_video_output(record)
    partial = upscaled_chunk.with_suffix(".partial.mp4")
    shutil.copy2(result, partial)
    validate_clip(partial, 1920, 1080, expected_frames)
    partial.replace(upscaled_chunk)


def concat_outputs(parts: list[Path], source: Path, output: Path) -> None:
    list_file = output.parent / f"{output.stem}_concat.txt"
    lines = [f"file '{part.as_posix()}'" for part in parts]
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    video_only = output.parent / f"{output.stem}_video_only.mp4"
    final_partial = output.with_suffix(".partial.mp4")
    run_ffmpeg(
        [
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-map",
            "0:v:0",
            "-an",
            "-c",
            "copy",
            str(video_only),
        ]
    )
    run_ffmpeg(
        [
            "-i",
            str(video_only),
            "-i",
            str(source),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0?",
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(final_partial),
        ]
    )
    expected_frames = sum(
        int(video_streams(part)[0]["nb_frames"]) for part in parts
    )
    validate_clip(final_partial, 1920, 1080, expected_frames)
    final_partial.replace(output)
    video_only.unlink(missing_ok=True)


def write_progress(work_dir: Path, payload: dict) -> None:
    target = work_dir / "progress.json"
    partial = target.with_suffix(".partial.json")
    partial.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    partial.replace(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--chunk-seconds", type=float, default=15.0)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--max-chunks", type=int, default=0, help="0 表示处理到结尾")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--concat", action="store_true")
    parser.add_argument("--seed", type=int, default=45)
    parser.add_argument("--frame-rate", type=float, default=30.0)
    parser.add_argument("--frame-batch", type=int, default=1)
    parser.add_argument("--tile-size", type=int, default=1024)
    parser.add_argument("--timeout-minutes", type=int, default=180)
    parser.add_argument("--overwrite-output", action="store_true")
    args = parser.parse_args()

    source = Path(args.input).resolve()
    output = Path(args.output).resolve()
    work_dir = Path(args.work_dir).resolve()
    source_chunks = work_dir / f"source_{args.chunk_seconds:g}s"
    upscaled_chunks = work_dir / f"vosr2_{args.chunk_seconds:g}s_1920x1080"
    source_chunks.mkdir(parents=True, exist_ok=True)
    upscaled_chunks.mkdir(parents=True, exist_ok=True)
    COMFY_INPUT.mkdir(parents=True, exist_ok=True)
    COMFY_OUTPUT.mkdir(parents=True, exist_ok=True)

    if output.exists() and not args.overwrite_output:
        raise FileExistsError(f"最终文件已存在，未覆盖：{output}")

    total_duration = probe_duration(source)
    source_video, _ = video_streams(source)
    total_frames = int(source_video.get("nb_frames") or 0)
    frames_per_chunk = round(args.chunk_seconds * args.frame_rate)
    total_chunks = math.ceil(total_frames / frames_per_chunk)
    end_index = (
        total_chunks
        if args.max_chunks == 0
        else min(total_chunks, args.start_index + args.max_chunks)
    )
    job_id = hashlib.sha1(str(source).encode("utf-8")).hexdigest()[:8]
    prefix_root = f"codex_vosr2/{source.stem}_{job_id}"

    print(
        f"输入 {source.name} · {total_duration:.3f}s · 共 {total_chunks} 块 · "
        f"处理 {args.start_index}-{end_index - 1} · 每块 {args.chunk_seconds:g}s",
        flush=True,
    )

    completed: list[Path] = []
    for index in range(args.start_index, end_index):
        started = time.time()
        start = index * args.chunk_seconds
        duration = min(args.chunk_seconds, total_duration - start)
        expected_frames = min(
            frames_per_chunk,
            total_frames - index * frames_per_chunk,
        )
        source_chunk = source_chunks / f"part_{index:02d}.mp4"
        upscaled_chunk = upscaled_chunks / f"part_{index:02d}.mp4"
        print(
            f"\n=== 第 {index + 1}/{total_chunks} 块 · "
            f"{start:.2f}s 起 · {duration:.2f}s · {expected_frames} 帧 ===",
            flush=True,
        )

        if args.resume and upscaled_chunk.exists() and upscaled_chunk.stat().st_size > 0:
            try:
                validate_clip(upscaled_chunk, 1920, 1080, expected_frames)
            except Exception as exc:
                print(f"  已有分块校验失败，将重新生成：{exc}", flush=True)
            else:
                print("  已有完成文件，跳过", flush=True)
                completed.append(upscaled_chunk)
                continue

        make_chunk(source, source_chunk, start, duration, expected_frames)
        input_name = f"codex_vosr2_{job_id}_{index:02d}.mp4"
        process_chunk(
            source_chunk,
            upscaled_chunk,
            input_name,
            f"{prefix_root}/part_{index:02d}",
            args.seed + index,
            args.frame_rate,
            args.frame_batch,
            args.tile_size,
            args.timeout_minutes * 60,
            expected_frames,
        )
        completed.append(upscaled_chunk)
        elapsed = time.time() - started
        print(
            f"  已完成 · {elapsed / 60:.1f}min · "
            f"{upscaled_chunk.stat().st_size} bytes",
            flush=True,
        )
        write_progress(
            work_dir,
            {
                "source": str(source),
                "output": str(output),
                "chunk_seconds": args.chunk_seconds,
                "total_chunks": total_chunks,
                "completed_chunks": index + 1,
                "last_chunk": upscaled_chunk.name,
                "last_elapsed_seconds": round(elapsed, 1),
                "tile_size": args.tile_size,
                "frame_batch": args.frame_batch,
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

    if args.concat:
        if args.start_index != 0 or end_index != total_chunks:
            raise ValueError("只有完整处理全部块后才能拼接")
        parts = [
            upscaled_chunks / f"part_{index:02d}.mp4"
            for index in range(total_chunks)
        ]
        for part in parts:
            if part not in completed:
                raise FileNotFoundError(f"缺少分块：{part}")
        output.parent.mkdir(parents=True, exist_ok=True)
        concat_outputs(parts, source, output)
        print(f"最终视频：{output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
