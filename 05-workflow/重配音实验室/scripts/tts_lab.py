#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地重配音实验室 · ComfyUI IndexTTS-2.5 客户端

用本地 ComfyUI 的 comfyui-indextts25-T8 节点重配单句台词，0 币耗。
用法：
    python tts_lab.py --case cases/P09_晚安/case.json --check
    python tts_lab.py --case cases/P09_晚安/case.json --only A_text_threat
    python tts_lab.py --case cases/P09_晚安/case.json

约定：
- 参考音频必须先放到 ComfyUI/input/，且文件名只用 ASCII（中文名在 LoadAudio 里易踩坑）。
- 输出的 filename_prefix 一律 ASCII，成品由本脚本下载到案例目录并改成中文名。
- 不启动、不重启 ComfyUI；只通过 HTTP API 排队。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

COMFY = "http://127.0.0.1:8188"
LAB = Path(__file__).resolve().parents[1]


def _get(url: str, timeout: int = 30) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _post(url: str, payload: dict, timeout: int = 60) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def build_prompt(case: dict, cand: dict) -> dict:
    """按官方 api/01 + 04 + 05 + 03 示例构造最小生成图。"""
    nodes: dict[str, dict] = {}

    nodes["1"] = {
        "class_type": "T8_IndexTTS25_ModelLoader",
        "inputs": {
            "model_name": case.get("model_name", "IndexTTS-2.5"),
            "device": "auto",
            "precision": "auto",
            "acceleration_mode": "off",
            "use_cuda_kernel": False,
            "release_after_run": False,
            "recycle_after_runs": 0,
            "verify_hashes": False,
            "custom_model_path": "",
            "reference_device": "auto",
            "reuse_spk_cond_for_emo": False,
            "persistent_reference_cache": True,
            "download_missing": False,
            "accept_model_license": False,
        },
    }

    speaker_file = cand.get("voice_ref", case["voice_ref"])
    nodes["2"] = {"class_type": "LoadAudio", "inputs": {"audio": speaker_file}}

    gen_inputs = {
        "model": ["1", 0],
        "speaker_audio": ["2", 0],
        "text": cand.get("text", case["line"]),
        "language": case.get("language", "ZH"),
        "duration_factor": float(cand.get("duration_factor", 1.0)),
        "target_duration_mode": "off",
        "target_duration_seconds": 0.0,
        "postprocess_preset": cand.get("postprocess_preset", "off"),
        "postprocess_strength": 1.0,
        "seed": int(cand.get("seed", 20261106)),
        "quality_retry_count": int(cand.get("quality_retry_count", 0)),
        "quality_asr_backend": "auto",
        "quality_asr_model": "base",
        "quality_asr_device": "auto",
        "quality_threshold": 0.82,
    }

    emo = cand.get("emotion")
    if emo:
        mode = emo["mode"]
        ei = {"mode": mode}
        if mode == "text":
            ei["mode.emotion_text"] = emo["emotion_text"]
            ei["mode.strength"] = float(emo.get("strength", 0.9))
        elif mode == "vector":
            for k in (
                "happy", "angry", "sad", "afraid", "disgusted",
                "melancholic", "surprised", "calm",
            ):
                ei[f"mode.{k}"] = float(emo.get(k, 0.0))
            ei["mode.strength"] = float(emo.get("strength", 1.0))
            ei["mode.use_random"] = False
        elif mode == "reference_audio":
            ref_file = emo.get("emotion_audio", case["emotion_ref"])
            nodes["3"] = {"class_type": "LoadAudio", "inputs": {"audio": ref_file}}
            ei["mode.emotion_audio"] = ["3", 0]
            ei["mode.strength"] = float(emo.get("strength", 0.8))
        elif mode == "speaker":
            ei["mode.strength"] = float(emo.get("strength", 1.0))
        else:
            raise ValueError(f"未知情感模式: {mode}")

        nodes["4"] = {"class_type": "T8_IndexTTS25_EmotionControl", "inputs": ei}
        gen_inputs["emotion"] = ["4", 0]

    # 可选采样配置：字间停顿 <pause=0.12> 在任何 pause_preset 下都生效；
    # 降低 inference_cfg_rate / 提高 cfm_temperature 会让发声更松、更接近气声。
    sampling = cand.get("sampling")
    if sampling:
        si = {
            "do_sample": bool(sampling.get("do_sample", False)),
            "temperature": float(sampling.get("temperature", 0.8)),
            "top_p": float(sampling.get("top_p", 0.8)),
            "top_k": int(sampling.get("top_k", 30)),
            "num_beams": int(sampling.get("num_beams", 3)),
            "repetition_penalty": float(sampling.get("repetition_penalty", 10.0)),
            "length_penalty": float(sampling.get("length_penalty", 0.0)),
            "max_mel_tokens": int(sampling.get("max_mel_tokens", 1500)),
            "diffusion_steps": int(sampling.get("diffusion_steps", 25)),
            "inference_cfg_rate": float(sampling.get("inference_cfg_rate", 0.7)),
            "cfm_temperature": float(sampling.get("cfm_temperature", 1.0)),
            "segmentation_mode": "auto",
            "max_text_tokens_per_segment": 120,
            "segment_silence_ms": 200,
            "pause_preset": sampling.get("pause_preset", "off"),
            "comma_pause_ms": int(sampling.get("comma_pause_ms", 100)),
            "sentence_pause_ms": int(sampling.get("sentence_pause_ms", 300)),
            "paragraph_pause_ms": 600,
            "text_normalization": True,
        }
        nodes["7"] = {"class_type": "T8_IndexTTS25_SamplingConfig", "inputs": si}
        gen_inputs["sampling"] = ["7", 0]

    nodes["5"] = {"class_type": "T8_IndexTTS25_Generate", "inputs": gen_inputs}
    prefix = f"voicelab/{case['case_id']}_{cand['name']}"
    nodes["6"] = {
        "class_type": "SaveAudio",
        "inputs": {"audio": ["5", 0], "filename_prefix": prefix},
    }
    return nodes


def wait_prompt(prompt_id: str, timeout: int = 900) -> dict:
    start = time.time()
    last = -10
    while True:
        try:
            h = _get(f"{COMFY}/history/{prompt_id}")
            if prompt_id in h:
                return h[prompt_id]
        except Exception as exc:  # 服务重启/网络抖动
            print(f"  [warn] history 查询异常: {exc}", flush=True)
        elapsed = int(time.time() - start)
        if elapsed >= last + 15:
            print(f"  ... 已等待 {elapsed}s", flush=True)
            last = elapsed
        if elapsed > timeout:
            raise TimeoutError(f"ComfyUI 任务 {prompt_id} 超过 {timeout}s 未完成")
        time.sleep(2)


def download_audio(result: dict, dest: Path) -> str:
    """从 history outputs 里找 SaveAudio 产物，用 /view 下载。"""
    outs = result.get("outputs", {})
    for _, node_out in outs.items():
        for key in ("audio", "images", "gifs"):
            for item in node_out.get(key, []) or []:
                fn = item.get("filename", "")
                if not fn.lower().endswith((".wav", ".flac", ".mp3", ".ogg")):
                    continue
                q = urllib.parse.urlencode(
                    {
                        "filename": fn,
                        "subfolder": item.get("subfolder", ""),
                        "type": item.get("type", "output"),
                    }
                )
                tmp = dest.with_name(dest.stem + Path(fn).suffix)
                with urllib.request.urlopen(f"{COMFY}/view?{q}", timeout=60) as r:
                    tmp.write_bytes(r.read())
                # SaveAudio 默认吐 .flac，统一转成 48k 单声道 PCM wav，便于后期对齐
                conv = subprocess.run(
                    ["ffmpeg", "-v", "error", "-y", "-i", str(tmp),
                     "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(dest)],
                    capture_output=True, text=True,
                )
                if conv.returncode != 0:
                    raise RuntimeError("音频转码失败: " + conv.stderr[-800:])
                tmp.unlink(missing_ok=True)
                return fn
    raise RuntimeError(f"未在 outputs 里找到音频: {json.dumps(outs, ensure_ascii=False)[:800]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, help="案例 case.json 路径")
    ap.add_argument("--only", default="", help="只跑指定候选名")
    ap.add_argument("--check", action="store_true", help="只打印 prompt，不提交")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    case_path = Path(args.case)
    if not case_path.is_absolute():
        case_path = (LAB / case_path).resolve()
    case = json.loads(case_path.read_text(encoding="utf-8"))
    out_dir = case_path.parent / case.get("out_dir", "候选音频")
    out_dir.mkdir(parents=True, exist_ok=True)

    cands = case["candidates"]
    if args.only:
        cands = [c for c in cands if c["name"] == args.only]
        if not cands:
            print(f"没有名为 {args.only} 的候选", file=sys.stderr)
            return 2

    failed = 0
    for cand in cands:
        prompt = build_prompt(case, cand)
        if args.check:
            print(f"\n===== {cand['name']} =====")
            print(json.dumps(prompt, ensure_ascii=False, indent=2))
            continue

        print(f"\n>>> 提交 {cand['name']} | 音色={cand.get('voice_ref', case['voice_ref'])} "
              f"| 情绪={cand.get('emotion', {}).get('mode', 'off')}", flush=True)
        client_id = str(uuid.uuid4())
        res = _post(f"{COMFY}/prompt", {"prompt": prompt, "client_id": client_id})
        pid = res.get("prompt_id")
        if not pid:
            print(f"  提交失败: {res}", file=sys.stderr)
            failed += 1
            continue
        print(f"  prompt_id={pid}", flush=True)
        try:
            result = wait_prompt(pid, args.timeout)
        except Exception as exc:
            print(f"  等待失败: {exc}", file=sys.stderr)
            failed += 1
            continue
        status = result.get("status", {})
        if status.get("status_str") != "success" or status.get("completed") is not True:
            print(f"  任务失败: {json.dumps(status, ensure_ascii=False)[:600]}", file=sys.stderr)
            msgs = status.get("messages", [])
            print(json.dumps(msgs, ensure_ascii=False)[:1500], file=sys.stderr)
            failed += 1
            continue

        dest = out_dir / f"{cand['name']}.wav"
        fn = download_audio(result, dest)
        print(f"  完成 -> {dest.name}  ({dest.stat().st_size} bytes, ComfyUI: {fn})", flush=True)

        # 打印生成节点的文本报告（时长、采样率等）
        for node_id, node_out in result.get("outputs", {}).items():
            for key in ("text", "string"):
                for t in node_out.get(key, []) or []:
                    if isinstance(t, str) and len(t) > 20:
                        print(f"  [{node_id}] {t[:300]}", flush=True)

    if failed:
        print(f"\n{failed} 个候选失败（其余已生成）", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
