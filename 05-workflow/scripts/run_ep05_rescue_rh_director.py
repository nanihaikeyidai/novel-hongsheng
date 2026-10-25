# -*- coding: utf-8 -*-
"""EP05《营救陆沉》RunningHub 云端导演台提交（ComfyUI 完整 workflow 格式）。

工作流 API ID: 2084788947984666625
工作流: 2096059277453643778
模板: F:/ComfyUI_V6.0/MiniMax H3 导演台全能工作流红绳_api.json

用法（用户机）:
  python 05-workflow/scripts/run_ep05_rescue_rh_director.py --unit P01a
  python 05-workflow/scripts/run_ep05_rescue_rh_director.py --unit P01a --poll
  python 05-workflow/scripts/run_ep05_rescue_rh_director.py --unit all01 --poll
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path

import requests

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
API_KEY = os.environ.get("RH_API_KEY") or os.environ.get("RUNNINGHUB_API_KEY") or ""
API_ID = "2084788947984666625"
SUBMIT_URL = f"https://www.runninghub.cn/openapi/v2/run/workflow/{API_ID}"
QUERY_URL = "https://www.runninghub.cn/openapi/v2/query"
UPLOAD_URL = "https://www.runninghub.cn/openapi/v2/media/upload/binary"
WF_TEMPLATE = Path(r"F:\ComfyUI_V6.0\MiniMax H3 导演台全能工作流红绳_api.json")
PKG = ROOT / "05-workflow" / "ep05" / "营救陆沉"
CACHE = PKG / "制作文档" / "rh_upload_cache.json"

FRAMES_15 = 362  # 15s @24fps + margin used by project
WIDTH, HEIGHT = 1056, 608


def headers():
    return {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def upload(path: Path) -> str:
    """Return openapi/ fileName."""
    cache = {}
    if CACHE.exists():
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    key = str(path.resolve())
    mtime = path.stat().st_mtime
    if key in cache and cache[key].get("mtime") == mtime and cache[key].get("fileName"):
        print(f"[cache] {path.name} -> {cache[key]['fileName']}")
        return cache[key]["fileName"]
    print(f"[upload] {path}")
    with path.open("rb") as f:
        r = requests.post(
            UPLOAD_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            files={"file": (path.name, f)},
            timeout=180,
        )
    r.raise_for_status()
    data = r.json()
    # tolerate nested shapes
    payload = data.get("data") or data
    file_name = payload.get("fileName") or payload.get("filename")
    if not file_name:
        raise RuntimeError(f"upload missing fileName: {data}")
    cache[key] = {"mtime": mtime, "fileName": file_name, "raw": payload}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[uploaded] {file_name}")
    return file_name


def extract_unit(md_text: str, unit: str) -> tuple[str, str]:
    """Return (prompt_six_sections, negativePrompt) for P0xx unit."""
    # Find section starting with # ========== P0xx
    pat = rf"# ========== {re.escape(unit)}[\s\S]*?(?=\n# ========== |\Z)"
    m = re.search(pat, md_text)
    if not m:
        raise SystemExit(f"unit {unit} not found in markdown")
    block = m.group(0)
    pm = re.search(r"\n(subject_definitions:\n[\s\S]*?non_diegetic_music: N/A)", block)
    if not pm:
        raise SystemExit(f"no six-section prompt in {unit}")
    prompt = pm.group(1).strip() + "\n"
    nm = re.search(r"negativePrompt:\s*(.+)", block)
    if not nm:
        raise SystemExit(f"no negativePrompt in {unit}")
    return prompt, nm.group(1).strip()


def audio_duration(path: Path) -> float:
    try:
        import wave
        with wave.open(str(path), "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return 3.0


def build_timeline(prompt: str, negative: str, image_files: list[str], audio_files: list[tuple[str, float]], global_prompt: str) -> dict:
    refs = []
    for i, fn in enumerate(image_files):
        refs.append({"index": i, "imageFile": fn, "fileName": "", "type": "input", "subfolder": ""})
    audios = []
    for i, (fn, dur) in enumerate(audio_files):
        audios.append({
            "index": i,
            "audioFile": fn,
            "fileName": fn.split("/")[-1],
            "type": "input",
            "subfolder": "",
            "durationSec": round(dur, 6),
        })
    seg_id = "ms" + uuid.uuid4().hex[:12]
    seg = {
        "id": seg_id,
        "start": 0,
        "length": FRAMES_15,
        "frameCount": FRAMES_15,
        "durationSec": 15,
        "prompt": prompt,
        "negativePrompt": negative,
        "taskType": "",
        "refs": [],
        "refAudios": [],
        "refVideos": [],
        "genImage": {"imageFile": "", "fileName": ""},
        "continuityFromPrev": False,
        "refImageSize": "match",
    }
    td = {
        "version": 5,
        "editMode": "segment",
        "totalFrames": FRAMES_15,
        "frameRate": 24,
        "video": {},
        "videoClips": [],
        "global": {
            "taskType": "r2v — 参考主体生视频(Reference to Video)",
            "prompt": global_prompt,
            "refs": refs,
            "refAudios": audios,
            "commonEnabled": True,
            "output": {
                "mode": "fixed",
                "aspectRatio": "16:9 (宽屏)",
                "megapixels": 0.6,
                "multiple": 32,
                "longEdge": 1056,
                "width": WIDTH,
                "height": HEIGHT,
                "continuityEnabled": True,
                "continuityOverlapFrames": 22,
                "refImageSize": "match",
            },
        },
        "output": {
            "mode": "fixed",
            "aspectRatio": "16:9 (宽屏)",
            "megapixels": 0.6,
            "multiple": 32,
            "longEdge": 1056,
            "width": WIDTH,
            "height": HEIGHT,
            "maxExportFrames": 0,
            "exportMode": "all",
            "audioMode": "generate",
            "refImageSize": "match",
            "continuityEnabled": True,
            "continuityOverlapFrames": 22,
        },
        "runSelectEnabled": False,
        "runSelection": [],
        "segments": [seg],
        "timelineMode": "prompt_batch",
        "width": WIDTH,
        "height": HEIGHT,
        "refMaxSize": 1056,
        "gen": {},
        "keyframes": [],
        "durationSec": 15,
        "shots": [],
        "liveTaePreview": False,
        "batchDetailMode": False,
        "batchWorkspaces": {"r2v": {"segments": [copy.deepcopy(seg)]}},
        "videoWorkspaces": {},
    }
    # sync negative in batch workspace
    td["batchWorkspaces"]["r2v"]["segments"][0]["negativePrompt"] = negative
    td["batchWorkspaces"]["r2v"]["segments"][0]["prompt"] = prompt
    return td


UNITS = {
    "P01a": {
        "seg": "01",
        "images": [
            ROOT / "05-workflow/归档素材/人物/雷斯特_人设.png",
            ROOT / "05-workflow/归档素材/人物/安娜_人设.png",
            ROOT / "05-images/场景/场景_翠羽社大厅_日漫电影感.png",
        ],
        "audios": [
            ROOT / "05-workflow/归档素材/人物参考音色/雷斯特.wav",
        ],
        "global_prompt": "subject_definitions:\n图片1：雷斯特人设。图片2：安娜人设。图片3：翠羽社大厅场景。\n音频1：雷斯特音色。",
    },
    "P01b": {
        "seg": "01",
        "images": [
            ROOT / "05-workflow/归档素材/人物/雷斯特_人设.png",
            ROOT / "05-workflow/归档素材/人物/安娜_人设.png",
            ROOT / "05-images/场景/场景_翠羽社大厅_日漫电影感.png",
        ],
        "audios": [
            ROOT / "05-workflow/归档素材/人物参考音色/雷斯特.wav",
            ROOT / "05-workflow/归档素材/人物参考音色/安娜.wav",
        ],
        "global_prompt": "subject_definitions:\n图片1：雷斯特人设。图片2：安娜人设。图片3：翠羽社大厅场景。\n音频1：雷斯特。音频2：安娜。",
    },
    "P02": {
        "seg": "02",
        "images": [
            ROOT / "05-workflow/归档素材/人物/陆沉_人设.png",
            ROOT / "05-images/场景/场景_EP05_ND观察室门口_门卫岗_夜_v5.jpg",
        ],
        "audios": [],
        "global_prompt": "subject_definitions:\n图片1：陆沉人设。图片2：ND观察室门口门卫场景。",
    },
    "P03": {
        "seg": "03",
        "images": [
            ROOT / "05-workflow/归档素材/人物/安娜_人设.png",
            ROOT / "05-workflow/归档素材/人物/沈默_人设.png",
            ROOT / "05-images/场景/场景_EP05_沈默电脑房_三巨屏暗室.jpg",
        ],
        "audios": [
            ROOT / "05-workflow/归档素材/人物参考音色/安娜.wav",
            ROOT / "05-workflow/归档素材/人物参考音色/沈默.wav",
        ],
        "global_prompt": "subject_definitions:\n图片1：安娜。图片2：沈默。图片3：电脑房暗室。\n音频1：安娜。音频2：沈默。",
    },
    "P04a": {
        "seg": "04",
        "images": [
            ROOT / "05-workflow/归档素材/人物/安娜_人设.png",
            ROOT / "05-workflow/归档素材/人物/沈默_人设.png",
            ROOT / "05-images/场景/场景_EP05_沈默电脑房_三巨屏暗室.jpg",
            ROOT / "05-images/道具/道具_EP05_复制门禁卡与改装手机.jpg",
        ],
        "audios": [ROOT / "05-workflow/归档素材/人物参考音色/沈默.wav"],
        "global_prompt": "subject_definitions:\n图片1：安娜。图片2：沈默。图片3：电脑房。图片4：手机门禁卡道具。\n音频1：沈默。",
    },
    "P04b": {
        "seg": "04",
        "images": [
            ROOT / "05-workflow/归档素材/人物/安娜_人设.png",
            ROOT / "05-workflow/归档素材/人物/沈默_人设.png",
            ROOT / "05-images/场景/场景_EP05_沈默电脑房_三巨屏暗室.jpg",
            ROOT / "05-images/道具/道具_EP05_复制门禁卡与改装手机.jpg",
        ],
        "audios": [
            ROOT / "05-workflow/归档素材/人物参考音色/安娜.wav",
            ROOT / "05-workflow/归档素材/人物参考音色/沈默.wav",
        ],
        "global_prompt": "subject_definitions:\n图片1：安娜。图片2：沈默。图片3：电脑房。图片4：道具。\n音频1：安娜。音频2：沈默。",
    },
    "P05a": {
        "seg": "05",
        "images": [
            ROOT / "05-workflow/归档素材/人物/安娜_人设.png",
            ROOT / "05-workflow/归档素材/人物/沈默_人设.png",
            ROOT / "05-images/场景/场景_EP05_沈默电脑房_三巨屏暗室.jpg",
            ROOT / "05-images/道具/道具_EP05_复制门禁卡与改装手机.jpg",
        ],
        "audios": [
            ROOT / "05-workflow/归档素材/人物参考音色/安娜.wav",
            ROOT / "05-workflow/归档素材/人物参考音色/沈默.wav",
        ],
        "global_prompt": "subject_definitions:\n图片1：安娜。图片2：沈默。图片3：电脑房。图片4：道具。\n音频1：安娜。音频2：沈默。",
    },
    "P05b": {
        "seg": "05",
        "images": [
            ROOT / "05-workflow/归档素材/人物/安娜_人设.png",
            ROOT / "05-workflow/归档素材/人物/沈默_人设.png",
            ROOT / "05-images/场景/场景_EP05_沈默电脑房_三巨屏暗室.jpg",
            ROOT / "05-images/道具/道具_EP05_复制门禁卡与改装手机.jpg",
        ],
        "audios": [
            ROOT / "05-workflow/归档素材/人物参考音色/安娜.wav",
            ROOT / "05-workflow/归档素材/人物参考音色/沈默.wav",
        ],
        "global_prompt": "subject_definitions:\n图片1：安娜。图片2：沈默。图片3：电脑房。图片4：道具。\n音频1：安娜。音频2：沈默。",
    },
}


def submit_unit(unit: str, poll: bool) -> dict:
    if not API_KEY:
        raise SystemExit("RH_API_KEY / RUNNINGHUB_API_KEY missing")
    meta = UNITS[unit]
    md_path = PKG / f"红绳片段{meta['seg']}" / "H3提示词.md"
    if not md_path.exists():
        # fallback: maybe only on box synced path
        raise SystemExit(f"missing {md_path}")
    prompt, negative = extract_unit(md_path.read_text(encoding="utf-8"), unit)
    for p in meta["images"] + meta["audios"]:
        if not p.exists():
            raise SystemExit(f"missing asset: {p}")
    image_files = [upload(p) for p in meta["images"]]
    audio_files = [(upload(p), audio_duration(p)) for p in meta["audios"]]
    td = build_timeline(prompt, negative, image_files, audio_files, meta["global_prompt"])

    wf = json.loads(WF_TEMPLATE.read_text(encoding="utf-8"))
    node12 = wf["12"]["inputs"]
    node12["timeline_data"] = json.dumps(td, ensure_ascii=False)
    node12["total_frames"] = FRAMES_15
    node12["width"] = WIDTH
    node12["height"] = HEIGHT
    node12["frame_rate"] = 24
    node12["steps"] = 8
    node12["sampler"] = "euler"
    node12["scheduler"] = "simple"
    node12["task_type"] = "r2v — 参考主体生视频(Reference to Video)"
    node12["global_prompt"] = meta["global_prompt"]
    node12["seed"] = 666

    out_dir = PKG / f"红绳片段{meta['seg']}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"timeline_{unit}.json").write_text(json.dumps(td, ensure_ascii=False, indent=2), encoding="utf-8")

    body = {"prompt": wf, "instanceType": "default"}
    print(f"[submit] {unit} ...")
    r = requests.post(SUBMIT_URL, headers=headers(), json=body, timeout=180)
    print("[submit status]", r.status_code)
    try:
        resp = r.json()
    except Exception:
        print(r.text[:1000])
        raise
    print(json.dumps(resp, ensure_ascii=False, indent=2)[:2000])
    task_id = resp.get("taskId") or (resp.get("data") or {}).get("taskId")
    result = {"unit": unit, "taskId": task_id, "raw": resp}
    (out_dir / f"rh_submit_{unit}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if not task_id:
        return result
    if not poll:
        return result
    # poll
    t0 = time.time()
    while time.time() - t0 < 1200:
        time.sleep(15)
        q = requests.post(QUERY_URL, headers=headers(), json={"taskId": task_id}, timeout=60)
        qd = q.json()
        st = qd.get("status") or (qd.get("data") or {}).get("status")
        print(f"[poll] {task_id} status={st}")
        if st in ("SUCCESS", "FAILED", "ERROR"):
            result["query"] = qd
            (out_dir / f"rh_result_{unit}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            if st == "SUCCESS":
                results = qd.get("results") or (qd.get("data") or {}).get("results") or []
                for i, item in enumerate(results):
                    url = item.get("url")
                    if not url:
                        continue
                    ext = "mp4" if "mp4" in url or item.get("outputType") == "mp4" else "bin"
                    dest = out_dir / f"片段{meta['seg']}_{unit}_云端草稿.{ext}"
                    print(f"[download] {url[:80]}... -> {dest}")
                    vr = requests.get(url, timeout=300)
                    dest.write_bytes(vr.content)
                    result["download"] = str(dest)
            break
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", required=True, help="P01a|P01b|P02|... or all01|all05")
    ap.add_argument("--poll", action="store_true")
    args = ap.parse_args()
    units = []
    if args.unit == "all01":
        units = ["P01a", "P01b"]
    elif args.unit == "all05":
        units = ["P01a", "P01b", "P02", "P03", "P04a", "P04b", "P05a", "P05b"]
    else:
        units = [args.unit]
    summary = []
    for u in units:
        summary.append(submit_unit(u, args.poll))
    print("=== SUMMARY ===")
    print(json.dumps([{k: s.get(k) for k in ('unit','taskId','download')} for s in summary], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
