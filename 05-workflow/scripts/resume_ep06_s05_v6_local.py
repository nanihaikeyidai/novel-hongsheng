#!/usr/bin/env python3
"""只续轮询 S05 v6 的 prompt_id，查 history 取产物；绝不二次提交（G09）。"""
import json, time, shutil, sys
from pathlib import Path
import urllib.request

PID = "d43a16b4-f4f5-4666-8cb7-d8bcbb721324"
BASE = "http://127.0.0.1:8188"
OUT = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep06\全本批量_梅林\视频草稿\EP06_S05_v6_本地_瞳孔红_镜头对陆沉.mp4")
# 带音轨版本优先（本地成片为模型自生成音轨）
SRCS = [
    Path(r"F:\Work-Fisher纯净包2026.8.7\ComfyUI\output\S05_v6_local_meilin_00001-audio.mp4"),
    Path(r"F:\Work-Fisher纯净包2026.8.7\ComfyUI\output\S05_v6_local_meilin_00001.mp4"),
]

def get_history():
    try:
        with urllib.request.urlopen(f"{BASE}/history/{PID}", timeout=10) as r:
            return json.load(r)
    except Exception:
        return {}

for i in range(90):  # 最多约 15 分钟
    h = get_history()
    if h:
        for pid, v in h.items():
            st = v.get("status", {})
            print(f"DONE status={st.get('status_str')} completed={st.get('completed')}", flush=True)
            for nid, o in v.get("outputs", {}).items():
                for key in ("gifs", "videos", "images"):
                    for it in (o.get(key) or []):
                        print("  output:", it.get("filename"), flush=True)
        picked = None
        for s in SRCS:
            if s.exists():
                picked = s
                break
        if picked:
            shutil.copy2(picked, OUT)
            print(f"COPIED {picked.name} -> {OUT} {OUT.stat().st_size} bytes", flush=True)
        else:
            print("WARN: expected S05_v6 output not found; check ComfyUI output", flush=True)
        sys.exit(0)
    print(f"[{i+1}] still running...", flush=True)
    time.sleep(10)

print("TIMEOUT after 900s, still running", flush=True)
sys.exit(1)
