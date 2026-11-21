#!/usr/bin/env python3
"""只续轮询 S06 v2 的 prompt_id，查 history 取产物；绝不二次提交（G09）。"""
import json, time, shutil, sys
from pathlib import Path
import urllib.request

PID = "2475d94e-df9d-4977-87d0-897bbb8b9e72"
BASE = "http://127.0.0.1:8188"
OUT = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep06\全本批量_梅林\视频草稿\EP06_S06_v2_本地_鞋刃特写踢头子弹时间.mp4")
SRC = Path(r"F:\Work-Fisher纯净包2026.8.7\ComfyUI\output\S06_v2_local_meilin_00001-audio.mp4")

def get_history():
    try:
        with urllib.request.urlopen(f"{BASE}/history/{PID}", timeout=10) as r:
            return json.load(r)
    except Exception:
        return {}

for i in range(60):  # 最多约 10 分钟
    h = get_history()
    if h:
        for pid, v in h.items():
            st = v.get("status", {})
            print(f"DONE status={st.get('status_str')} completed={st.get('completed')}", flush=True)
            for nid, o in v.get("outputs", {}).items():
                for key in ("gifs", "videos", "images"):
                    for it in (o.get(key) or []):
                        print("  output:", it.get("filename"), flush=True)
        if SRC.exists():
            shutil.copy2(SRC, OUT)
            print(f"COPIED {OUT} {OUT.stat().st_size} bytes", flush=True)
        else:
            print(f"WARN: expected {SRC} not found; check ComfyUI output", flush=True)
        sys.exit(0)
    print(f"[{i+1}] still running...", flush=True)
    time.sleep(10)

print("TIMEOUT after 600s, still running", flush=True)
sys.exit(1)
