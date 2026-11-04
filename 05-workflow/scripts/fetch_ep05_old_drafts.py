# -*- coding: utf-8 -*-
"""从 RunningHub 历史任务拉回 ep05 旧片段成片（本地缺失的云端草稿）。"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\Administrator\.codex\skills\runninghub\scripts")
from runninghub import download_file, fix_mov_to_mp4, poll_task  # noqa: E402

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep05\营救陆沉")

# (片段目录, 输出文件名, taskId, 版本标签)
JOBS = [
    ("红绳片段04", "片段04_P04b_金鱼草稿_云端旧版黑发.mp4", "2115472606995111938"),
    ("红绳片段05", "片段05_P05a_金鱼草稿_云端旧版黑发.mp4", "2115807889888337921"),
    ("红绳片段05", "片段05_P05b_金鱼草稿_云端旧版黑发.mp4", "2114296128521601026"),
    ("红绳片段06", "片段06_P06a_金鱼草稿_云端旧版黑发.mp4", "2116202548926042114"),
    ("红绳片段07", "片段07_P07v6_金鱼草稿_云端旧版黑发.mp4", "2116417950402699266"),
    ("红绳片段08", "片段08_P08_金鱼草稿_云端旧版黑发.mp4", "2116217897314648066"),
    ("红绳片段09", "片段09_P09v13_金鱼草稿_云端旧版黑发.mp4", "2117298304089018370"),
    ("红绳片段10", "片段10_P10_金鱼草稿_云端旧版黑发.mp4", "2116220721435987969"),
    ("红绳片段11", "片段11_P11v5_金鱼草稿_云端旧版黑发.mp4", "2116378298463518722"),
]


def main() -> int:
    api_key = os.environ.get("RH_API_KEY") or os.environ.get("RUNNINGHUB_API_KEY")
    ok, fail = [], []
    for seg, name, tid in JOBS:
        out = ROOT / seg / "视频草稿" / name
        if out.exists():
            print(f"[skip] {name} 已存在", flush=True)
            ok.append((name, tid))
            continue
        try:
            r = poll_task(api_key, tid)
            results = r.get("results") or []
            urls = [it.get("url") or it.get("outputUrl") for it in results]
            urls = [u for u in urls if u]
            if not urls:
                print(f"[fail] {name} taskId={tid} 无产物: {str(r)[:200]}", flush=True)
                fail.append((name, tid))
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            download_file(urls[0], str(out))
            fix_mov_to_mp4(str(out))
            print(f"[ok] {name} ({out.stat().st_size // 1024} KB)", flush=True)
            ok.append((name, tid))
        except Exception as exc:  # noqa: BLE001
            print(f"[fail] {name} taskId={tid} {exc}", flush=True)
            fail.append((name, tid))
    print(json.dumps({"ok": len(ok), "fail": len(fail),
                      "failed": [f[0] for f in fail]}, ensure_ascii=False), flush=True)
    return 0 if not fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
