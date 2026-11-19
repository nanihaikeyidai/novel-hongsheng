# -*- coding: utf-8 -*-
"""EP05 P04a v2 重制｜03→04 衔接插入段｜RunningHub 云端金鱼 Ref2VA 提交。

触发：2026-11-07 David「剪辑归档出现问题，`片段04_P04a_金鱼草稿.mp4` 是废稿，
和归档视频的前后对不上，重新生成这一段，参考归档视频，03 到 04，这一段插入在中间注意衔接」。

依据 David 规则 §一.17：用户已在需求里明说「重新生成」，视为该次已确认，
本脚本**只提交 1 次**，出片后不自动迭代第二版。闸门 P04A_CONFIRMED=1 仅用于防误触。

衔接锚：
  入点 image3 = `ep05/视频归档/P03_金鱼草稿.mp4` 末帧（近黑三屏命令行暗室，安娜椅后）
  出点 image4 = `ep05/视频归档/P04b_兼容.mp4` 首帧（蓝椅、开放抽屉、双屏、立式机箱）
  两端均截自归档成片，100% 同画风域（避坑手册 L 型）。

参考槽位：image1=51 安娜 / image2=49 沈默 / image3=50 P03末帧 / image4=43 P04b首帧
         audio1=48 沈默音色
应用：2110357037929558018（YZ金鱼 H3 Ref2VA Plus）
规格：16:9 / 15s / 1.5MP / simple / 12 步 → 1664×928
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

RUNNINGHUB_SCRIPTS = Path(r"C:\Users\Administrator\.codex\skills\runninghub\scripts")
sys.path.insert(0, str(RUNNINGHUB_SCRIPTS))

import subprocess as _sp  # noqa: E402

_orig_run = _sp.run


def _utf8_run(*args, **kwargs):
    if kwargs.get("text") or kwargs.get("universal_newlines"):
        kwargs.setdefault("encoding", "utf-8")
        kwargs.setdefault("errors", "replace")
    return _orig_run(*args, **kwargs)


_sp.run = _utf8_run

from runninghub import download_file, fix_mov_to_mp4, poll_task, require_api_key  # noqa: E402
from runninghub_app import apply_modifications, get_node_info, submit_task  # noqa: E402

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
APP_ID = "2110357037929558018"
SEG = ROOT / "05-workflow" / "ep05" / "营救陆沉" / "红绳片段04"
PACK = SEG / "上传包_relink"

PROMPT = SEG / "金鱼_H3纯提示词_P04a_v2.txt"
REFS = [
    PACK / "image1_anna.png",
    PACK / "image2_shenmo.png",
    PACK / "image3_P03_lastframe_anime.jpg",
    PACK / "image4_P04b_firstframe_anime.jpg",
]
AUDIOS = [PACK / "audio1_shenmo.wav"]
IMAGE_NODES = ("51", "49", "50", "43")
AUDIO_NODES = ("48",)
OUT = SEG / "视频草稿" / "片段04_P04a_金鱼草稿_v2_衔接版.mp4"

LINE = "里面有个手机和我复制的ND门禁卡，连上耳机听指挥就行。"


def main() -> int:
    if os.environ.get("P04A_CONFIRMED") != "1":
        raise SystemExit(
            "P04a v2: 未获确认，拒绝提交视频生成（约 379-425 币）。"
            "确认后请设 P04A_CONFIRMED=1 再运行本脚本。"
        )
    api_key = require_api_key(os.environ.get("RH_API_KEY") or os.environ.get("RUNNINGHUB_API_KEY"))

    prompt = PROMPT.read_text(encoding="utf-8").strip()
    labels = [
        "subject_definitions:",
        "summary:",
        "retention_analysis:",
        "detailed_description:",
        "overall_soundscape:",
        "non_diegetic_music:",
    ]
    pos = [prompt.find(l) for l in labels]
    if any(i < 0 for i in pos) or pos != sorted(pos) or not prompt.startswith("subject_definitions:"):
        raise ValueError("P04a: H3 gate failed (6 labels order)")
    if len(prompt.encode("utf-8")) > 5000:
        raise ValueError(f"P04a: prompt too long {len(prompt.encode('utf-8'))} bytes")
    declared = len(set(re.findall(r"<Audio (\d+)>", prompt)))
    if declared != len(AUDIOS):
        raise ValueError(f"P04a: audio mismatch prompt={declared} bound={len(AUDIOS)}")
    pics = set(re.findall(r"<Picture (\d+)>", prompt))
    if pics != {str(i + 1) for i in range(len(REFS))}:
        raise ValueError(f"P04a: picture mismatch prompt={pics} bound={len(REFS)}")
    if prompt.count(LINE) != 1:
        raise ValueError("P04a: dialogue line must appear exactly once")
    # 防止误用旧废稿 / 相邻段落台词
    for stale in ("你这手机有追踪功能", "五十米内的异能者都能找到", "距离这么近"):
        if stale in prompt:
            raise ValueError(f"P04a: stale dialogue from adjacent clip: {stale}")
    for hard in ("LAST FRAME", "FIRST FRAME", "face never the subject", "blue-black hair"):
        if hard not in prompt:
            raise ValueError(f"P04a: missing hard lock: {hard}")
    for f in REFS + AUDIOS:
        if not f.exists():
            raise FileNotFoundError(f"P04a: missing asset {f}")

    node_args = [
        f"263:text={prompt}",
        "252:aspect_ratio=16:9 (Widescreen)",
        "252:megapixels=1.5",
        "259:value=15",
        "261:scheduler=simple",
        "261:steps=12",
    ]
    file_args = [f"{IMAGE_NODES[i]}:image={REFS[i]}" for i in range(len(REFS))]
    file_args += [f"{AUDIO_NODES[i]}:audio={AUDIOS[i]}" for i in range(len(AUDIOS))]

    print(
        f"=== P04a v2 重制·03→04衔接 | 金鱼 {APP_ID} | "
        f"{len(prompt.encode('utf-8'))} bytes | 15s | 1.5MP ===",
        flush=True,
    )
    for i, r in enumerate(REFS):
        print(f"  image{i+1} node {IMAGE_NODES[i]} -> {r.name}", flush=True)
    for i, a in enumerate(AUDIOS):
        print(f"  Audio{i+1} node {AUDIO_NODES[i]} -> {a.name}", flush=True)

    def _rh_call(fn, *args, **kwargs):
        real_exit = sys.exit

        def _trap(code=0):
            raise RuntimeError(f"RH_API_EXIT code={code}")

        sys.exit = _trap  # type: ignore[assignment]
        try:
            return fn(*args, **kwargs)
        finally:
            sys.exit = real_exit

    delay = 45
    data = None
    nodes = None
    for attempt in range(1, 13):
        try:
            if nodes is None:
                nodes = _rh_call(
                    apply_modifications,
                    api_key,
                    _rh_call(get_node_info, api_key, APP_ID),
                    node_args,
                    file_args,
                )
            data = _rh_call(submit_task, api_key, APP_ID, nodes)
            break
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            print(f"submit error attempt {attempt}: {msg}", flush=True)
            retryable = (
                "RH_API_EXIT" in msg or "421" in msg
                or "queue" in msg.lower() or "QUEUE" in msg
            )
            if not retryable or attempt == 12:
                raise
            nodes = None
            print(f"sleep {delay}s then retry...", flush=True)
            time.sleep(delay)
            delay = min(delay + 30, 180)

    if not data:
        raise RuntimeError("P04a: submit returned no data")

    task_id = str(data["taskId"])
    print(f"taskId = {task_id}", flush=True)

    final = poll_task(api_key, task_id)
    results = final.get("results") or []
    if not results:
        raise RuntimeError("P04a: task done but no files")

    usage = final.get("usage") or {}
    print("status:", final.get("status"), "usage:", usage, flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    saved = []
    for idx, item in enumerate(results, start=1):
        url = item.get("url") or item.get("outputUrl")
        if not url:
            continue
        dest = OUT if len(results) == 1 else OUT.with_name(f"{OUT.stem}_{idx}{OUT.suffix}")
        download_file(url, str(dest))
        fix_mov_to_mp4(str(dest))
        saved.append(dest)
        print(f"saved {dest} ({dest.stat().st_size // 1024} KB)", flush=True)

    receipt = {
        "unit": "P04a_v2_relink",
        "versionNote": (
            "重制 03→04 插入段；入点锁 P03 归档末帧、出点锁 P04b 归档首帧；"
            "废稿 960x544 明亮蓝波形房作废；近黑命令行暗室 + 沈默不给正脸 + 蓝椅开放抽屉；"
            "一次反馈=一次生成，未迭代第二版"
        ),
        "workflow": "金鱼",
        "appId": APP_ID,
        "taskId": task_id,
        "status": final.get("status"),
        "usage": usage,
        "promptBytes": len(prompt.encode("utf-8")),
        "params": "16:9 / 15s / 1.5MP / simple / 12",
        "refs": [str(r) for r in REFS],
        "audios": [str(a) for a in AUDIOS],
        "nodes": {"prompt": "263", "images": list(IMAGE_NODES), "audios": list(AUDIO_NODES)},
        "saved": [str(s) for s in saved],
    }
    (SEG / "RH任务回执_金鱼_P04a_v2.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"done": "P04a_v2", "taskId": task_id, "saved": [str(s) for s in saved]}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
