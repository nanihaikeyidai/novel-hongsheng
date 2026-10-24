import json
import os
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ID = "2096999459073912833"
WORKFLOW_PATH = ROOT / "05-workflow" / "agents" / "MiniMax H3 导演台全能工作流红绳_api.json"
OUT_DIR = ROOT / "05-workflow" / "output" / "pv" / "唐小满_vs_天云" / "runninghub"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SUBMIT_URL = f"https://www.runninghub.cn/openapi/v2/run/workflow/{WORKFLOW_ID}"
UPLOAD_URL = "https://www.runninghub.cn/openapi/v2/media/upload/binary"
QUERY_URL = "https://www.runninghub.cn/openapi/v2/query"


def api_key() -> str:
    key = os.environ.get("RUNNINGHUB_API_KEY", "")
    if not key:
        raise RuntimeError("RUNNINGHUB_API_KEY is not set")
    return key


def upload_image(path: Path, headers: dict) -> str:
    with path.open("rb") as f:
        resp = requests.post(
            UPLOAD_URL,
            headers={"Authorization": headers["Authorization"]},
            files={"file": (path.name, f, "image/png")},
            timeout=180,
        )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") not in (0, "0", None) and not data.get("data"):
        raise RuntimeError(f"upload failed: {data}")
    payload = data.get("data", data)
    name = payload.get("fileName") or payload.get("file_name") or payload.get("path")
    if not name and payload.get("download_url"):
        name = payload["download_url"]
    if not name:
        raise RuntimeError(f"upload response has no file name: {data}")
    return name


def build_prompt() -> str:
    return """subject_definitions:
<Subject 1> is Tang Xiaoman from <Picture 1>, a fictional 12-year-old girl about 140 cm tall, with the exact childlike face, warm chestnut-red hair in one large fluffy messy bun, jeweled tiara, ivory-and-burgundy aristocratic princess dress, and impatient highborn expression locked to Picture 1. She uses a supernatural repulsion field: a translucent pale-violet spherical pressure field and concentric air-ring distortions, never a weapon.
<Subject 2> is Tianyun from <Picture 2>, the adult female mentor with the exact face, hairstyle, outfit, proportions and anime rendering locked to Picture 2. She practices Chinese martial arts with disciplined, controlled movement, using empty-hand forms only.
Picture 1 locks Tang Xiaoman's identity, child proportions, costume and palette only. Picture 2 locks Tianyun's identity, adult proportions, costume and palette only. Neither picture supplies a background or additional character.

CONTINUITY — HARD CONSTRAINTS
Both subjects remain present throughout. Tianyun is always the mentor and controls the pace; Tang Xiaoman is always the 12-year-old student. They train in an open traditional Chinese martial-arts courtyard with stone floor, wooden practice posts and distant tiled eaves. Keep their world positions coherent: Tianyun starts screen-right facing left, Tang Xiaoman starts screen-left facing right; preserve this axis during cuts. No injury, no contact violence, no weapons, no costume changes.

For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) and <Picture 2> (from [Shot 1]) are fully referenced.

integrated_multimodal_description: [Shot 1] 0.00–2.20 seconds, extreme wide establishing shot of the traditional Chinese training courtyard at cool dawn. Tianyun stands screen-right in a grounded horse stance, calmly demonstrating a compact Chinese martial-arts palm sequence; Tang Xiaoman stands screen-left, visibly impatient, mirroring the stance with smaller child-scale movement. The camera rushes forward with a fast low dolly and a brief whip-pan between them, but the left-right axis stays fixed. [Shot 2] 2.20–5.00 seconds, rapid medium close-ups cut on movement: Tianyun pivots, parries an incoming training palm without touching Tang Xiaoman, and redirects the force into a wooden post; Tang Xiaoman lunges one step, her dress and single bun trailing naturally. Use crisp hand and foot action, readable anatomy, and short speed-ramped motion accents. [Shot 3] 5.00–8.00 seconds, Tang Xiaoman thrusts both palms forward and activates a translucent pale-violet repulsion field; concentric pressure rings expand across the courtyard, dust and loose leaves lift outward, and Tianyun slides backward two controlled steps while maintaining a stable martial-arts guard. The field visibly stops before Tianyun and causes no injury. Camera performs a fast orbit around the pressure wave, preserving both characters. [Shot 4] 8.00–11.80 seconds, alternating fast flash cuts: Tianyun uses a flowing Chinese baguazhang-inspired sidestep, low sweep and open-palm feint; Tang Xiaoman counters with two short repulsion bursts that bend dust, fabric and falling leaves away from her palms. Each burst has a clear start, expansion and fade; no random explosions. [Shot 5] 11.80–13.80 seconds, medium-wide two-shot. Tianyun leaps over a low pressure wave, lands softly in a centered guard, then raises one hand to signal Tang Xiaoman to stop. Tang Xiaoman brakes her field, cheeks puffed in frustration, and settles into a guarded stance. [Shot 6] 13.80–15.00 seconds, clean final hero frame: both remain fully visible in the courtyard, Tianyun screen-right calm and composed, Tang Xiaoman screen-left proud and irritated, faint violet pressure rings fading around Tang Xiaoman's hands. The camera finishes its motion and holds a readable stable composition for the final 0.60 seconds; only hair, dress hems, dust and leaves make subtle low-amplitude motion.

overall_soundscape: crisp cloth swishes, light footfalls on stone, palm strikes cutting air, wooden post impact, controlled breath, expanding pressure-wave rumbles, dust and leaves scattering, and a final soft settling wind; no spoken dialogue.

non_diegetic_music: N/A

visual_style_and_hard_constraints: High-precision Japanese anime cinematic style, delicate cel shading, clean stable linework, hand-painted animation background, transparent atmospheric perspective, dynamic action-film lighting, 16:9 landscape, 2K-class detail. Keep Tang Xiaoman visibly childlike and approximately 140 cm tall, never adult or sexualized. Keep Tianyun clearly adult and mentor-like. Fast camera cuts and fast readable martial-arts movement, but preserve identity, anatomy, spatial axis and causal action. No live action, no photography, no 3D render, no Western comic, no childish cartoon, no oil painting, no gore, no injury, no weapons, no extra characters, no duplicate bodies, no teleportation, no costume change, no face drift, no subtitles, no captions, no Chinese characters, no title card, no speech bubbles, no UI, no watermark, no logo, no BGM, no unstable final frame."""


def build_timeline(prompt: str, ref1: str, ref2: str) -> dict:
    frames = 360
    negative = "subtitles, captions, on-screen text, Chinese characters, title cards, speech bubbles, UI, watermark, logo, BGM, photorealistic, live action, 3D render, Western comic, childish cartoon, oil painting, adult Tang Xiaoman, sexualized child, identity drift, face change, hairstyle change, costume change, extra character, duplicated body parts, teleportation, weapons, gore, injury, unstable anatomy, unstable final frame"
    refs = [
        {"index": 0, "imageFile": ref1, "fileName": ref1, "type": "input", "subfolder": ""},
        {"index": 1, "imageFile": ref2, "fileName": ref2, "type": "input", "subfolder": ""},
    ]
    seg = {
        "id": "tangxiaoman_tianyun_flash_pv_15s",
        "start": 0,
        "length": frames,
        "frameCount": frames,
        "durationSec": 15,
        "prompt": prompt,
        "negativePrompt": negative,
        "taskType": "",
        "refs": refs,
        "refAudios": [],
        "refVideos": [],
        "genImage": {"imageFile": "", "fileName": ""},
        "continuityFromPrev": False,
    }
    return {
        "version": 5,
        "editMode": "segment",
        "totalFrames": frames,
        "frameRate": 24,
        "video": {"fileName": "", "videoFile": "", "subfolder": "", "type": "input", "frames": [], "frameMap": [], "deletedSourceRanges": [], "sourceFrameCount": frames, "width": 0, "height": 0},
        "videoClips": [],
        "global": {"taskType": "r2v — 参考主体生视频(Reference to Video)", "prompt": prompt.split("\n\nFor the target video")[0], "refs": refs, "referenceVideo": {"videoFile": "", "fileName": "", "type": "input", "subfolder": ""}, "continuousReference": False, "genImage": {"imageFile": ""}, "sourceWidth": 1376, "sourceHeight": 768, "refAudios": [], "refVideos": [], "commonEnabled": True, "commonCollapsed": False},
        "output": {"mode": "fixed", "aspectRatio": "16:9 (宽屏)", "megapixels": 2, "multiple": 32, "longEdge": 1376, "width": 1376, "height": 768, "maxExportFrames": 0, "exportMode": "all", "audioMode": "generate", "continuityEnabled": False, "continuityOverlapFrames": 5},
        "runSelectEnabled": False,
        "runSelection": [],
        "segments": [seg],
        "timelineMode": "prompt_batch",
        "width": 1376,
        "height": 768,
        "refMaxSize": 1376,
        "gen": {"defaultFrameCount": frames},
        "keyframes": [],
        "durationSec": 15,
        "shots": [],
        "liveTaePreview": True,
        "batchDetailMode": "solo",
        "batchWorkspaces": {"r2v": {"selectedIndex": 0, "editMode": "segment", "runSelectEnabled": False, "runSelection": [], "segments": [seg], "globalCommon": {"commonEnabled": True, "commonCollapsed": False, "prompt": prompt.split("\n\nFor the target video")[0], "refs": refs, "refAudios": [], "refVideos": []}}},
    }


def main() -> None:
    key = api_key()
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    tang = ROOT / "05-workflow" / "归档素材" / "人物" / "唐小满_人设.png"
    tian = ROOT / "05-workflow" / "归档素材" / "人物" / "天云_人设.png"
    for p in (tang, tian, WORKFLOW_PATH):
        if not p.exists():
            raise FileNotFoundError(p)

    ref1 = upload_image(tang, headers)
    ref2 = upload_image(tian, headers)
    prompt = build_prompt()
    timeline = build_timeline(prompt, ref1, ref2)
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    node = workflow["12"]["inputs"]
    node["task_type"] = "r2v — 参考主体生视频(Reference to Video)"
    node["global_prompt"] = timeline["global"]["prompt"]
    node["width"] = 1376
    node["height"] = 768
    node["frame_rate"] = 24
    node["total_frames"] = 360
    node["ref_max_size"] = 1376
    node["timeline_data"] = json.dumps(timeline, ensure_ascii=False, separators=(",", ":"))
    node["seed"] = 666
    node["steps"] = 20
    node["refine"][0] if False else None
    workflow["7"]["inputs"]["filename_prefix"] = "video/TangXiaoman_Tianyun_FlashPV"

    prepared = OUT_DIR / "tangxiaoman_tianyun_workflow_prepared.json"
    prepared.write_text(json.dumps(workflow, ensure_ascii=False, indent=2), encoding="utf-8")
    body = {"prompt": workflow, "instanceType": "plus", "addMetadata": True}
    resp = requests.post(SUBMIT_URL, headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    submit = resp.json()
    (OUT_DIR / "submit_response.json").write_text(json.dumps(submit, ensure_ascii=False, indent=2), encoding="utf-8")
    task_id = submit.get("taskId") or submit.get("data", {}).get("taskId")
    if not task_id:
        raise RuntimeError(f"no task id: {submit}")
    print(f"TASK_ID:{task_id}")

    for _ in range(180):
        time.sleep(30)
        q = requests.post(QUERY_URL, headers=headers, json={"taskId": task_id}, timeout=60)
        q.raise_for_status()
        result = q.json()
        status = result.get("status") or result.get("data", {}).get("status")
        print(f"STATUS:{status}", flush=True)
        if status == "SUCCESS":
            (OUT_DIR / "task_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            results = result.get("results") or result.get("data", {}).get("results", [])
            for item in results:
                url = item.get("url") or item.get("outputUrl")
                if url and (item.get("outputType") in ("mp4", "video") or url.lower().split("?")[0].endswith((".mp4", ".mov"))):
                    out = ROOT / "05-workflow" / "output" / "pv" / "唐小满_vs_天云" / "唐小满_vs_天云_武戏快闪PV_15秒.mp4"
                    with requests.get(url, stream=True, timeout=300) as dl:
                        dl.raise_for_status()
                        with out.open("wb") as f:
                            for chunk in dl.iter_content(1024 * 1024):
                                if chunk:
                                    f.write(chunk)
                    print(f"OUTPUT_FILE:{out}")
                    return
            raise RuntimeError(f"success without video result: {result}")
        if status == "FAILED":
            (OUT_DIR / "task_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            raise RuntimeError(f"task failed: {result}")
    raise TimeoutError("poll timeout")


if __name__ == "__main__":
    main()
