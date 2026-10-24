# -*- coding: utf-8 -*-
"""EP04 片段07「审问室空镜」· 金鱼工作流 RunningHub 提交脚本。

工作流：YZ金鱼-MiniMax H3 终极篇-文武双全（AI 应用 2093984226331938818）
素材：@图片1 陆沉人设 → <Picture 1> → <Subject 1>
      @图片2 审问室场景 → <Picture 2> → <Subject 2>
片段 07 为纯空镜，无对白，故不绑定任何 <Audio N>。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

RUNNINGHUB_SCRIPTS = Path(r"C:\Users\Administrator\.codex\skills\runninghub\scripts")
sys.path.insert(0, str(RUNNINGHUB_SCRIPTS))

from runninghub import download_file, fix_mov_to_mp4, poll_task, require_api_key  # noqa: E402
from runninghub_app import apply_modifications, get_node_info, submit_task  # noqa: E402

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
APP_ID = "2093984226331938818"

SEG = ROOT / "05-workflow" / "ep04" / "红绳片段07_审问室空镜"
PROMPT = SEG / "动作流_H3纯提示词.txt"
OUT_DIR = SEG / "视频草稿"
OUT = OUT_DIR / "E04-07_审问室空镜_未审核草稿.mp4"

# 槽位节点沿用 ep03 已跑通的映射：前三个为 51/49/50
SLOT_NODES = ("51", "49", "50")

REFS = [
    ROOT / "05-workflow" / "ep04" / "归档素材" / "人物" / "陆沉_人设.png",
    ROOT / "05-images" / "场景" / "场景_ND审问室_无人.png",
]


def main() -> int:
    api_key = require_api_key(os.environ.get("RH_API_KEY"))
    prompt = PROMPT.read_text(encoding="utf-8").strip()

    missing = [p for p in [PROMPT, *REFS] if not Path(p).exists()]
    if missing:
        print("缺失文件:", *[str(m) for m in missing], sep="\n  ")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    node_args = [
        f"263:text={prompt}",
        "252:aspect_ratio=16:9 (Widescreen)",
        "252:megapixels=0.5",
        "259:value=15",
        "283:value=1",
    ]
    file_args = [f"{SLOT_NODES[i]}:image={REFS[i]}" for i in range(len(REFS))]

    print(f"提交 {APP_ID} · 片段07 审问室空镜", flush=True)
    print(f"提示词 {len(prompt)} 字 · 参考图 {len(file_args)} 张 · 15s · 0.5MP", flush=True)

    nodes = apply_modifications(api_key, get_node_info(api_key, APP_ID), node_args, file_args)
    data = submit_task(api_key, APP_ID, nodes)
    task_id = str(data["taskId"])
    print(f"taskId = {task_id}", flush=True)

    final = poll_task(api_key, task_id)
    results = final.get("results") or []
    if not results:
        raise RuntimeError("任务完成但未返回文件")

    usage = final.get("usage") or {}
    print("状态:", final.get("status"), "消耗:", usage, flush=True)

    saved = []
    for idx, item in enumerate(results, start=1):
        url = item.get("url") or item.get("outputUrl")
        if not url:
            continue
        dest = OUT if len(results) == 1 else OUT.with_name(f"{OUT.stem}_{idx}{OUT.suffix}")
        download_file(url, str(dest))
        fix_mov_to_mp4(str(dest))
        saved.append(dest)
        print(f"已保存 {dest} ({dest.stat().st_size // 1024} KB)", flush=True)

    (SEG / "RH任务回执.json").write_text(
        json.dumps(
            {"taskId": task_id, "status": final.get("status"), "usage": usage,
             "saved": [str(s) for s in saved]},
            ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
