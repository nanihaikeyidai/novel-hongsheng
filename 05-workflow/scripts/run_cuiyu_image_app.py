# -*- coding: utf-8 -*-
"""用 RunningHub 生图应用生成翠羽社夕阳大厅场景图与墙面空镜首帧。"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

RUNNINGHUB_SCRIPTS = Path(r"C:\Users\Administrator\.codex\skills\runninghub\scripts")
sys.path.insert(0, str(RUNNINGHUB_SCRIPTS))

from runninghub import download_file, fix_mov_to_mp4, poll_task, require_api_key  # noqa: E402
from runninghub_app import apply_modifications, get_node_info, submit_task  # noqa: E402

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
APP_ID = "2112991658311766017"
SEG_DIR = ROOT / "05-workflow" / "ep04" / "红绳片段16_翠羽社汇报"

STAGES = {
    "scene": {
        "prompt": SEG_DIR / "翠羽社大厅_生图提示词.txt",
        "output": ROOT / "05-images" / "场景" / "场景_翠羽社大厅_日漫电影感.png",
        "title": "翠羽社大厅场景图",
        "receipt_dir": SEG_DIR,
    },
    "frame": {
        "prompt": SEG_DIR / "首帧图_生图提示词.txt",
        "output": SEG_DIR / "首帧图.png",
        "title": "翠羽社墙面夕阳空镜首帧",
        "receipt_dir": SEG_DIR,
    },
    "nd_gate": {
        "prompt": ROOT / "05-workflow" / "ep04" / "红绳片段11d4_世界的代价" / "场景_ND东郊分部大门_薄暮_生图提示词.txt",
        "output": ROOT / "05-images" / "场景" / "场景_ND东郊分部大门_薄暮_日漫电影感.png",
        "title": "ND东郊分部大门薄暮外景",
        "receipt_dir": ROOT / "05-workflow" / "ep04" / "红绳片段11d4_世界的代价",
    },
}


def find_image_result(results: list[dict]) -> str:
    for item in results:
        url = item.get("url") or item.get("outputUrl")
        if not url:
            continue
        path = url.split("?")[0]
        if path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            return url
    for item in results:
        url = item.get("url") or item.get("outputUrl")
        if url:
            return url
    raise RuntimeError("任务结果中没有图片文件")


def run_stage(api_key: str, stage: str) -> Path:
    conf = STAGES[stage]
    prompt_path = Path(conf["prompt"])
    output_path = Path(conf["output"])
    prompt = prompt_path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"空提示词：{prompt_path}")

    node_args = [
        f"57:value={prompt}",
        "19:aspect_ratio=16:9 (Widescreen)",
        "19:megapixels=2",
    ]
    print(f"\n=== {conf['title']} ===\n提示词 {len(prompt)} 字 · 16:9 · 2MP", flush=True)

    nodes = apply_modifications(
        api_key,
        get_node_info(api_key, APP_ID),
        node_args,
        None,
    )
    data = submit_task(api_key, APP_ID, nodes)
    task_id = str(data["taskId"])
    print(f"taskId = {task_id}", flush=True)

    final = poll_task(api_key, task_id)
    results = final.get("results") or []
    url = find_image_result(results)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    download_file(url, str(output_path))
    fix_mov_to_mp4(str(output_path))

    usage = final.get("usage") or {}
    receipt = {
        "stage": stage,
        "title": conf["title"],
        "taskId": task_id,
        "status": final.get("status"),
        "usage": usage,
        "prompt": str(prompt_path),
        "output": str(output_path),
    }
    receipt_dir = Path(conf.get("receipt_dir", SEG_DIR))
    (receipt_dir / f"RH生图回执_{stage}.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"已保存 {output_path} · 消耗 {usage}", flush=True)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stages", nargs="+", choices=list(STAGES), default=list(STAGES))
    args = parser.parse_args()
    api_key = require_api_key(os.environ.get("RUNNINGHUB_API_KEY"))
    for stage in args.stages:
        run_stage(api_key, stage)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
