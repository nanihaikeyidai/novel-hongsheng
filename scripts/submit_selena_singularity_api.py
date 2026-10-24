import json
import os
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from submit_selena_action_flow import prompt, upload  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
API_JSON = Path(r"C:\Users\Administrator\.paseo\uploads\upload_5cf64fb1-6bed-4357-9fe6-e8ba10f1fe6f\AIGC___-Minimax-H3____________Singularity__api _1_.json")
WORKFLOW_ID = "2096999459073912833"
CHARACTER = ROOT / "05-workflow" / "归档素材" / "人物" / "赛琳娜_人设.png"
FIRST_FRAME = ROOT / "05-workflow" / "pv素材" / "人物出场首帧" / "赛琳娜_PV出场首帧.png"
OUT_DIR = ROOT / "05-workflow" / "pv素材"
RUN_DIR = ROOT / "05-workflow" / "output" / "pv" / "赛琳娜_动作流"
RUN_DIR.mkdir(parents=True, exist_ok=True)
SUBMIT_URL = f"https://www.runninghub.cn/openapi/v2/run/workflow/{WORKFLOW_ID}"
QUERY_URL = "https://www.runninghub.cn/openapi/v2/query"


def main() -> None:
    key = os.environ.get("RUNNINGHUB_API_KEY", "")
    if not key:
        raise RuntimeError("RUNNINGHUB_API_KEY is not set")
    for p in (API_JSON, CHARACTER, FIRST_FRAME):
        if not p.exists():
            raise FileNotFoundError(p)

    wf = json.loads(API_JSON.read_text(encoding="utf-8"))
    if not all(x in wf for x in ("49", "51", "263", "265", "214")):
        raise RuntimeError("uploaded API JSON does not contain expected Singularity nodes")

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    character_ref = upload(CHARACTER, key)
    first_frame_ref = upload(FIRST_FRAME, key)

    # 真实 API 的引用顺序：节点 51 -> ref_image_0 -> Picture 1；节点 49 -> Picture 2。
    wf["51"]["inputs"]["image"] = character_ref
    wf["49"]["inputs"]["image"] = first_frame_ref
    wf["263"]["inputs"]["text"] = prompt()
    wf["214"]["inputs"]["filename_prefix"] = "Selena_ActionFlow_Corrected"

    prepared = RUN_DIR / "赛琳娜_动作流_Singularity_API_节点参数.json"
    prepared.write_text(json.dumps(wf, ensure_ascii=False, indent=2), encoding="utf-8")

    node_info_list = [
        {"nodeId": "49", "fieldName": "image", "value": first_frame_ref},
        {"nodeId": "51", "fieldName": "image", "value": character_ref},
        {"nodeId": "263", "fieldName": "text", "value": wf["263"]["inputs"]["text"]},
        {"nodeId": "214", "fieldName": "filename_prefix", "value": "Selena_ActionFlow_Corrected"},
    ]
    # Singularity API 需要完整 workflow 作为 prompt；该接口不接受 nodeInfoList 与 prompt 混传。
    body = {"prompt": wf, "instanceType": "plus"}
    resp = requests.post(SUBMIT_URL, headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    submit = resp.json()
    (RUN_DIR / "singularity_submit_response.json").write_text(json.dumps(submit, ensure_ascii=False, indent=2), encoding="utf-8")
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
            (RUN_DIR / "singularity_task_result.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            results = data.get("results") or data.get("data", {}).get("results", [])
            for item in results:
                url = item.get("url") or item.get("outputUrl")
                if url and (item.get("outputType") in ("mp4", "video") or url.lower().split("?")[0].endswith((".mp4", ".mov"))):
                    out = OUT_DIR / "赛琳娜_远距离感知_动作流_15秒_节点参数修正版.mp4"
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
            (RUN_DIR / "singularity_task_result.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            raise RuntimeError(f"task failed: {data}")
    raise TimeoutError("poll timeout")


if __name__ == "__main__":
    main()
