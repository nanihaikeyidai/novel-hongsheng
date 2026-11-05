# -*- coding: utf-8 -*-
"""EP05 P14 v6 加速下楼｜单梯段 / 安娜领跑 / 侧面特写 —— RunningHub 云端金鱼 Ref2VA 提交。

v6 修正（P14_v5_复盘.md）：用户四项反馈。
  - 跑太慢：补加速奔跑锁（footfalls accelerate / 前倾 / 发衣后扬 / 台阶动感模糊 /
    切镜变短），删 never break stride / still descending / slower pulse
  - 楼梯不要分开两边：<Picture 3> 换本地 MOSS 生成的单一连续下行梯段视图，
    删全部折返条款（两段平行梯段 / 半层平台 / 180° 转向 / 中央分隔扶手）
  - 安娜在前陆沉在后：主体定义 + summary + 各 Shot 共 4 处 LEADS / 2 处 BEHIND 写死
  - 安娜台词给侧面特写：Shot 2 改 TIGHT PROFILE CLOSE-UP、说话不转头；
    蓝黑发在特写行重述（dark navy, visible blue sheen + 红光只改光色不改色素）
  - 保留 v5 已验证的垂直下降锁 / 低机位迎面锁 / 台词 ONCE 锁 / 红闪 / 伪字加强版

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
SEG = ROOT / "05-workflow" / "ep05" / "营救陆沉" / "红绳片段14"

PROMPT = SEG / "金鱼_H3纯提示词_P14_v6.txt"
REFS = [
    SEG / "上传包" / "image1_anna_cleaner.jpg",
    SEG / "上传包" / "image2_luchen_whiteshirt.jpg",
    SEG / "上传包" / "image3_MOSS_single_flight_v4.jpg",
]
AUDIOS = [
    SEG / "上传包" / "audio1_anna.wav",
]
IMAGE_NODES = ("51", "49", "50")
AUDIO_NODES = ("48",)
OUT = SEG / "视频草稿" / "片段14_P14_金鱼草稿_v6.mp4"


def main() -> int:
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
        raise ValueError("P14: H3 gate failed")
    declared = len(set(re.findall(r"<Audio (\d+)>", prompt)))
    if declared != len(AUDIOS):
        raise ValueError(f"P14: audio mismatch prompt={declared} bound={len(AUDIOS)}")
    if len(prompt.encode("utf-8")) > 5000:
        raise ValueError(f"P14: prompt too long {len(prompt.encode('utf-8'))} bytes")

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

    print(f"=== P14 v6 加速下楼 | 金鱼 {APP_ID} | {len(prompt.encode('utf-8'))} bytes | 15s | 1.5MP ===", flush=True)
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
        raise RuntimeError("P14: submit returned no data")

    task_id = str(data["taskId"])
    print(f"taskId = {task_id}", flush=True)

    final = poll_task(api_key, task_id)
    results = final.get("results") or []
    if not results:
        raise RuntimeError("P14: task done but no files")

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
        "unit": "P14_v6",
        "versionNote": "Picture 3 换本地 MOSS 单一连续下行梯段视图（无中央分隔扶手）；加速奔跑锁；安娜在前陆沉在后；台词侧面特写 + 蓝发双重锁定；删全部折返条款",
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
    (SEG / "RH任务回执_金鱼_P14_v6.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"done": "P14", "taskId": task_id, "saved": [str(s) for s in saved]},
                     ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
