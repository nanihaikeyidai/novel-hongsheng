#!/usr/bin/env python3
"""把 episodes/*.md 内嵌进 index.html，便于 file:// 离线打开。"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EP_DIR = ROOT / "episodes"
INDEX = Path(__file__).resolve().parent / "index.html"
MARKER_START = "/*__EPISODES_JSON_START__*/"
MARKER_END = "/*__EPISODES_JSON_END__*/"


def load_episodes() -> list[dict]:
    items = []
    for path in sorted(EP_DIR.glob("ep*.md")):
        text = path.read_text(encoding="utf-8")
        meta = {"id": path.stem, "title": path.stem, "status": "", "updated": ""}
        # yaml 块的正则必须兼容 CRLF：Windows git 的 autocrlf 会把文件写成 \r\n，
        # 用 ```yaml\n 匹配会整个失配，导致 status/updated 等字段读不出来
        # （页面显示成默认的「草稿」）。
        m = re.search(r"```ya?ml\r?\n(.*?)```", text, re.S)
        if m:
            for line in m.group(1).splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"').strip("'")
        # title from H1 if present
        h1 = re.search(r"^#\s+(.+)$", text, re.M)
        if h1 and "·" in h1.group(1):
            meta["title"] = h1.group(1).split("·", 1)[-1].strip()
        elif h1:
            meta["title"] = h1.group(1).strip()
        items.append({"id": meta["id"], "meta": meta, "markdown": text})
    return items


def main() -> None:
    eps = load_episodes()
    payload = json.dumps(eps, ensure_ascii=False)
    html = INDEX.read_text(encoding="utf-8")
    if MARKER_START not in html or MARKER_END not in html:
        raise SystemExit("index.html missing embed markers")
    before, rest = html.split(MARKER_START, 1)
    _, after = rest.split(MARKER_END, 1)
    new_html = (
        before
        + MARKER_START
        + "\nconst EMBEDDED_EPISODES = "
        + payload
        + ";\n"
        + MARKER_END
        + after
    )
    INDEX.write_text(new_html, encoding="utf-8")
    print(f"synced {len(eps)} episode(s) -> {INDEX}")


if __name__ == "__main__":
    main()
