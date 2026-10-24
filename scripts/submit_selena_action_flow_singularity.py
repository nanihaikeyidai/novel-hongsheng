import json
import os
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ID = "2096999459073912833"
WORKFLOW_PATH = ROOT / "05-workflow" / "agents" / "AIGC特异点-Minimax-H3多参考双采放大生成视频（Singularity）_api.json"
CHARACTER = ROOT / "05-workflow" / "归档素材" / "人物" / "赛琳娜_人设.png"
FIRST_FRAME = ROOT / "05-workflow" / "pv素材" / "人物出场首帧" / "赛琳娜_PV出场首帧.png"
OUT_DIR = ROOT / "05-workflow" / "pv素材"
RUN_DIR = ROOT / "05-workflow" / "output" / "pv" / "赛琳娜_动作流_singularity"
RUN_DIR.mkdir(parents=True, exist_ok=True)

SUBMIT_URL = f"https://www.runninghub.cn/openapi/v2/run/workflow/{WORKFLOW_ID}"
UPLOAD_URL = "https://www.runninghub.cn/openapi/v2/media/upload/binary"
QUERY_URL = "https://www.runninghub.cn/openapi/v2/query"


def upload(path: Path, key: str) -> str:
    with path.open("rb") as handle:
        response = requests.post(
            UPLOAD_URL,
            headers={"Authorization": f"Bearer {key}"},
            files={"file": (path.name, handle, "image/png")},
            timeout=180,
        )
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != 0 or not payload.get("data"):
        raise RuntimeError(f"素材上传失败: {payload}")
    data = payload["data"]
    return data.get("fileName") or data.get("download_url") or data.get("path")


def build_prompt() -> str:
    return """subject_definitions:
<Subject 1> is Selena from <Picture 1>, the exact adult female mentor identity, face, long dark-brown hair, pale blue-and-white layered outfit, adult proportions and refined high-precision Japanese anime rendering established by Picture 1. Selena possesses long-distance perception: she senses distant positions, movement trajectories and hidden spatial disturbances across the city without using a device.
<Picture 1> locks Selena's identity, face, hair, costume and proportions only. <Picture 2> is the approved PV opening frame and locks the night command room, rain-streaked glass, city lights and opening composition only. Do not inherit text, annotations or extra subjects.

summary:
[keyframe completion + reference generation] Generate a 15-second, 16:9 landscape, 2K-class anime action PV. Selena instantly detects a distant spatial disturbance, maps multiple far-away moving targets and reacts with large decisive movements. The rhythm is fast, sharp and kinetic, with no slow motion or dreamy drifting. Keep the city intact and make the perception ability readable as spatial information rather than a generic attack.

retention_analysis:
Preserve Selena's exact face, long dark-brown hair, pale blue-and-white layered outfit, adult body proportions and calm mentor presence from <Picture 1>. Preserve <Picture 2>'s night command room, rain-streaked window, blue-black city lights and initial composition at 0.00 seconds. Preserve the ability logic: expanding transparent spatial grids, luminous sight-lines, concentric range rings, pinpoint trajectory markers and distant-location locks. Only camera motion, grounded body movement, hair and coat motion, city-light response and spatial overlays may change. No identity drift, costume change, duplicate body, teleportation or extra character.

detailed_description:
At 0.00 seconds, <Picture 2> from [Shot 1] is fully referenced while <Picture 1> locks Selena's identity. [Shot 1] 0.00–2.50s: immediate fast push-in and hard lateral whip-pan; Selena snaps her head toward the skyline, raises one hand, and the window blooms into a huge transparent city-scale map with several distant points and bright sight-lines. [Shot 2] 2.50–5.20s: rapid wide sweep across several city districts; range rings expand from far rooftops, moving targets become luminous trajectories, and hidden disturbances distort the air; cut back as Selena pivots hard and cuts one arm across frame. [Shot 3] 5.20–8.10s: fast orbit around Selena; she takes a decisive step and draws three intersecting spatial planes through the skyline, showing exact distance, direction and movement vectors. [Shot 4] 8.10–11.20s: aggressive montage of focused eyes, skyline, rooftop trajectories and a full-body counter-step; Selena detects an unseen distant threat before it appears and throws a precise open-palm perception lock, not an attack. [Shot 5] 11.20–13.70s: she crosses the room in three quick grounded steps and sweeps her hand outward; a giant transparent hemispherical perception field expands across the skyline with hundreds of fine range lines updating in real time. [Shot 6] 13.70–15.00s: rapid motion brakes into a strong medium-wide hero frame; Selena stands at the window with one hand extended, the spatial grid stabilizing for the final 0.60s. Use crisp full-speed movement, large readable gestures, rapid push-ins, hard pans and fast orbit. Never use slow motion, time dilation, frozen posing, minimal movement or dreamy drifting. Use high-precision Japanese anime cinematic style, delicate cel shading, stable linework, hand-painted nocturnal city, transparent atmospheric perspective, blue-black rainlight and restrained silver-white highlights. No live action, photography, 3D render, Western comic, childish cartoon, oil painting, generic energy blast, weapon, injury, destruction, subtitles, captions, Chinese characters, title card, speech bubbles, UI, watermark, logo or BGM.

overall_soundscape:
Rapid fabric and hair movement, decisive grounded footsteps, sharp hand-motion whooshes, glass-window resonance, layered spatial pulses, distant city rain and low electrical room ambience; no dialogue, no music.

non_diegetic_music:
N/A"""


def extract_video_url(payload: dict) -> str | None:
    results = payload.get("results") or payload.get("data", {}).get("results", [])
    for item in results:
        url = item.get("url") or item.get("outputUrl")
        if url and (item.get("outputType") in {"mp4", "video"} or url.lower().split("?")[0].endswith((".mp4", ".mov"))):
            return url
    return None


def main() -> None:
    key = os.environ.get("RUNNINGHUB_API_KEY", "")
    if not key:
        raise RuntimeError("RUNNINGHUB_API_KEY 未设置")
    for path in (WORKFLOW_PATH, CHARACTER, FIRST_FRAME):
        if not path.exists():
            raise FileNotFoundError(path)

    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    prompt = build_prompt()
    character_remote = upload(CHARACTER, key)
    first_frame_remote = upload(FIRST_FRAME, key)

    # 本地副本记录本次真正提交的素材绑定与节点参数，便于复核。
    prepared = json.loads(json.dumps(workflow, ensure_ascii=False))
    # 真实连接：265.ref_image_0 ← 51，265.ref_image_1 ← 49。
    # 因此 51 绑定人物图（Picture 1），49 绑定首帧（Picture 2）。
    prepared["51"]["inputs"]["image"] = character_remote
    prepared["49"]["inputs"]["image"] = first_frame_remote
    prepared["263"]["inputs"]["text"] = prompt
    prepared["259"]["inputs"]["value"] = 15.0
    prepared["252"]["inputs"]["megapixels"] = 0.5
    prepared["264"]["inputs"]["filename_prefix"] = "Selena_ActionFlow_NewPV_15s"
    prepared["214"]["inputs"]["filename_prefix"] = "Selena_ActionFlow_NewPV_15s"
    (RUN_DIR / "赛琳娜_新版PV_动作流_提交工作流.json").write_text(
        json.dumps(prepared, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (RUN_DIR / "赛琳娜_新版PV_动作流_提示词.txt").write_text(prompt, encoding="utf-8")

    # 只覆盖真实 Singularity 工作流中存在的节点，避免旧导演台 node 12 误提交。
    node_info_list = [
        {"nodeId": "51", "fieldName": "image", "fieldValue": character_remote},
        {"nodeId": "49", "fieldName": "image", "fieldValue": first_frame_remote},
        {"nodeId": "263", "fieldName": "text", "fieldValue": prompt},
        {"nodeId": "259", "fieldName": "value", "fieldValue": 15.0},
        {"nodeId": "252", "fieldName": "megapixels", "fieldValue": 0.5},
        {"nodeId": "264", "fieldName": "filename_prefix", "fieldValue": "Selena_ActionFlow_NewPV_15s"},
        {"nodeId": "214", "fieldName": "filename_prefix", "fieldValue": "Selena_ActionFlow_NewPV_15s"},
    ]
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    response = requests.post(SUBMIT_URL, headers=headers, json={"nodeInfoList": node_info_list, "instanceType": "plus"}, timeout=120)
    response.raise_for_status()
    submitted = response.json()
    (RUN_DIR / "submit_response.json").write_text(json.dumps(submitted, ensure_ascii=False, indent=2), encoding="utf-8")
    task_id = submitted.get("taskId") or submitted.get("data", {}).get("taskId")
    if not task_id:
        raise RuntimeError(f"RunningHub 未返回 taskId: {submitted}")
    print(f"TASK_ID:{task_id}", flush=True)

    for attempt in range(180):
        time.sleep(20)
        query = requests.post(QUERY_URL, headers=headers, json={"taskId": task_id}, timeout=60)
        query.raise_for_status()
        payload = query.json()
        status = payload.get("status") or payload.get("data", {}).get("status")
        print(f"STATUS:{status} ATTEMPT:{attempt + 1}", flush=True)
        if str(status).upper() in {"SUCCESS", "COMPLETED"}:
            (RUN_DIR / "task_result.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            url = extract_video_url(payload)
            if not url:
                raise RuntimeError(f"任务成功但未找到视频结果: {payload}")
            output = OUT_DIR / "赛琳娜_新版PV_动作流_15秒.mp4"
            with requests.get(url, stream=True, timeout=300) as download:
                download.raise_for_status()
                with output.open("wb") as handle:
                    for chunk in download.iter_content(1024 * 1024):
                        if chunk:
                            handle.write(chunk)
            print(f"OUTPUT_FILE:{output}", flush=True)
            return
        if str(status).upper() in {"FAILED", "ERROR"}:
            (RUN_DIR / "task_result.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            raise RuntimeError(f"RunningHub 任务失败: {payload}")
    raise TimeoutError("RunningHub 轮询超过 60 分钟")


if __name__ == "__main__":
    main()
