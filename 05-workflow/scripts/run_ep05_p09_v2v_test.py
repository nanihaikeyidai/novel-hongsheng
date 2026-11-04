# -*- coding: utf-8 -*-
"""本地梅林 H3 v2v（Ripple 式编辑）测试 — P09 黑发安娜 -> 蓝黑发

链路: UNET(hybrid int8) -> DMaD LoRA -> Spark SM89 -> MiniMaxH3Director(v2v)
源视频: P09v13 前 124 帧(约5s), 0.7MP 16:9, 8步 euler/simple, seed 固定
用法: python run_ep05_p09_v2v_test.py [--dry-run]
"""
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

COMFY = Path(r"F:/Work-Fisher纯净包2026.8.7/ComfyUI")
API = "http://127.0.0.1:8188"
SRC = Path(r"D:/HermesWorkspace/ai小说/红绳/05-workflow/ep05/营救陆沉/红绳片段09/视频草稿/片段09_P09v13_金鱼草稿_云端旧版黑发.mp4")
OUT_DIR = SRC.parent / "v2v测试_蓝发"
INPUT_NAME = "P09_v2v_test_5s.mp4"

TOTAL_FRAMES = 124  # 24fps ≈ 5.17s, MiniMax 17k+5 网格
W, H = 1152, 640    # 0.7MP 16:9（与梅林模板一致）
STEPS = 8
SEED = 42

EDIT_PROMPT = (
    "Keep the scene from <Video 1> exactly: same camera, framing, motion, "
    "characters, clothing, lighting and timing. Change only the young woman "
    "cleaner's long straight hair color: from pure black to blue-black "
    "(dark navy blue with a visible blue sheen under the light). Keep her "
    "hairstyle, hair length, cap, face mask, uniform and pose unchanged. "
    "Keep the male security guard completely unchanged. Audio: keep the quiet "
    "indoor facility ambience; no new dialogue. No text or logos."
)

TASK_TYPE = "v2v — 视频转视频(Video to Video)"


def build_timeline() -> str:
    tl = {
        "version": 4,
        "editMode": "global",
        "timelineMode": "video",
        "totalFrames": TOTAL_FRAMES,
        "frameRate": 24.0,
        "width": W,
        "height": H,
        "refMaxSize": 864,
        "output": {
            "mode": "fixed", "longEdge": W, "width": W, "height": H,
            "maxExportFrames": 0, "exportMode": "all",
            "continuityEnabled": False, "continuityOverlapFrames": 9,
        },
        "videoClips": [],
        "video": {
            "fileName": INPUT_NAME, "videoFile": "", "subfolder": "",
            "type": "input", "frames": [], "frameMap": [],
        },
        "global": {
            "taskType": TASK_TYPE, "prompt": EDIT_PROMPT, "refs": [],
            "referenceVideo": {}, "continuousReference": False,
            "genImage": {"imageFile": ""},
        },
        "segments": [{
            "id": "s0", "start": 0, "length": TOTAL_FRAMES,
            "frameCount": TOTAL_FRAMES, "durationSec": round(TOTAL_FRAMES / 24.0, 2),
            "prompt": "", "taskType": "", "refs": [], "referenceVideo": {},
            "genImage": {"imageFile": ""}, "negativePrompt": "",
        }],
        "gen": {"defaultFrameCount": TOTAL_FRAMES},
        "runSelectEnabled": False, "runSelection": [],
    }
    return json.dumps(tl, ensure_ascii=False)


def build_prompt() -> dict:
    timeline = build_timeline()
    return {
        "1": {"class_type": "UNETLoader", "inputs": {
            "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
            "weight_dtype": "default"}},
        "2": {"class_type": "LoraLoaderModelOnly", "inputs": {
            "lora_name": "h3\\loras\\minimax_h3_dmad_full_dareties_v4_step600_comfy_fro.safetensors",
            "strength_model": 1.0, "model": ["1", 0]}},
        "3": {"class_type": "MiniMaxH3SparkAttentionSM89", "inputs": {
            "model": ["2", 0], "enabled": True, "steps": STEPS,
            "warmup_mode": "warmup_ratio", "warmup_ratio": 0.2, "warmup_steps": 2,
            "topk_mode": "topk_ratio", "topk_ratio": 0.2, "topk_blocks": 228,
            "dense_layers": 0, "min_tokens": 12288, "strict": True,
            "tail_granularity": "query", "reblock_layout": "q_reuse_k"}},
        "4": {"class_type": "VAELoader", "inputs": {
            "vae_name": "minimax_h3_video_vae_int8_convrot.safetensors"}},
        "5": {"class_type": "VAELoader", "inputs": {
            "vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
        "6": {"class_type": "CLIPLoader", "inputs": {
            "clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
            "type": "minimax", "device": "default"}},
        "10": {"class_type": "MiniMaxH3Director", "inputs": {
            "model": ["3", 0], "video_vae": ["4", 0], "audio_vae": ["5", 0],
            "clip": ["6", 0],
            "task_type": TASK_TYPE, "global_prompt": EDIT_PROMPT,
            "bd_grp_sample": "采样设置", "cfg": 1.0, "seed": SEED,
            "frame_rate": 24.0, "width": W, "height": H, "ref_max_size": 864,
            "total_frames": TOTAL_FRAMES, "timeline_data": timeline,
            "bd_grp_advanced": "高级采样", "steps": STEPS,
            "sampler": "euler", "scheduler": "simple",
            "shift_video": 12.0, "shift_audio": 3.0,
            "bd_grp_perf": "性能", "clear_vram_between_segments": True}},
        "20": {"class_type": "CreateVideo", "inputs": {
            "images": ["10", 0], "fps": ["10", 2], "audio": ["10", 1],
            "bit_depth": "auto", "color_space": "sRGB"}},
        "21": {"class_type": "SaveVideo", "inputs": {
            "video": ["20", 0], "filename_prefix": "video/P09_v2v_lanfa_test",
            "format": "auto", "codec": "auto"}},
    }


def http_json(path: str, payload: dict | None = None, timeout: int = 30):
    url = API + path
    if payload is not None:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"})
    else:
        req = url
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    dry = "--dry-run" in sys.argv
    # 1) 切 124 帧
    dst = COMFY / "input" / INPUT_NAME
    if not dry:
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-i", str(SRC),
            "-frames:v", str(TOTAL_FRAMES), "-an", str(dst)], check=True)
        print(f"[OK] 源片段已切: {dst}")
    # 2) 组工作流
    prompt = build_prompt()
    if dry:
        print(json.dumps(prompt, ensure_ascii=False, indent=1)[:3000])
        return 0
    # 3) 提交
    resp = http_json("/prompt", {"prompt": prompt, "client_id": "v2v-test"})
    pid = resp["prompt_id"]
    print(f"[OK] 已提交 prompt_id={pid}")
    # 4) 轮询
    while True:
        time.sleep(15)
        h = http_json(f"/history/{pid}")
        if pid not in h:
            q = http_json("/queue")
            running = len(q.get("queue_running", []))
            pending = len(q.get("queue_pending", []))
            print(f"  ...运行中 (running={running} pending={pending})")
            continue
        item = h[pid]
        status = item.get("status", {})
        print(f"[status] {status.get('status_str')} completed={status.get('completed')}")
        if status.get("status_str") == "error":
            for m in status.get("messages", []):
                if m[0] == "execution_error":
                    print(json.dumps(m[1], ensure_ascii=False)[:2000])
            return 1
        if status.get("completed"):
            outs = []
            for node_id, node_out in item.get("outputs", {}).items():
                for key, val in node_out.items():
                    if isinstance(val, list):
                        for f in val:
                            if isinstance(f, dict) and "filename" in f:
                                outs.append((node_id, key, f))
            for node_id, key, f in outs:
                sub = f.get("subfolder", "")
                url = f"/view?filename={f['filename']}&subfolder={sub}&type={f.get('type','output')}"
                print(f"[out] node{node_id}.{key}: {sub}/{f['filename']}")
                if key == "gifs" or f["filename"].endswith(".mp4"):
                    OUT_DIR.mkdir(parents=True, exist_ok=True)
                    save_to = OUT_DIR / "片段09_P09_v2v蓝发测试_v1.mp4"
                    with urllib.request.urlopen(API + url, timeout=120) as r, open(save_to, "wb") as fp:
                        shutil.copyfileobj(r, fp)
                    print(f"[OK] 已下载: {save_to}")
            return 0


if __name__ == "__main__":
    sys.exit(main())
