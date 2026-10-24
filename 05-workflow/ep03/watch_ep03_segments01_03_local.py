from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

COMFY_URL = "http://127.0.0.1:8188"
PROMPT_ID = "13676cf0-dd22-48fc-bca3-d99b885e42a0"
RUN_DIR = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep03\local_runs\segments01_03_long")
OUTPUT_DIR = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep03\视频长片段")
OUTPUT = OUTPUT_DIR / "EP03_片段01-03_本地导演台_未审核长视频.mp4"


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def locate_video(history: dict) -> dict | None:
    candidates = []
    for node_output in (history.get("outputs") or {}).values():
        if not isinstance(node_output, dict):
            continue
        for key in ("videos", "gifs", "files"):
            values = node_output.get(key, [])
            if isinstance(values, dict):
                values = [values]
            for item in values:
                if isinstance(item, dict) and item.get("filename"):
                    candidates.append(item)
    mp4 = [v for v in candidates if str(v.get("filename", "")).lower().endswith((".mp4", ".mov", ".webm"))]
    return (mp4 or candidates)[-1] if candidates else None


def download(item: dict) -> None:
    query = urllib.parse.urlencode({
        "filename": item["filename"],
        "subfolder": item.get("subfolder", ""),
        "type": item.get("type", "output"),
    })
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(f"{COMFY_URL}/view?{query}", timeout=120) as response:
        OUTPUT.write_bytes(response.read())


def main() -> None:
    while True:
        history = get_json(f"{COMFY_URL}/history/{PROMPT_ID}")
        result = history.get(PROMPT_ID)
        if result:
            status = result.get("status") or {}
            if status.get("status_str") == "error":
                (RUN_DIR / "结果监听错误.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
                return
            item = locate_video(result)
            if item:
                download(item)
                (RUN_DIR / "历史记录.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                (RUN_DIR / "结果监听完成.json").write_text(json.dumps({"output": str(OUTPUT), "source": item}, ensure_ascii=False, indent=2), encoding="utf-8")
                return
        time.sleep(30)


if __name__ == "__main__":
    main()
