# -*- coding: utf-8 -*-
"""EP05 营救陆沉 RunningHub 金鱼工作流提交脚本。

YZ金鱼-MiniMax H3 终极篇-文武双全
AI应用 2093984226331938818 · 15秒 · 0.5MP · 二采倍率1 · 16:9

勿用导演台 2096059277453643778 / API 2084788947984666625。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

RUNNINGHUB_SCRIPTS = Path(r"C:\Users\Administrator\.codex\skills\runninghub\scripts")
sys.path.insert(0, str(RUNNINGHUB_SCRIPTS))

# Windows GBK locale breaks curl JSON with Chinese; force UTF-8 text subprocess I/O.
import subprocess as _sp

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
APP_ID = "2093984226331938818"
RESCUE = ROOT / "05-workflow" / "ep05" / "营救陆沉"

LESTER = ROOT / "05-workflow" / "归档素材" / "人物" / "雷斯特_人设.png"
ANNA = ROOT / "05-workflow" / "归档素材" / "人物" / "安娜_人设.png"
HALL = ROOT / "05-images" / "场景" / "场景_翠羽社大厅_日漫电影感.png"
VOICE_DIR = ROOT / "05-workflow" / "归档素材" / "人物参考音色"
LESTER_VOICE = VOICE_DIR / "雷斯特.wav"

SLOT_NODES = ("51", "49", "50", "43")
AUDIO_SLOT_NODES = ("48", "14", "15")

UNITS = {
    "P01a": {
        "seg_dir": RESCUE / "红绳片段01",
        "title": "下令救人回社",
        "prompt": RESCUE / "红绳片段01" / "金鱼_H3纯提示词_P01a.txt",
        "refs": [LESTER, ANNA, HALL],
        "audios": [LESTER_VOICE],
        "out_name": "片段01_P01a_金鱼草稿.mp4",
    },
}


def normalize_for_phone(video: Path) -> Path:
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "out.mp4"
        subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error", "-i", str(video),
                "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                "-ar", "44100", "-ac", "2", "-movflags", "+faststart", str(tmp),
            ],
            check=True,
        )
        if tmp.stat().st_size == 0:
            print(f"phone remux failed, keep original: {video.name}", file=sys.stderr)
            return video
        data = tmp.read_bytes()
    video.write_bytes(data)
    head = data[:65536]
    order = [head.find(b) for b in (b"ftyp", b"moov", b"mdat")]
    ok = order[1] > 0 and order[1] < order[2]
    print(f"phone remux: ftyp/moov/mdat @ {order} moov_front={ok}", flush=True)
    return video


def run_unit(api_key: str, unit_id: str, suffix: str = "") -> int:
    conf = UNITS[unit_id]
    prompt_file = Path(conf["prompt"])
    seg = Path(conf["seg_dir"])
    out_dir = seg / "视频草稿"
    stem = Path(conf["out_name"]).stem
    out = out_dir / f"{stem}{suffix}.mp4"
    audios = conf.get("audios", [])
    prompt = prompt_file.read_text(encoding="utf-8").strip()

    missing = [p for p in [prompt_file, *conf["refs"], *audios] if not Path(p).exists()]
    if missing:
        print("missing:", *[str(m) for m in missing], sep="\n  ")
        return 1

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
        print("H3 gate failed")
        return 1

    declared = len(set(re.findall(r"<Audio (\d+)>", prompt)))
    if declared != len(audios):
        print(f"audio mismatch: prompt declares {declared}, bound {len(audios)}")
        return 1
    for bad in re.findall(r"\(S\d+\)\s*<d>", prompt):
        print(f"duplicate speaker tag: {bad}")
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    node_args = [
        f"263:text={prompt}",
        "252:aspect_ratio=16:9 (Widescreen)",
        "252:megapixels=0.5",
        "259:value=15",
        "283:value=1",
    ]
    file_args = [f"{SLOT_NODES[i]}:image={conf['refs'][i]}" for i in range(len(conf["refs"]))]
    file_args += [f"{AUDIO_SLOT_NODES[i]}:audio={audios[i]}" for i in range(len(audios))]

    print(f"\n=== {unit_id} {conf['title']} jinyu {APP_ID} ===", flush=True)
    print(
        f"prompt {len(prompt)} chars · refs {len(conf['refs'])} · audios {len(audios)} · 15s · 0.5MP",
        flush=True,
    )
    for i, r in enumerate(conf["refs"]):
        print(f"  image{i+1} node {SLOT_NODES[i]} -> {Path(r).name}", flush=True)
    for i, a in enumerate(audios):
        print(f"  Audio{i+1} node {AUDIO_SLOT_NODES[i]} -> {Path(a).name}", flush=True)

    nodes = apply_modifications(api_key, get_node_info(api_key, APP_ID), node_args, file_args)
    data = submit_task(api_key, APP_ID, nodes)
    task_id = str(data["taskId"])
    print(f"taskId = {task_id}", flush=True)

    final = poll_task(api_key, task_id)
    results = final.get("results") or []
    if not results:
        raise RuntimeError("task done but no files")

    usage = final.get("usage") or {}
    print("status:", final.get("status"), "usage:", usage, flush=True)

    saved = []
    for idx, item in enumerate(results, start=1):
        url = item.get("url") or item.get("outputUrl")
        if not url:
            continue
        dest = out if len(results) == 1 else out.with_name(f"{out.stem}_{idx}{out.suffix}")
        download_file(url, str(dest))
        fix_mov_to_mp4(str(dest))
        dest = normalize_for_phone(dest)
        saved.append(dest)
        print(f"saved {dest} ({dest.stat().st_size // 1024} KB)", flush=True)

    (seg / "RH任务回执_金鱼.json").write_text(
        json.dumps(
            {
                "unit": unit_id,
                "workflow": "金鱼",
                "appId": APP_ID,
                "taskId": task_id,
                "status": final.get("status"),
                "usage": usage,
                "promptChars": len(prompt),
                "refs": [str(r) for r in conf["refs"]],
                "audios": [str(a) for a in audios],
                "nodes": {
                    "prompt": "263",
                    "images": list(SLOT_NODES[: len(conf["refs"])]),
                    "audios": list(AUDIO_SLOT_NODES[: len(audios)]),
                },
                "saved": [str(s) for s in saved],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("units", nargs="+", choices=sorted(UNITS), help="unit id e.g. P01a")
    ap.add_argument("--suffix", default="", help="output filename suffix")
    args = ap.parse_args()

    api_key = require_api_key(os.environ.get("RH_API_KEY") or os.environ.get("RUNNINGHUB_API_KEY"))
    rc = 0
    for unit_id in args.units:
        rc |= run_unit(api_key, unit_id, args.suffix)
    return rc


if __name__ == "__main__":
    sys.exit(main())
