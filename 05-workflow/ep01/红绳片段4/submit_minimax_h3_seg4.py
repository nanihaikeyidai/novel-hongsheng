# -*- coding: utf-8 -*-
"""
红绳片段4 · MiniMax-H3 管线3（Multi-Reference Ref2VA）视频生成
==============================================================
从 Work-Fisher UI 格式工作流提取管线3（MiniMaxH3ReferenceToVideo, node 153），
转换为 ComfyUI API 格式 prompt，提交到本地 ComfyUI (127.0.0.1:8188) 并轮询结果。

管线3 节点链（UI id -> API 结构）：
  UNETLoader(129) -> ReservedVRAMSetter(142) -> SageAttentionPatch(147)
    -> BasicGuider(138) + BasicScheduler(141)
  CLIPLoader(132) / VAELoader(131 video) / VAELoader(130 audio)
  LoadImage(154/155/156) -> MiniMaxH3ReferenceToVideo(153)
  PrimitiveStringMultiline(151 prompt) + ResolutionSelector(133) + ComfyMathExpression(150)
  KSamplerSelect(140) + RandomNoise(139) -> SamplerCustomAdvanced(144)
    -> VAEDecode(145) + VAEDecodeAudio(146) -> VHS_VideoCombine(149)

用法：python3 submit_minimax_h3_seg4.py [--seconds 15] [--dry-run]
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse

COMFY_HOST = "127.0.0.1"
COMFY_PORT = 8188
API_PROMPT = f"http://{COMFY_HOST}:{COMFY_PORT}/prompt"
API_HISTORY = f"http://{COMFY_HOST}:{COMFY_PORT}/history"

HERE = os.path.dirname(os.path.abspath(__file__))
PROMPT_MD = os.path.join(HERE, "MiniMax_H3_视频提示词.md")
REF_IMAGES = [
    "hongsheng_ep01/seg4_ref1_monster.png",
    "hongsheng_ep01/seg4_ref2_teacher.png",
    "hongsheng_ep01/seg4_ref3_classroom.png",
]
OUTPUT_PREFIX = "hongsheng_ep01/seg4_ref2va"


def extract_main_prompt(md_path):
    """从提示词 md 提取 ```text 代码块全文"""
    with open(md_path, encoding="utf-8") as f:
        content = f.read()
    m = re.search(r"```text\s*\n(.*?)\n```", content, re.DOTALL)
    if not m:
        raise SystemExit("未找到 ```text 代码块")
    return m.group(1).strip()


def build_prompt(seconds=15.0):
    prompt_text = extract_main_prompt(PROMPT_MD)

    prompt = {
        # ---- 模型加载 ----
        "129": {"class_type": "UNETLoader", "inputs": {
            "unet_name": "minimax_h3_fl2va_int8_convrot.safetensors",
            "weight_dtype": "default",
        }},
        "142": {"class_type": "ReservedVRAMSetter", "inputs": {
            "anything": ["129", 0],
            "reserved": 1.0,
            "mode": "manual",
            "seed": 95023784637039,
            "auto_max_reserved": 0.0,
            "clean_gpu_before": True,
        }},
        "147": {"class_type": "MiniMaxH3MemoryEfficientSageAttentionPatch", "inputs": {
            "model": ["142", 0],
        }},
        "132": {"class_type": "CLIPLoader", "inputs": {
            "clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
            "type": "minimax",
            "device": "default",
        }},
        "131": {"class_type": "VAELoader", "inputs": {
            "vae_name": "minimax_h3_video_vae_fp16.safetensors",
        }},
        "130": {"class_type": "VAELoader", "inputs": {
            "vae_name": "minimax_h3_audio_vae_fp32.safetensors",
        }},

        # ---- 输入 ----
        "154": {"class_type": "LoadImage", "inputs": {"image": REF_IMAGES[0]}},
        "155": {"class_type": "LoadImage", "inputs": {"image": REF_IMAGES[1]}},
        "156": {"class_type": "LoadImage", "inputs": {"image": REF_IMAGES[2]}},
        "151": {"class_type": "PrimitiveStringMultiline", "inputs": {"value": prompt_text}},
        "133": {"class_type": "ResolutionSelector", "inputs": {
            "aspect_ratio": "16:9 (Widescreen)",
            "megapixels": 0.4,
            "multiple": 32,
        }},
        "143": {"class_type": "PrimitiveFloat", "inputs": {"value": seconds}},
        "150": {"class_type": "ComfyMathExpression", "inputs": {
            "values.a": ["143", 0],
            "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
        }},

        # ---- 生成核心 ----
        "153": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {
            "clip": ["132", 0],
            "vae": ["131", 0],
            "audio_vae": ["130", 0],
            "ref_images.ref_image_0": ["154", 0],
            "ref_images.ref_image_1": ["155", 0],
            "ref_images.ref_image_2": ["156", 0],
            "prompt": ["151", 0],
            "width": ["133", 0],
            "height": ["133", 1],
            "length": ["150", 1],
            "ref_image_size": "match",
        }},
        "138": {"class_type": "BasicGuider", "inputs": {
            "model": ["147", 0],
            "conditioning": ["153", 0],
        }},
        "141": {"class_type": "BasicScheduler", "inputs": {
            "model": ["147", 0],
            "scheduler": "beta",
            "steps": 10,
            "denoise": 1.0,
        }},
        "140": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "139": {"class_type": "RandomNoise", "inputs": {"noise_seed": 488357386810245}},
        "144": {"class_type": "SamplerCustomAdvanced", "inputs": {
            "noise": ["139", 0],
            "guider": ["138", 0],
            "sampler": ["140", 0],
            "sigmas": ["141", 0],
            "latent_image": ["153", 1],
        }},

        # ---- 解码与输出 ----
        "145": {"class_type": "VAEDecode", "inputs": {
            "samples": ["144", 0],
            "vae": ["131", 0],
        }},
        "146": {"class_type": "VAEDecodeAudio", "inputs": {
            "samples": ["144", 0],
            "vae": ["130", 0],
        }},
        "149": {"class_type": "VHS_VideoCombine", "inputs": {
            "images": ["145", 0],
            "audio": ["146", 0],
            "frame_rate": 24,
            "loop_count": 0,
            "filename_prefix": OUTPUT_PREFIX,
            "format": "video/h264-mp4",
            "pix_fmt": "yuv420p",
            "crf": 19,
            "save_metadata": True,
            "trim_to_audio": False,
            "pingpong": False,
            "save_output": True,
        }},
    }
    return prompt, prompt_text


def queue_prompt(prompt):
    body = json.dumps({"prompt": prompt}).encode("utf-8")
    req = urllib.request.Request(API_PROMPT, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def poll_history(prompt_id, timeout=600, interval=10):
    start = time.time()
    while time.time() - start < timeout:
        url = f"{API_HISTORY}/{urllib.parse.quote(prompt_id)}"
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                history = json.loads(resp.read())
        except Exception as e:
            print(f"[poll] 读取 history 失败: {e}", flush=True)
            time.sleep(interval)
            continue
        if prompt_id in history and history[prompt_id]:
            return history[prompt_id], time.time() - start
        elapsed = int(time.time() - start)
        print(f"[poll] {elapsed}s 已等待，仍在执行...", flush=True)
        time.sleep(interval)
    return None, time.time() - start


def main():
    seconds = 15.0
    dry_run = False
    args = sys.argv[1:]
    if "--seconds" in args:
        seconds = float(args[args.index("--seconds") + 1])
    if "--dry-run" in args:
        dry_run = True

    prompt, prompt_text = build_prompt(seconds)
    print(f"提示词字数: {len(prompt_text)}")
    print(f"参考图: {REF_IMAGES}")
    print(f"时长: {seconds} 秒")

    out_path = os.path.join(HERE, "seg4_api_prompt.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"prompt": prompt}, f, ensure_ascii=False, indent=2)
    print(f"API prompt 已保存: {out_path}")

    if dry_run:
        print("DRY-RUN: 不提交。")
        return

    print("提交到 ComfyUI ...", flush=True)
    try:
        resp = queue_prompt(prompt)
    except Exception as e:
        # 尝试读取错误详情
        try:
            body = e.read().decode("utf-8", errors="replace")
            print(f"提交失败: {e}\n响应: {body}")
        except Exception:
            print(f"提交失败: {e}")
        sys.exit(1)

    pid = resp.get("prompt_id")
    print(f"提交成功! prompt_id = {pid}")
    if resp.get("node_errors"):
        print("node_errors:", json.dumps(resp["node_errors"], ensure_ascii=False))

    history, elapsed = poll_history(pid, timeout=600, interval=10)
    if history is None:
        print(f"超时（{int(elapsed)}s），任务仍在队列/执行中")
        sys.exit(2)

    status = history.get("status", {})
    status_str = status.get("status_str")
    print(f"\n完成: status_str={status_str}, 总耗时 {int(elapsed)}s")

    outputs = history.get("outputs", {})
    for nid, out in sorted(outputs.items()):
        for key, val in out.items():
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict) and item.get("filename"):
                        print(f"  节点{nid} [{key}]: {item.get('type')}/{item.get('subfolder','')}/{item.get('filename')}")

    if status_str == "error":
        for msg in status.get("messages", []):
            if msg[0] == "execution_error":
                detail = msg[1]
                print("\n执行错误:", detail.get("exception_message"))
                print("节点:", detail.get("node_id"), detail.get("node_type"))
        sys.exit(3)


if __name__ == "__main__":
    main()
