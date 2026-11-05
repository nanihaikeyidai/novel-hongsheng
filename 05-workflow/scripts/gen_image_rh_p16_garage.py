# -*- coding: utf-8 -*-
"""用 RunningHub 生图应用 2112991658311766017 生成 P16 地下车库场景图（保持日漫风格一致）。

用法：
    python gen_image_rh_p16_garage.py            # 生成
    python gen_image_rh_p16_garage.py --check    # 只查节点，不提交
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

RUNNINGHUB_SCRIPTS = Path(r"C:\Users\Administrator\.codex\skills\runninghub\scripts")
sys.path.insert(0, str(RUNNINGHUB_SCRIPTS))

from runninghub import download_file, fix_mov_to_mp4, poll_task, require_api_key  # noqa: E402
from runninghub_app import apply_modifications, get_node_info, submit_task  # noqa: E402

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
APP_ID = "2112991658311766017"
SEG_DIR = ROOT / "05-workflow" / "ep05" / "营救陆沉" / "红绳片段16"
PROMPT_PATH = SEG_DIR / "P16车库_生图提示词.txt"
OUT_DIR = ROOT / "05-images" / "场景"
STAMP = time.strftime("%Y%m%d_%H%M")


def find_image_result(results: list[dict]) -> str:
    for item in results:
        url = item.get("url") or item.get("outputUrl")
        if not url:
            continue
        if url.split("?")[0].lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            return url
    for item in results:
        url = item.get("url") or item.get("outputUrl")
        if url:
            return url
    raise RuntimeError("任务结果中没有图片文件")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只打印节点信息，不提交任务")
    ap.add_argument("--tag", default=STAMP, help="输出文件名后缀")
    args = ap.parse_args()

    api_key = require_api_key(os.environ.get("RUNNINGHUB_API_KEY"))
    prompt = PROMPT_PATH.read_text(encoding="utf-8").strip()
    if not prompt:
        raise SystemExit(f"空提示词：{PROMPT_PATH}")
    print(f"提示词 {len(prompt)} 字 · 16:9 · 2MP", flush=True)

    nodes = get_node_info(api_key, APP_ID)
    if args.check:
        print(json.dumps(nodes, ensure_ascii=False, indent=2)[:6000])
        return 0

    node_args = [
        f"57:value={prompt}",
        "19:aspect_ratio=16:9 (Widescreen)",
        "19:megapixels=2",
    ]
    print("提交任务…", flush=True)
    data = submit_task(api_key, APP_ID, apply_modifications(api_key, nodes, node_args, None))
    task_id = str(data["taskId"])
    print(f"taskId = {task_id}", flush=True)

    final = poll_task(api_key, task_id)
    url = find_image_result(final.get("results") or [])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"场景_EP05_地下车库_日漫电影感_{args.tag}.png"
    download_file(url, str(out))
    fix_mov_to_mp4(str(out))

    usage = final.get("usage") or {}
    receipt = {
        "appId": APP_ID,
        "taskId": task_id,
        "status": final.get("status"),
        "usage": usage,
        "prompt": str(PROMPT_PATH),
        "output": str(out),
        "url": url,
    }
    (SEG_DIR / f"RH生图回执_P16车库_{args.tag}.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"已保存 {out}\n消耗 {usage}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
