import json
import os
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ID = "2096999459073912833"
WORKFLOW_PATH = ROOT / "05-workflow" / "agents" / "MiniMax H3 导演台全能工作流红绳_api.json"
CHARACTER = ROOT / "05-workflow" / "归档素材" / "人物" / "赛琳娜_人设.png"
FIRST_FRAME = ROOT / "05-workflow" / "pv素材" / "人物出场首帧" / "赛琳娜_PV出场首帧.png"
OUT_DIR = ROOT / "05-workflow" / "pv素材"
RUN_DIR = ROOT / "05-workflow" / "output" / "pv" / "赛琳娜_动作流"
RUN_DIR.mkdir(parents=True, exist_ok=True)

SUBMIT_URL = f"https://www.runninghub.cn/openapi/v2/run/workflow/{WORKFLOW_ID}"
UPLOAD_URL = "https://www.runninghub.cn/openapi/v2/media/upload/binary"
QUERY_URL = "https://www.runninghub.cn/openapi/v2/query"


def upload(path: Path, key: str) -> str:
    with path.open("rb") as f:
        r = requests.post(
            UPLOAD_URL,
            headers={"Authorization": f"Bearer {key}"},
            files={"file": (path.name, f, "image/png")},
            timeout=180,
        )
    r.raise_for_status()
    payload = r.json()
    if payload.get("code") != 0 or not payload.get("data"):
        raise RuntimeError(f"upload failed: {payload}")
    data = payload["data"]
    return data.get("fileName") or data.get("download_url") or data.get("path")


def prompt() -> str:
    return """subject_definitions:
<Subject 1> is Selena from <Picture 1>, the exact adult female mentor identity, face, long dark-brown hair, pale blue-and-white layered outfit, proportions and refined Japanese anime rendering established by Picture 1. Selena is a calm, highly perceptive spatial-systems mentor. Her long-distance perception is an ability, not a device: she can sense distant positions, movement trajectories and hidden spatial disturbances across the city.
<Picture 1> locks Selena's identity, appearance, costume, age and body proportions only. <Picture 2> is Selena's approved PV opening frame and locks the night observatory-like command room, rain-streaked glass, city lights and initial composition only. Do not inherit annotations, text or extra subjects from either image.

summary: A high-density action PV beat in which Selena instantly detects a distant spatial disturbance, maps multiple far-away moving targets, and reacts with large decisive movements. The visual language is fast, sharp and kinetic rather than slow or meditative.

retention_analysis: Preserve Selena's exact face, long dark-brown hair, pale blue-and-white outfit, adult proportions, calm mentor presence, night command-room atmosphere and the original opening composition at 0.00 seconds. Preserve the ability's logic: distant perception appears as expanding transparent spatial grids, luminous sight-lines, concentric range rings and pinpoint trajectory markers across the city, never as a generic magic blast. Allow only the stated camera movement, arm gestures, hair and coat motion, city-light response and spatial overlays to change.

detailed_description: For the target video, at 0.00 seconds into the target video, <Picture 2> (from [Shot 1]) is fully referenced, while <Picture 1> (from [Shot 1]) locks Selena's identity. [Shot 1] 0.00–2.50 seconds: the camera starts in the approved night command room, then makes an immediate fast push-in and hard lateral whip-pan. Selena snaps her head toward the distant skyline, raises one hand sharply, and the dark window behind her blooms into a huge transparent city-scale spatial map. Multiple far-away points ignite at once, connected by bright sight-lines; the motion is crisp and full-speed, no slow motion. [Shot 2] 2.50–5.20 seconds: rapid cut to a wide city view seen through the glass. Selena's perception travels across several districts in one continuous visual sweep: range rings expand from far rooftops, moving figures are represented as tiny luminous trajectories, and hidden disturbances briefly distort the air between buildings. Cut back to a dynamic three-quarter shot as Selena pivots hard, her long hair and coat flaring with the turn, one arm cutting across frame to lock onto a far target. [Shot 3] 5.20–8.10 seconds: fast orbit around Selena. She steps forward decisively and draws three intersecting spatial planes with both hands; the planes stretch from the room through the skyline, showing exact distance, direction and movement vectors. The camera accelerates with the gesture; no floating pause, no dreamy slow motion. [Shot 4] 8.10–11.20 seconds: aggressive montage of close-up eye focus, wide skyline, rooftop trajectory lines and Selena's full-body counter-step. A distant incoming threat is detected before it appears; Selena sharply turns and throws one open-palm spatial mark toward the correct far-off location. The mark is a precise perception lock, not an attack, and the city remains intact. [Shot 5] 11.20–13.70 seconds: Selena crosses the room in three quick grounded steps, reaches the window and sweeps her hand outward. A giant transparent hemispherical perception field expands across the skyline, with hundreds of fine range lines and several bright moving paths updating in real time. The effect is large, readable and physically anchored to her gesture. [Shot 6] 13.70–15.00 seconds: the camera brakes from the rapid motion into a strong final medium-wide hero frame. Selena stands at the window, one hand extended toward the far city, calm eyes fixed on a distant point; the spatial grid remains visible and slowly stabilizes for the final 0.60 seconds. No new action begins in the final hold.

overall_soundscape: rapid fabric and hair movement, decisive footsteps, sharp hand-motion whooshes, glass-window resonance, layered spatial pulses, distant city rain and low electrical ambience from the room; no dialogue.

non_diegetic_music: N/A

visual_style_and_hard_constraints: High-precision Japanese anime cinematic style, delicate cel shading, clean stable linework, hand-painted nocturnal city background, transparent atmospheric perspective, blue-black rainlight and controlled silver-white highlights, 16:9 landscape, 2K-class detail. Make the movement visibly large, forceful and full-speed: rapid push-ins, hard pans, fast orbit, decisive pivots, quick steps and strong arm gestures. Never use slow motion, time dilation, dreamy drifting, frozen posing or minimal movement. Preserve Selena's identity and adult proportions. No live action, photography, 3D render, Western comic, childish cartoon, oil painting, generic energy blast, weapon, combat injury, destruction, extra character, face drift, hairstyle change, costume change, duplicate body, teleportation, subtitles, captions, Chinese characters, title card, speech bubbles, UI, watermark, logo or BGM."""


def timeline(p: str, char_ref: str, frame_ref: str) -> dict:
    refs = [
        {"index": 0, "imageFile": char_ref, "fileName": char_ref, "type": "input", "subfolder": ""},
        {"index": 1, "imageFile": frame_ref, "fileName": frame_ref, "type": "input", "subfolder": ""},
    ]
    neg = "subtitles, captions, on-screen text, Chinese characters, title cards, speech bubbles, UI, watermark, logo, BGM, slow motion, time dilation, dreamy drifting, frozen posing, minimal movement, photorealistic, live action, 3D render, Western comic, childish cartoon, oil painting, generic energy blast, weapon, injury, destruction, extra character, face drift, hairstyle change, costume change, duplicate body, teleportation, unstable final frame"
    seg = {"id": "selena_action_flow_15s", "start": 0, "length": 360, "frameCount": 360, "durationSec": 15, "prompt": p, "negativePrompt": neg, "taskType": "", "refs": refs, "refAudios": [], "refVideos": [], "genImage": {"imageFile": "", "fileName": ""}, "continuityFromPrev": False}
    common = p
    return {"version": 5, "editMode": "segment", "totalFrames": 360, "frameRate": 24, "video": {"fileName": "", "videoFile": "", "subfolder": "", "type": "input", "frames": [], "frameMap": [], "deletedSourceRanges": [], "sourceFrameCount": 360, "width": 0, "height": 0}, "videoClips": [], "global": {"taskType": "r2v — 参考主体生视频(Reference to Video)", "prompt": common, "refs": refs, "referenceVideo": {"videoFile": "", "fileName": "", "type": "input", "subfolder": ""}, "continuousReference": False, "genImage": {"imageFile": ""}, "sourceWidth": 1376, "sourceHeight": 768, "refAudios": [], "refVideos": [], "commonEnabled": True, "commonCollapsed": False}, "output": {"mode": "fixed", "aspectRatio": "16:9 (宽屏)", "megapixels": 2, "multiple": 32, "longEdge": 1376, "width": 1376, "height": 768, "maxExportFrames": 0, "exportMode": "all", "audioMode": "generate", "continuityEnabled": False, "continuityOverlapFrames": 5}, "runSelectEnabled": False, "runSelection": [], "segments": [seg], "timelineMode": "prompt_batch", "width": 1376, "height": 768, "refMaxSize": 1376, "gen": {"defaultFrameCount": 360}, "keyframes": [], "durationSec": 15, "shots": [], "liveTaePreview": True, "batchDetailMode": "solo", "batchWorkspaces": {"r2v": {"selectedIndex": 0, "editMode": "segment", "runSelectEnabled": False, "runSelection": [], "segments": [seg], "globalCommon": {"commonEnabled": True, "commonCollapsed": False, "prompt": common, "refs": refs, "refAudios": [], "refVideos": []}}}}


def main() -> None:
    key = os.environ.get("RUNNINGHUB_API_KEY", "")
    if not key:
        raise RuntimeError("RUNNINGHUB_API_KEY is not set")
    for p in (WORKFLOW_PATH, CHARACTER, FIRST_FRAME):
        if not p.exists():
            raise FileNotFoundError(p)
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    char_ref = upload(CHARACTER, key)
    frame_ref = upload(FIRST_FRAME, key)
    p = prompt()
    td = timeline(p, char_ref, frame_ref)
    wf = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    inputs = wf["12"]["inputs"]
    inputs["task_type"] = "r2v — 参考主体生视频(Reference to Video)"
    inputs["global_prompt"] = p
    inputs["frame_rate"] = 24
    inputs["width"] = 1376
    inputs["height"] = 768
    inputs["ref_max_size"] = 1376
    inputs["total_frames"] = 360
    inputs["timeline_data"] = json.dumps(td, ensure_ascii=False, separators=(",", ":"))
    inputs["seed"] = 666
    wf["7"]["inputs"]["filename_prefix"] = "video/Selena_ActionFlow_15s"
    prepared = RUN_DIR / "赛琳娜_动作流_工作流.json"
    prepared.write_text(json.dumps(wf, ensure_ascii=False, indent=2), encoding="utf-8")
    # 线上“动作流”必须使用节点参数格式提交；直接提交完整本地 workflow JSON
    # 会被线上模板忽略部分输入并回落到默认示例素材。
    node_info_list = []
    for field_name, value in wf["12"]["inputs"].items():
        node_info_list.append({"nodeId": "12", "fieldName": field_name, "value": value})
    resp = requests.post(SUBMIT_URL, headers=headers, json={"nodeInfoList": node_info_list, "instanceType": "plus"}, timeout=120)
    resp.raise_for_status()
    submit = resp.json()
    (RUN_DIR / "submit_response.json").write_text(json.dumps(submit, ensure_ascii=False, indent=2), encoding="utf-8")
    task_id = submit.get("taskId") or submit.get("data", {}).get("taskId")
    if not task_id:
        raise RuntimeError(f"no task id: {submit}")
    print(f"TASK_ID:{task_id}")
    for _ in range(180):
        time.sleep(30)
        q = requests.post(QUERY_URL, headers=headers, json={"taskId": task_id}, timeout=60)
        q.raise_for_status()
        data = q.json()
        status = data.get("status") or data.get("data", {}).get("status")
        print(f"STATUS:{status}", flush=True)
        if status == "SUCCESS":
            (RUN_DIR / "task_result.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            results = data.get("results") or data.get("data", {}).get("results", [])
            for item in results:
                url = item.get("url") or item.get("outputUrl")
                if url and (item.get("outputType") in ("mp4", "video") or url.lower().split("?")[0].endswith((".mp4", ".mov"))):
                    out = OUT_DIR / "赛琳娜_远距离感知_动作流_15秒_节点参数重提.mp4"
                    with requests.get(url, stream=True, timeout=300) as dl:
                        dl.raise_for_status()
                        with out.open("wb") as f:
                            for chunk in dl.iter_content(1024 * 1024):
                                if chunk:
                                    f.write(chunk)
                    print(f"OUTPUT_FILE:{out}")
                    return
            raise RuntimeError(f"success without video result: {data}")
        if status == "FAILED":
            (RUN_DIR / "task_result.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            raise RuntimeError(f"task failed: {data}")
    raise TimeoutError("poll timeout")


if __name__ == "__main__":
    main()
