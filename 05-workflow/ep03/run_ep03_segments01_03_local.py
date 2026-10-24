from __future__ import annotations

import copy
import json
import shutil
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
API_PATH = Path(r"F:\ComfyUI_V6.0\MiniMax H3 导演台全能工作流_api.json")
COMFY_INPUT = Path(r"F:\Work-Fisher纯净包2026.8.7\ComfyUI\input")
COMFY_URL = "http://127.0.0.1:8188"
RUN_DIR = ROOT / "05-workflow" / "ep03" / "local_runs" / "segments01_03_long"
OUTPUT_DIR = ROOT / "05-workflow" / "ep03" / "视频长片段"

GLOBAL_ASSETS = [
    (ROOT / "05-workflow/ep03/归档素材/人物/安娜_人设.png", "redstring_ep03_anna_school.png"),
    (ROOT / "05-workflow/ep03/归档素材/人物/安娜_游泳社人设.png", "redstring_ep03_anna_swim.png"),
    (ROOT / "05-workflow/ep03/归档素材/场景/场景_红杉高中校门_晴天_无人.png", "redstring_ep03_school_gate.png"),
    (ROOT / "05-workflow/ep03/归档素材/场景/场景_室内标准泳池_无人.png", "redstring_ep03_pool.png"),
    (ROOT / "05-workflow/ep03/归档素材/场景/场景_室内泳池起跳端_无人.png", "redstring_ep03_pool_start.png"),
]

SEGMENTS = [
    ("ep03_p01_school_gate", "EP03-P01", "红绳片段01", []),
    (
        "ep03_p02_noticeboard_anna_passes",
        "EP03-P02",
        "红绳片段02",
        [(ROOT / "05-workflow/ep03/归档素材/场景/场景_社团公告栏走廊_无人.png", "redstring_ep03_noticeboard.png")],
    ),
    (
        "ep03_p03_indoor_pool_gathering",
        "EP03-P03",
        "红绳片段03",
        [(ROOT / "05-workflow/ep03/归档素材/道具/游泳社训练套件.png", "redstring_ep03_swim_kit.png")],
    ),
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def copy_assets() -> list[dict]:
    COMFY_INPUT.mkdir(parents=True, exist_ok=True)
    refs = []
    for index, (source, target) in enumerate(GLOBAL_ASSETS):
        if not source.is_file():
            raise FileNotFoundError(f"缺少参考素材：{source}")
        shutil.copy2(source, COMFY_INPUT / target)
        refs.append({"index": index, "imageFile": target, "fileName": target, "type": "input", "subfolder": ""})
    return refs


def copy_segment_assets(items: list[tuple[Path, str]]) -> list[dict]:
    refs = []
    for offset, (source, target) in enumerate(items, start=5):
        if not source.is_file():
            raise FileNotFoundError(f"缺少分段参考素材：{source}")
        shutil.copy2(source, COMFY_INPUT / target)
        refs.append({"index": offset, "imageFile": target, "fileName": target, "type": "input", "subfolder": ""})
    return refs


def parse_negative(prompt: str) -> str:
    marker = "## negativePrompt"
    end = "## 连续性出点"
    if marker not in prompt or end not in prompt:
        raise ValueError("提示词缺少 negativePrompt 或 连续性出点段落")
    value = prompt.split(marker, 1)[1].split(end, 1)[0].strip()
    value = value.replace("```text", "").replace("```", "").strip()
    if not value:
        raise ValueError("negativePrompt 为空")
    return value


def segment(prompt_path: Path, segment_id: str, name: str, start: int, refs: list[dict], continuity: bool) -> dict:
    prompt = prompt_path.read_text(encoding="utf-8")
    if not prompt.startswith("subject_definitions:"):
        raise ValueError(f"提示词第一行不是 subject_definitions: {prompt_path}")
    negative = parse_negative(prompt)
    return {
        "id": segment_id,
        "name": name,
        "startFrame": start,
        "length": 362,
        "frameCount": 362,
        "duration": 15,
        "prompt": prompt,
        "negativePrompt": negative,
        "taskType": "",
        "refs": refs,
        "refAudios": [],
        "refVideos": [],
        "genImage": {"imageFile": "", "fileName": ""},
        "continuityFromPrev": continuity,
        "refImageSize": "match",
        "referenceVideo": {"videoFile": "", "fileName": "", "type": "input", "subfolder": ""},
    }


def build_workflow() -> tuple[dict, dict]:
    source = read_json(API_PATH)
    workflow = copy.deepcopy(source)
    global_refs = copy_assets()
    segment_values = []
    start = 0
    for segment_id, name, directory, extra in SEGMENTS:
        extra_refs = copy_segment_assets(extra)
        prompt_path = ROOT / "05-workflow" / "ep03" / directory / "视频提示词.md"
        value = segment(prompt_path, segment_id, name, start, extra_refs, start > 0)
        segment_values.append(value)
        start += 362

    global_prompt = """subject_definitions:
图片1：安娜校服人物参考图，只锁定安娜的身份、深蓝长发、年龄感、体态和校服；不继承背景、文字或姿势。
图片2：安娜游泳社人物参考图，只锁定安娜进入泳池后的深蓝长发、泳池服装和体态；不继承背景、文字或姿势。
图片3：红杉高中校门晴天场景参考图，只锁定校门、中央校徽、红杉树、铁门、教学楼和晴朗早晨光线。
图片4：室内标准泳池场景参考图，只锁定明亮蓝白泳池、六条泳道、长椅、远端池壁和室内天光。
图片5：室内泳池起跳端场景参考图，只锁定起跳端与泳道正对的空间关系；不提前生成跳台上的人物。
故事板已本地查看并转化为三个分段提示词中的文字化镜头顺序、景别、站位、动作节拍和出点状态；本次不上传任何故事板图片、线稿故事板或六宫格图。所有片段均无字幕、无画面文字、无BGM、无水印、无Logo。"""

    timeline = read_json(API_PATH)  # 重新读取源结构，避免旧 timeline 摘要覆盖原文件
    timeline = timeline["12"]["inputs"]["timeline_data"]
    timeline = json.loads(timeline)
    timeline["editMode"] = "segment"
    timeline["totalFrames"] = 1086
    timeline["frameRate"] = 24
    timeline["durationSec"] = 45
    timeline["video"]["sourceFrameCount"] = 0
    timeline["global"]["taskType"] = "r2v — 参考主体生视频(Reference to Video)"
    timeline["global"]["prompt"] = global_prompt
    timeline["global"]["refs"] = global_refs
    timeline["global"]["refAudios"] = []
    timeline["global"]["refVideos"] = []
    timeline["global"]["commonEnabled"] = True
    timeline["global"]["commonCollapsed"] = False
    timeline["output"]["mode"] = "fixed"
    timeline["output"]["aspectRatio"] = "16:9 (宽屏)"
    timeline["output"]["megapixels"] = 1
    timeline["output"]["multiple"] = 32
    timeline["output"]["longEdge"] = 1376
    timeline["output"]["width"] = 1376
    timeline["output"]["height"] = 768
    timeline["output"]["exportMode"] = "all"
    timeline["output"]["audioMode"] = "generate"
    timeline["output"]["continuityEnabled"] = True
    timeline["output"]["continuityOverlapFrames"] = 22
    timeline["runSelectEnabled"] = True
    timeline["runSelection"] = [0, 1, 2]
    timeline["segments"] = segment_values
    timeline["width"] = 1376
    timeline["height"] = 768
    timeline["refMaxSize"] = 1376
    timeline["batchWorkspaces"]["r2v"]["selectedIndex"] = 0
    timeline["batchWorkspaces"]["r2v"]["editMode"] = "segment"
    timeline["batchWorkspaces"]["r2v"]["runSelectEnabled"] = True
    timeline["batchWorkspaces"]["r2v"]["runSelection"] = [0, 1, 2]
    timeline["batchWorkspaces"]["r2v"]["segments"] = copy.deepcopy(segment_values)
    timeline["batchWorkspaces"]["r2v"]["globalCommon"]["commonEnabled"] = True
    timeline["batchWorkspaces"]["r2v"]["globalCommon"]["prompt"] = global_prompt
    timeline["batchWorkspaces"]["r2v"]["globalCommon"]["refs"] = global_refs
    timeline["batchWorkspaces"]["r2v"]["globalCommon"]["refAudios"] = []
    timeline["batchWorkspaces"]["r2v"]["globalCommon"]["refVideos"] = []

    # Verify both segment arrays and negativePrompt synchronization before submission.
    if len(timeline["segments"]) != 3 or len(timeline["batchWorkspaces"]["r2v"]["segments"]) != 3:
        raise ValueError("导演台分段数量不是3")
    if sum(s["length"] for s in timeline["segments"]) != timeline["totalFrames"]:
        raise ValueError("总帧数与三段帧数不一致")
    for index, value in enumerate(timeline["segments"]):
        mirror = timeline["batchWorkspaces"]["r2v"]["segments"][index]
        if value["negativePrompt"] != mirror["negativePrompt"]:
            raise ValueError(f"第{index + 1}段 negativePrompt 未同步")
        if index > 0 and not value["continuityFromPrev"]:
            raise ValueError(f"第{index + 1}段未启用 continuityFromPrev")
        if index == 0 and value["continuityFromPrev"]:
            raise ValueError("第一段不应启用 continuityFromPrev")

    workflow["12"]["inputs"]["task_type"] = "r2v — 参考主体生视频(Reference to Video)"
    workflow["12"]["inputs"]["global_prompt"] = global_prompt
    workflow["12"]["inputs"]["frame_rate"] = 24
    workflow["12"]["inputs"]["width"] = 1376
    workflow["12"]["inputs"]["height"] = 768
    workflow["12"]["inputs"]["ref_max_size"] = 1376
    workflow["12"]["inputs"]["total_frames"] = 1086
    workflow["12"]["inputs"]["timeline_data"] = json.dumps(timeline, ensure_ascii=False, separators=(",", ":"))
    workflow["7"]["inputs"]["filename_prefix"] = "video/RedString_EP03_segments01_03_local_long"
    return workflow, timeline


def request_json(url: str, method: str = "GET", data: bytes | None = None) -> dict:
    request = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_history(prompt_id: str) -> dict:
    last_report = 0.0
    while True:
        history = request_json(f"{COMFY_URL}/history/{urllib.parse.quote(prompt_id)}")
        if prompt_id in history:
            result = history[prompt_id]
            status = result.get("status", {})
            if status.get("status_str") == "error" or status.get("completed") is False and status.get("messages"):
                if status.get("status_str") == "error":
                    raise RuntimeError(json.dumps(status, ensure_ascii=False))
            if result.get("outputs"):
                return result
        now = time.time()
        if now - last_report > 30:
            print("本地导演台仍在生成，已等待约 %.1f 分钟。" % ((now - last_report) / 60), flush=True)
            last_report = now
        time.sleep(5)


def locate_video(history: dict) -> dict:
    outputs = history.get("outputs", {})
    candidates = []
    for node_output in outputs.values():
        if not isinstance(node_output, dict):
            continue
        for key in ("videos", "gifs", "files"):
            values = node_output.get(key, [])
            if isinstance(values, dict):
                values = [values]
            for item in values:
                if isinstance(item, dict) and item.get("filename"):
                    candidates.append(item)
    if not candidates:
        raise RuntimeError("历史记录已完成，但没有找到视频输出")
    mp4 = [item for item in candidates if str(item.get("filename", "")).lower().endswith((".mp4", ".mov", ".webm"))]
    return (mp4 or candidates)[-1]


def download_video(item: dict, output: Path) -> None:
    query = urllib.parse.urlencode({
        "filename": item["filename"],
        "subfolder": item.get("subfolder", ""),
        "type": item.get("type", "output"),
    })
    with urllib.request.urlopen(f"{COMFY_URL}/view?{query}", timeout=120) as response:
        output.write_bytes(response.read())


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    workflow, timeline = build_workflow()
    write_json(RUN_DIR / "timeline_data_EP03_segments01_03.json", timeline)
    write_json(RUN_DIR / "工作流_提交.json", workflow)
    payload = json.dumps({"prompt": workflow, "client_id": str(uuid.uuid4())}, ensure_ascii=False).encode("utf-8")
    print("提交本地 MiniMax H3 导演台：EP03 片段1–3，45秒长视频。", flush=True)
    response = request_json(f"{COMFY_URL}/prompt", method="POST", data=payload)
    prompt_id = response.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(json.dumps(response, ensure_ascii=False))
    print("PROMPT_ID=" + prompt_id, flush=True)
    (RUN_DIR / "提交回执.json").write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8")
    history = wait_for_history(prompt_id)
    item = locate_video(history)
    output = OUTPUT_DIR / "EP03_片段01-03_本地导演台_未审核长视频.mp4"
    download_video(item, output)
    (RUN_DIR / "历史记录.json").write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OUTPUT_FILE=" + str(output), flush=True)
    print("SOURCE_FILE=" + json.dumps(item, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
