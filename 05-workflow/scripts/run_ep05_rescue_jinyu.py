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
import time
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
SHENMO = ROOT / "05-workflow" / "归档素材" / "人物" / "沈默_人设.png"
LUCHEN = ROOT / "05-workflow" / "归档素材" / "人物" / "陆沉_人设.png"
HALL = ROOT / "05-images" / "场景" / "场景_翠羽社大厅_日漫电影感.png"
GATE = ROOT / "05-images" / "场景" / "场景_EP05_ND观察室门口_门卫岗_夜_v5.jpg"
COMPUTER = ROOT / "05-images" / "场景" / "场景_EP05_沈默电脑房_三巨屏暗室.jpg"
PROPS = ROOT / "05-images" / "道具" / "道具_EP05_复制门禁卡与改装手机.jpg"
VOICE_DIR = ROOT / "05-workflow" / "归档素材" / "人物参考音色"
LESTER_VOICE = VOICE_DIR / "雷斯特.wav"
ANNA_VOICE = VOICE_DIR / "安娜.wav"
SHENMO_VOICE = VOICE_DIR / "沈默.wav"

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
    "P01b": {
        "seg_dir": RESCUE / "红绳片段01",
        "title": "约束找小默明白",
        "prompt": RESCUE / "红绳片段01" / "金鱼_H3纯提示词_P01b.txt",
        "refs": [LESTER, ANNA, HALL],
        "audios": [LESTER_VOICE, ANNA_VOICE],
        "out_name": "片段01_P01b_金鱼草稿.mp4",
    },
    "P02": {
        "seg_dir": RESCUE / "红绳片段02",
        "title": "观察室门口门卫",
        "prompt": RESCUE / "红绳片段02" / "金鱼_H3纯提示词_P02.txt",
        "refs": [LUCHEN, GATE],
        "audios": [],
        "out_name": "片段02_P02_金鱼草稿.mp4",
    },
    "P03": {
        "seg_dir": RESCUE / "红绳片段03",
        "title": "电脑房找小默",
        "prompt": RESCUE / "红绳片段03" / "金鱼_H3纯提示词_P03.txt",
        "refs": [ANNA, SHENMO, COMPUTER],
        "audios": [ANNA_VOICE, SHENMO_VOICE],
        "out_name": "片段03_P03_金鱼草稿.mp4",
    },
    "P04a": {
        "seg_dir": RESCUE / "红绳片段04",
        "title": "抽屉道具沈默指",
        "prompt": RESCUE / "红绳片段04" / "金鱼_H3纯提示词_P04a.txt",
        "refs": [ANNA, SHENMO, COMPUTER, PROPS],
        "audios": [SHENMO_VOICE],
        "out_name": "片段04_P04a_金鱼草稿.mp4",
    },
    "P04b": {
        "seg_dir": RESCUE / "红绳片段04",
        "title": "安娜提问沈默答",
        "prompt": RESCUE / "红绳片段04" / "金鱼_H3纯提示词_P04b.txt",
        "refs": [ANNA, SHENMO, COMPUTER, PROPS],
        "audios": [ANNA_VOICE, SHENMO_VOICE],
        "out_name": "片段04_P04b_金鱼草稿.mp4",
    },
    "P05a": {
        "seg_dir": RESCUE / "红绳片段05",
        "title": "嘲笑与不耐烦",
        "prompt": RESCUE / "红绳片段05" / "金鱼_H3纯提示词_P05a.txt",
        "refs": [ANNA, SHENMO, COMPUTER, PROPS],
        "audios": [ANNA_VOICE, SHENMO_VOICE],
        "out_name": "片段05_P05a_金鱼草稿.mp4",
    },
    "P05b": {
        "seg_dir": RESCUE / "红绳片段05",
        "title": "取物道谢关门",
        "prompt": RESCUE / "红绳片段05" / "金鱼_H3纯提示词_P05b.txt",
        "refs": [ANNA, SHENMO, COMPUTER, PROPS],
        "audios": [ANNA_VOICE, SHENMO_VOICE],
        "out_name": "片段05_P05b_金鱼草稿.mp4",
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


def _is_queue_limit(exc: BaseException) -> bool:
    text = str(exc)
    return "421" in text or "QUEUE" in text.upper() or "queue" in text.lower()


def submit_with_retry(api_key: str, nodes: list, max_attempts: int = 12) -> dict:
    delay = 45
    last = None
    for attempt in range(1, max_attempts + 1):
        try:
            return submit_task(api_key, APP_ID, nodes)
        except SystemExit as exc:
            last = exc
            # runninghub_app may sys.exit(1) on API errors; re-raise unless queue
            raise
        except Exception as exc:  # noqa: BLE001
            last = exc
            if not _is_queue_limit(exc) or attempt == max_attempts:
                raise
            print(f"queue/limit hit ({exc}); sleep {delay}s then retry {attempt}/{max_attempts}", flush=True)
            time.sleep(delay)
            delay = min(delay + 30, 180)
    raise RuntimeError(f"submit failed after retries: {last}")


def run_unit(api_key: str, unit_id: str, suffix: str = "") -> dict:
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
        raise FileNotFoundError(str(missing))

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
        raise ValueError(f"{unit_id}: H3 gate failed")

    declared = len(set(re.findall(r"<Audio (\d+)>", prompt)))
    if declared != len(audios):
        raise ValueError(f"{unit_id}: audio mismatch prompt={declared} bound={len(audios)}")
    for bad in re.findall(r"\(S\d+\)\s*<d>", prompt):
        raise ValueError(f"{unit_id}: duplicate speaker tag {bad}")

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

    def _rh_call(fn, *args, **kwargs):
        """runninghub_app uses sys.exit on API errors; convert to exception for retry."""
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
            # Always retry RH_API_EXIT / 421 / queue; re-upload nodes next try if needed
            retryable = (
                "RH_API_EXIT" in msg
                or "421" in msg
                or "queue" in msg.lower()
                or "QUEUE" in msg
            )
            if not retryable or attempt == 12:
                raise
            # force re-get nodes next attempt in case upload tokens stale
            nodes = None
            print(f"sleep {delay}s then retry...", flush=True)
            time.sleep(delay)
            delay = min(delay + 30, 180)

    if not data:
        raise RuntimeError(f"{unit_id}: submit returned no data")

    task_id = str(data["taskId"])
    print(f"taskId = {task_id}", flush=True)

    final = poll_task(api_key, task_id)
    results = final.get("results") or []
    if not results:
        raise RuntimeError(f"{unit_id}: task done but no files")

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

    receipt = {
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
    }
    (seg / f"RH任务回执_金鱼_{unit_id}.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # also keep legacy name for P01a compatibility
    if unit_id == "P01a":
        (seg / "RH任务回执_金鱼.json").write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("units", nargs="+", choices=sorted(UNITS), help="unit id e.g. P01b")
    ap.add_argument("--suffix", default="", help="output filename suffix")
    args = ap.parse_args()

    api_key = require_api_key(os.environ.get("RH_API_KEY") or os.environ.get("RUNNINGHUB_API_KEY"))
    results = []
    for unit_id in args.units:
        receipt = run_unit(api_key, unit_id, args.suffix)
        results.append(receipt)
        print(json.dumps({"done": unit_id, "taskId": receipt["taskId"], "status": receipt["status"]}, ensure_ascii=False), flush=True)

    summary_path = RESCUE / "制作文档" / "jinyu_batch_receipts.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if summary_path.exists():
        try:
            existing = json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = []
    by_unit = {r.get("unit"): r for r in existing if isinstance(r, dict)}
    for r in results:
        by_unit[r["unit"]] = r
    summary_path.write_text(
        json.dumps(list(by_unit.values()), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
