# -*- coding: utf-8 -*-
"""本地 H3 Ripple（WepeNerd）测试 — P09 黑发安娜 -> 蓝黑发，锚点帧0

链路: UNET(hybrid int8) -> DMaD LoRA -> Ripple LoRA -> Spark SM89 -> RippleApply
源视频: ComfyUI/input/P09_v2v_test_5s.mp4 (124帧@24fps)
锚点: input/anchor_f0_edited_bluehair.png (marker frame 0)
输出: ripple/P09_bluehair_test*.mp4 (原声保留)
用法: python run_ep05_p09_ripple_test.py [--dry-run]
"""
import json
import shutil
import sys
import time
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:8188"
OUT_DIR = Path(r"D:/HermesWorkspace/ai小说/红绳/05-workflow/ep05/营救陆沉/红绳片段09/视频草稿/Ripple测试_蓝发")
STEPS = 8
SEED = 42

RIPPLE_PROMPT = (
    "Edit propagation: each edited frame shows exactly how that moment of the video should look after the edit. "
    "Apply the same changes to every frame of the clip, before, between and after the edited frames, so the edit "
    "stays consistent through the whole video. Keep the guide video's motion, timing, camera movement, composition "
    "and all unedited content unchanged."
)


def build_prompt(compare: bool = False) -> dict:
    return {
        "1": {"class_type": "UNETLoader", "inputs": {
            "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
            "weight_dtype": "default"}},
        "2": {"class_type": "LoraLoaderModelOnly", "inputs": {
            "lora_name": "h3\\loras\\minimax_h3_dmad_full_dareties_v4_step600_comfy_fro.safetensors",
            "strength_model": 1.0, "model": ["1", 0]}},
        "3": {"class_type": "LoraLoaderModelOnly", "inputs": {
            "lora_name": "h3\\minimax_H3_Ripple-v1.safetensors",
            "strength_model": 1.0, "model": ["2", 0]}},
        "4": {"class_type": "MiniMaxH3SparkAttentionSM89", "inputs": {
            "model": ["3", 0], "enabled": True, "steps": STEPS,
            "warmup_mode": "warmup_ratio", "warmup_ratio": 0.2, "warmup_steps": 2,
            "topk_mode": "topk_ratio", "topk_ratio": 0.2, "topk_blocks": 228,
            "dense_layers": 0, "min_tokens": 12288, "strict": True,
            "tail_granularity": "query", "reblock_layout": "q_reuse_k"}},
        "5": {"class_type": "VAELoader", "inputs": {
            "vae_name": "minimax_h3_video_vae_int8_convrot.safetensors"}},
        "6": {"class_type": "CLIPLoader", "inputs": {
            "clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
            "type": "minimax", "device": "default"}},
        "7": {"class_type": "WN_RippleClip", "inputs": {
            "video": "P09_v2v_test_5s.mp4", "duration": 5.1667,
            "megapixels": 0.7, "window_start": 0,
            "markers": json.dumps([{"id": 1, "frame": 0}], separators=(",", ":"))}},
        "8": {"class_type": "LoadImage", "inputs": {
            "image": "anchor_f0_edited_bluehair.png"}},
        "9": {"class_type": "WN_RippleApply", "inputs": {
            "clip": ["6", 0], "vae": ["5", 0], "ripple": ["7", 1],
            "prompt": RIPPLE_PROMPT, "edited_anchor_1": ["8", 0]}},
        "10": {"class_type": "RandomNoise", "inputs": {"noise_seed": SEED}},
        "11": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "12": {"class_type": "BasicScheduler", "inputs": {
            "scheduler": "simple", "steps": STEPS, "denoise": 1, "model": ["4", 0]}},
        "13": {"class_type": "BasicGuider", "inputs": {
            "model": ["4", 0], "conditioning": ["9", 0]}},
        "14": {"class_type": "SamplerCustomAdvanced", "inputs": {
            "noise": ["10", 0], "guider": ["13", 0], "sampler": ["11", 0],
            "sigmas": ["12", 0], "latent_image": ["9", 1]}},
        "15": {"class_type": "VAEDecode", "inputs": {
            "samples": ["14", 0], "vae": ["5", 0]}},
        "16": {"class_type": "WN_RippleOutput", "inputs": {
            "images": ["15", 0], "ripple": ["7", 1],
            "save": "shot + comparison" if compare else "shot",
            "filename_prefix": "ripple/P09_bluehair_test",
            "show_anchor_markers": False}},
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
    prompt = build_prompt()
    if "--dry-run" in sys.argv:
        print(json.dumps(prompt, ensure_ascii=False, indent=1))
        return 0
    # 节点存在性检查
    oi = http_json("/object_info")
    missing = [n for n in ("WN_RippleClip", "WN_RippleApply", "WN_RippleOutput")
               if n not in oi]
    if missing:
        print(f"[ERR] 节点未注册: {missing} —— 需重启 ComfyUI 加载 ComfyUI-WepeNerd")
        return 1
    resp = http_json("/prompt", {"prompt": prompt, "client_id": "ripple-test"})
    pid = resp["prompt_id"]
    print(f"[OK] 已提交 prompt_id={pid}")
    while True:
        time.sleep(15)
        h = http_json(f"/history/{pid}")
        if pid not in h:
            q = http_json("/queue")
            print(f"  ...运行中 (running={len(q.get('queue_running', []))} "
                  f"pending={len(q.get('queue_pending', []))})")
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
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            for node_id, node_out in item.get("outputs", {}).items():
                for key, val in node_out.items():
                    if isinstance(val, list):
                        for f in val:
                            if isinstance(f, dict) and "filename" in f:
                                print(f"[out] node{node_id}.{key}: {f.get('subfolder','')}/{f['filename']}")
                                if f["filename"].endswith(".mp4") and "_compare" not in f["filename"]:
                                    sub = f.get("subfolder", "")
                                    url = (f"/view?filename={f['filename']}&subfolder={sub}"
                                           f"&type={f.get('type', 'output')}")
                                    save_to = OUT_DIR / "片段09_P09_Ripple蓝发测试_v1.mp4"
                                    with urllib.request.urlopen(API + url, timeout=300) as r, open(save_to, "wb") as fp:
                                        shutil.copyfileobj(r, fp)
                                    print(f"[OK] 已下载: {save_to}")
            return 0


if __name__ == "__main__":
    sys.exit(main())
