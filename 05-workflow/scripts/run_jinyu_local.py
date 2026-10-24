"""用红绳真实资产填充金鱼本地版并提交 ComfyUI 实跑。

这是「金鱼工作流本地部署」的最终验收：不是跑通采样，而是跑通
金鱼完整数据流——9 张参考图 + 3 段参考视频 + 3 条参考音频 + 真实 6395 字提示词。
"""
import json
import shutil
import sys
import time
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from local_h3_ref2va_test import api  # noqa: E402

API_JSON = Path("F:/h3tmp/jinyu_api_final.json")
COMFY = Path(r"F:\Work-Fisher纯净包2026.8.7\ComfyUI")
ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
PROMPT_TXT = (ROOT / "05-workflow/ep04/红绳片段09c_陆定天的名字"
              / "动作流_H3纯提示词.txt")

IMAGES = [
    "05-workflow/ep04/归档素材/人物/陆沉_人设.png",
    "05-workflow/ep04/归档素材/人物/审讯员老韩_人设_单人.png",
    "05-images/场景/场景_ND审问室_日漫v3.png",
    "05-images/人物/陆定天_军装照_日漫.png",
]
AUDIOS = ["人物参考音色/老韩.wav", "人物参考音色/陆沉.wav"]
VIDEOS = [
    "05-workflow/ep04/红绳片段09c_陆定天的名字/视频草稿/E04-09c_陆定天的名字_v4_未审核草稿.mp4",
]


def stage(src: Path, sub: str) -> str:
    """把素材复制进 ComfyUI 的 input 目录并返回文件名。"""
    dst_dir = COMFY / "input" / sub
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    if not dst.exists():
        shutil.copy(src, dst)
    return f"{sub}/{src.name}"


def find_nodes(api_wf: dict, cls: str) -> list[str]:
    return [k for k, v in api_wf.items() if v["class_type"] == cls]


def main() -> None:
    wf = json.loads(API_JSON.read_text(encoding="utf-8"))

    # ---- 素材入库 ----
    imgs = [stage(ROOT / p, "jinyu_img") for p in IMAGES]
    auds = [stage(ROOT / p, "jinyu_aud") for p in AUDIOS]
    vids = [stage(ROOT / p, "jinyu_vid") for p in VIDEOS]
    print("参考图:", imgs)
    print("参考音频:", auds)
    print("参考视频:", vids)

    # ---- 控件策略：全部重铺 ----
    # 前端 widgets_values 的顺序和 object_info 的 required 顺序在 RH 导出的
    # 工作流里对不上（RH 有自定义控件），按位置硬塞会把 start_percent 填成
    # 1.3、sink_conditioning 填成 256 这类脏值。
    # 所以：先删光所有非连线输入，再用 object_info 的 default 铺一遍，
    # 最后用 OVERRIDE 表显式覆盖真正需要指定的值。
    oi = api("/object_info")
    # 连线输入形如 ["329", 0]，第一个元素是 API 图的 key（字符串）。
    # 注意要排除 {"model": "MODEL"} 这类「类型名字符串」——它也是长度 2 的
    # 字符串列表，但不是连线（第一个元素不在图里），会被上面的判据漏掉，
    # 所以额外要求 v[1] 是 int。
    linked = 0
    for nid, n in wf.items():
        keep = {}
        for k, v in n["inputs"].items():
            if (isinstance(v, list) and len(v) == 2
                    and isinstance(v[0], str) and v[0] in wf
                    and isinstance(v[1], int)):
                keep[k] = v
        n["inputs"] = keep
        linked += len(keep)
    print(f"保留连线输入 {linked} 个，控件值全部丢弃后按 object_info 重铺")

    for nid, n in wf.items():
        spec = oi.get(n["class_type"], {}).get("input", {})
        for sec in ("required", "optional"):
            for k, meta in (spec.get(sec) or {}).items():
                if k in n["inputs"] or not isinstance(meta, list) or not meta:
                    continue
                head = meta[0]
                default = None
                if isinstance(head, str) and len(meta) > 1 and isinstance(meta[1], dict):
                    default = meta[1].get("default")
                elif not isinstance(head, list):
                    default = head
                # default 恰好等于输入的**类型名**（VAE/MODEL/CONDITIONING…）
                # 说明这是「需要连线对象」的可选输入，object_info 只是把类型名
                # 当占位符返回；填进去会让节点拿到 str 而报
                # "'str' object has no attribute 'inputs'"。这类必须跳过。
                if default == head and isinstance(head, str) and (
                        head.isupper() or head.endswith("Manager")):
                    continue
                if isinstance(default, list) or not isinstance(
                        default, (int, float, str, bool)):
                    continue
                n["inputs"][k] = default

    # 显式覆盖（class_type, key）-> 值
    OVERRIDE = {
        ("UNETLoader", "unet_name"):
            "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
        ("UNETLoader", "weight_dtype"): "default",
        ("CLIPLoader", "clip_name"):
            "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
        ("CLIPLoader", "type"): "minimax",
        ("VAELoader", "vae_name"): "minimax_h3_video_vae_fp16.safetensors",
        ("ModelPreviewOverrideKJ", "vae"): "minimax_h3_audio_vae_fp32.safetensors",
        ("ResolutionSelector", "megapixels"): 0.5,
        ("ResolutionSelector", "aspect_ratio"): "16:9 (Widescreen)",
        ("RandomNoise", "noise_seed"): 29732110694208,
        ("MiniMaxH3MultiRateSamplerEXPT8", "video_steps"): 4,
        ("MiniMaxH3MultiRateSamplerEXPT8", "audio_steps"): 10,
        ("MiniMaxH3MultiRateSamplerEXPT8", "shift_video"): 12.0,
        ("MiniMaxH3MultiRateSamplerEXPT8", "shift_audio"): 3.0,
        ("MiniMaxH3ReferenceToVideo", "length"): 124,
        ("MiniMaxH3ReferenceToVideo", "ref_image_size"): "match",
        ("MiniMaxH3ReferenceToVideo", "strict_prompt_tags"): True,
        ("VHS_LoadVideo", "format"): "H3",
        ("VHS_VideoCombine", "save_output"): True,
        ("VHS_VideoCombine", "pingpong"): False,
        ("VHS_VideoCombine", "format"): "video/h264-mp4",
        ("VHS_VideoCombine", "filename_prefix"): "金鱼本地_H3Ref2VA",
    }
    # 按 class_type 分组，逐节点套用
    by_cls: dict[str, list[str]] = {}
    for nid, n in wf.items():
        by_cls.setdefault(n["class_type"], []).append(nid)
    for (cls, key), val in OVERRIDE.items():
        for nid in by_cls.get(cls, []):
            # video VAE / audio VAE 两个 VAELoader 按序区分
            if (cls, key) == ("VAELoader", "vae_name"):
                continue
            wf[nid]["inputs"][key] = val
    # VAELoader 36=video 37=audio，按节点 id 精确指定
    # 注意：API 图的 key 是字符串，必须用 str(id) 查找
    for nid, name in (("36", "minimax_h3_video_vae_fp16.safetensors"),
                      ("37", "minimax_h3_audio_vae_fp32.safetensors")):
        if nid in wf:
            wf[nid]["inputs"]["vae_name"] = name
            print(f"  VAELoader#{nid} -> {name}")
    # LoRA 按节点 id 精确指定（枚举列表，object_info 的 default 取不到）
    for nid, name in (("342", "minimax_h3_turbo_4步加速_"
                            "DasiwaREF2VAHybridV1_curveproj1025_compat_v001-T8.safetensors"),
                      ("343", "H3_Combat_V2.safetensors"),
                      ("53", "h3\\minimax_h3_turbo_4步加速_"
                           "DasiwaREF2VAHybridV1_curveproj1025_compat_v001-T8.safetensors"),
                      ("400", "h3\\MysticXXX_MMH3-V2.safetensors")):
        if nid in wf:
            wf[nid]["inputs"]["lora_name"] = name
            print(f"  Lora#{nid} -> {name}")
    print(f"显式覆盖 {len(OVERRIDE)} 类控件")

    # ---- 补模型链的断点 ----
    # 金鱼原图里 Lora#343 的 model 输入是连线（来自 UNETLoader#192），
    # 但 RH 导出成前端 JSON 时这条 link 丢失，转换后 inputs 里是脏字符串。
    # 这里按「Lora 的 model 若不是 [node, slot] 形式，就接到 UNETLoader」补齐。
    unet = next((nid for nid, n in wf.items()
                 if n["class_type"] == "UNETLoader"), None)
    if unet:
        fixed_model = 0
        for nid, n in wf.items():
            if n["class_type"] != "LoraLoaderModelOnly":
                continue
            v = n["inputs"].get("model")
            if not (isinstance(v, list) and len(v) == 2 and str(v[0]) in wf):
                n["inputs"]["model"] = [unet, 0]
                fixed_model += 1
        print(f"补齐 LoraLoader.model -> UNETLoader#{unet}：{fixed_model} 处")

    # ---- 强制填的 VHS 参数 ----
    for nid, n in wf.items():
        if n["class_type"] == "VHS_LoadVideo":
            n["inputs"]["video"] = vids[0]
            n["inputs"]["force_rate"] = 0
        if n["class_type"] == "VHS_VideoCombine":
            n["inputs"].update({"save_output": True, "pingpong": False,
                                "format": "video/h264-mp4",
                                "filename_prefix": "金鱼本地_H3Ref2VA",
                                "frame_rate": 25})

    # ---- 素材与提示词（必须放在重铺之后，否则会被清掉）----
    img_nodes = sorted(find_nodes(wf, "LoadImage"), key=int)
    for i, nid in enumerate(img_nodes):
        wf[nid]["inputs"]["image"] = imgs[i % len(imgs)]
    aud_nodes = sorted(find_nodes(wf, "LoadAudio"), key=int)
    for i, nid in enumerate(aud_nodes):
        wf[nid]["inputs"]["audio"] = auds[i % len(auds)]
    prompt = PROMPT_TXT.read_text(encoding="utf-8").strip()
    for nid in find_nodes(wf, "Text"):
        wf[nid]["inputs"]["text"] = prompt
    print(f"LoadImage {len(img_nodes)} 个 / LoadAudio {len(aud_nodes)} 个 / "
          f"提示词 {len(prompt)} 字")

    Path("F:/h3tmp/jinyu_submitted.json").write_text(
        json.dumps(wf, ensure_ascii=False, indent=1), encoding="utf-8")

    try:
        pid = api("/prompt", {"prompt": wf, "client_id": str(uuid.uuid4())})["prompt_id"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        print(f"\nHTTP {e.code} 提交被拒：\n{body[:3000]}")
        return
    print("\nprompt_id =", pid)
    t0 = time.time()
    while True:
        h = api(f"/history/{pid}")
        if pid in h:
            st = h[pid]["status"]
            print(f"耗时 {time.time()-t0:.0f}s  状态 {st.get('status_str')}")
            if st.get("status_str") != "success":
                for m in st.get("messages", []):
                    if isinstance(m, list) and isinstance(m[1], dict) and "exception_message" in m[1]:
                        print(f"  错误节点 {m[1].get('node_id')} [{m[1].get('node_type')}]")
                        print("   ", m[1]["exception_message"].strip()[:300])
                return
            for out in h[pid]["outputs"].values():
                for v in out.get("gifs", []) + out.get("videos", []):
                    print("  产出:", v.get("filename"))
            return
        q = api("/queue")
        print(f"耗时 {time.time()-t0:.0f}s  pending={len(q.get('queue_pending', []))}")
        time.sleep(20)


if __name__ == "__main__":
    main()
