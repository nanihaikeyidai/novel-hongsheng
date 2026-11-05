# -*- coding: utf-8 -*-
"""EP05 P16 v1 地下车库上车｜日漫场景图 / 安娜「上车」ONCE —— RunningHub 云端金鱼 Ref2VA 提交。

开发依据：`红绳片段16/本片段分镜.md`（按 shot-and-segment.md 的七列单元表 /
八列镜头表 / 对白台账 / 参考图清单 / 质量检查开发）。

承接 P14 v7（空梯 + 红色警报）：两人撞开底层防火门冲进 ND 地下车库，
跑向 P06a 开来的同一辆深蓝黑轿车；安娜开近侧副驾车门、侧面特写说
「上车」一次；陆沉入副驾、安娜在驾驶座、两门关上、警报变闷、前灯亮起。
车不驶离。

  - <Picture 3> = 本轮新生成的日漫化车库场景图 image3_garage_anime_v2.jpg
    （赛璐璐化、裁 16:9 去水印、抹车标、无文字、四门关闭、远处一抹红光）；
    备选 image3_P06a_anime_frame.jpg（100% 同源成片截帧）。MOSS 写实图停用（L 型）。
  - 人物锁：安娜蓝黑发 / 灰帽 / 白口罩 / 深灰工装；陆沉黑乱短发 + 白衬衫，全程沉默。
  - 台词 ONCE 锁：2 字「上车」只在 ~06.2–07.2s 一次，前后零音节。
  - D / J / E / L 型条款见分镜文档第六节。

⚠️ 生成闸门（用户 2026-11-05 硬规则）：必须显式设 P16_CONFIRMED=1 才允许提交，
   否则直接退出，避免误烧 379–425 币。

应用：2110357037929558018（YZ金鱼 H3 Ref2VA Plus）
规格：16:9 / 15s / 1.5MP / simple / 12 步
槽位：image1=51 image2=49 image3=50 | audio1=48（本段仅安娜音色）
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
SEG = ROOT / "05-workflow" / "ep05" / "营救陆沉" / "红绳片段16"

PROMPT = SEG / "金鱼_H3纯提示词_P16_v1.txt"
REFS = [
    SEG / "上传包" / "image1_anna_cleaner.jpg",
    SEG / "上传包" / "image2_luchen_whiteshirt.jpg",
    SEG / "上传包" / "image3_garage_anime_v2.jpg",
]
AUDIOS = [
    SEG / "上传包" / "audio1_anna.wav",
]
IMAGE_NODES = ("51", "49", "50")
AUDIO_NODES = ("48",)
OUT = SEG / "视频草稿" / "片段16_P16_金鱼草稿_v1.mp4"


def main() -> int:
    if os.environ.get("P16_CONFIRMED") != "1":
        raise SystemExit(
            "P16: 未获用户确认，拒绝提交视频生成（约 379-425 币）。"
            "确认后请设 P16_CONFIRMED=1 再运行本脚本。"
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
        raise ValueError("P16: H3 gate failed")
    declared = len(set(re.findall(r"<Audio (\d+)>", prompt)))
    if declared != len(AUDIOS):
        raise ValueError(f"P16: audio mismatch prompt={declared} bound={len(AUDIOS)}")
    if len(prompt.encode("utf-8")) > 5000:
        raise ValueError(f"P16: prompt too long {len(prompt.encode('utf-8'))} bytes")

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

    print(f"=== P16 v1 地下车库上车 | 金鱼 {APP_ID} | {len(prompt.encode('utf-8'))} bytes | 15s | 1.5MP ===", flush=True)
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
        raise RuntimeError("P16: submit returned no data")

    task_id = str(data["taskId"])
    print(f"taskId = {task_id}", flush=True)

    final = poll_task(api_key, task_id)
    results = final.get("results") or []
    if not results:
        raise RuntimeError("P16: task done but no files")

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
        "unit": "P16_v1",
        "versionNote": "按剧本分镜规范开发的地下车库上车新段；Picture 3 为本轮新生成日漫化车库场景图（MOSS 写实图停用）；台词「上车」ONCE；车不驶离；生成闸门 P16_CONFIRMED=1",
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
    (SEG / "RH任务回执_金鱼_P16_v1.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"done": "P16", "taskId": task_id, "saved": [str(s) for s in saved]},
                     ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
