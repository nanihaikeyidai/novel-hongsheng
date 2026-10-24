"""金鱼工作流（3 参考图版）本地实跑提交器。

节点依赖已在本地装齐：
  comfyui-SelfLift   -> SelfLiftH3Sampler
  ComfyUI-KJNodes    -> SetNode/GetNode（纯前端节点，已由 expand_setget.py 展开）
模型全部本地已有（upscaler / LoRA / VAE 均齐）。
"""
from __future__ import annotations

import json
import shutil
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from local_h3_ref2va_test import api  # noqa: E402

API_JSON = Path("F:/h3tmp/jinyu_ref3_expanded.json")
COMFY = Path(r"F:\Work-Fisher纯净包2026.8.7\ComfyUI")
ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
PROMPT_TXT = (ROOT / "05-workflow/ep04/红绳片段09c_陆定天的名字"
              / "动作流_H3纯提示词.txt")

# 审讯场景只需 2 人物 + 1 场景
IMAGES = [
    "05-workflow/ep04/归档素材/人物/陆沉_人设.png",
    "05-workflow/ep04/归档素材/人物/审讯员老韩_人设_单人.png",
    "05-images/场景/场景_ND审问室_日漫v3.png",
]
AUDIOS = ["05-workflow/归档素材/人物参考音色/老韩.wav",
          "05-workflow/归档素材/人物参考音色/陆沉.wav"]
VIDEOS = [
    "05-workflow/ep04/红绳片段09c_陆定天的名字/视频草稿/"
    "E04-09c_陆定天的名字_v4_未审核草稿.mp4",
]


def stage(src: Path, sub: str) -> str:
    dst_dir = COMFY / "input" / sub
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    if not dst.exists():
        shutil.copy(src, dst)
    return f"{sub}/{src.name}"


def find_nodes(wf: dict, cls: str) -> list[str]:
    return sorted((k for k, v in wf.items() if v["class_type"] == cls), key=int)


def main() -> None:
    wf = json.loads(API_JSON.read_text(encoding="utf-8"))

    imgs = [stage(ROOT / p, "jinyu_img") for p in IMAGES]
    auds = [stage(ROOT / p, "jinyu_aud") for p in AUDIOS]
    vids = [stage(ROOT / p, "jinyu_vid") for p in VIDEOS]
    print(f"参考图 {len(imgs)} 张: {[Path(i).name for i in imgs]}")
    print(f"参考音频 {len(auds)} 条: {[Path(a).name for a in auds]}")
    print(f"参考视频 {len(vids)} 段")

    oi = api("/object_info")

    # ---- 1. 只保留连线，其余控件按 object_info default 铺 ----
    linked = 0
    for nid, n in wf.items():
        keep = {k: v for k, v in n["inputs"].items()
                if isinstance(v, list) and len(v) == 2
                and isinstance(v[0], str) and v[0] in wf
                and isinstance(v[1], int)}
        n["inputs"] = keep
        linked += len(keep)
    print(f"保留连线 {linked} 个")

    for nid, n in wf.items():
        spec = oi.get(n["class_type"], {}).get("input", {})
        for sec in ("required", "optional"):
            for k, meta in (spec.get(sec) or {}).items():
                if n["inputs"].get(k) is not None:
                    continue
                if not isinstance(meta, list) or not meta:
                    continue
                head = meta[0]
                if isinstance(head, str) and len(meta) > 1 and isinstance(meta[1], dict):
                    default = meta[1].get("default")
                elif not isinstance(head, list):
                    default = head
                else:
                    continue
                # default == 类型名/管理器名 => 这是需要连线对象的可选输入
                if isinstance(default, str) and default == head and (
                        head.isupper() or head.endswith("Manager")):
                    continue
                # COMFY_DYNAMICCOMBO_V3 等动态组合框：default 是 dict，
                # 直接采用（它自带选中项与子参数）
                if isinstance(default, dict):
                    n["inputs"][k] = default
                    continue
                if isinstance(default, list) or not isinstance(
                        default, (int, float, str, bool)):
                    continue
                n["inputs"][k] = default

    # ---- 2. 显式覆盖 ----
    def by_cls(cls: str) -> list[str]:
        return find_nodes(wf, cls)

    for nid in by_cls("UNETLoader"):
        wf[nid]["inputs"]["unet_name"] = (
            "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors")
        wf[nid]["inputs"]["weight_dtype"] = "default"
    for nid in by_cls("CLIPLoader"):
        wf[nid]["inputs"]["clip_name"] = "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"
        wf[nid]["inputs"]["type"] = "minimax"
    for nid in by_cls("ResolutionSelector"):
        wf[nid]["inputs"]["megapixels"] = 0.5
        wf[nid]["inputs"]["aspect_ratio"] = "16:9 (Widescreen)"
    for nid in by_cls("RandomNoise"):
        wf[nid]["inputs"]["noise_seed"] = 29732110694208
    for nid in by_cls("MiniMaxH3ReferenceToVideo"):
        wf[nid]["inputs"]["ref_image_size"] = "match"
        wf[nid]["inputs"]["strict_prompt_tags"] = True
    for nid in by_cls("VHS_LoadVideo"):
        wf[nid]["inputs"]["format"] = "H3"
    for nid in by_cls("VHS_VideoCombine"):
        wf[nid]["inputs"].update({
            "save_output": True, "pingpong": False,
            "format": "video/h264-mp4", "frame_rate": 25,
            "filename_prefix": "金鱼本地_3图Ref2VA",
        })

    # COMFY_DYNAMICCOMBO_V3（动态组合框）的正确填法：
    #   selection       = 选中项的 key（字符串），如 "sol-attn"
    #   selection.<子参数> = 子参数值，如 "selection.tau" = 1.3
    # 不是嵌套 dict —— 嵌套会报 missing 1 required positional argument: 'selection'。
    # 参照 comfyui-vrgamedevgirl/VRGDG_WorkflowRunnerNodes.py 的官方用法。
    for nid in by_cls("BlockSparseAttention"):
        wf[nid]["inputs"].update({
            "selection": "sol-attn",
            "selection.tau": 1.3,
            "start_percent": 0.2,
            "end_percent": 1.0,
            "dense_blocks": "",
            "min_tokens": 12288,
            "extra_tokens": 256,
            "sink_conditioning": "exact_kv_and_rows",
            "verbose": False,
        })
        print(f"  BlockSparseAttention#{nid} selection=sol-attn(tau=1.3)")

    # VAELoader / LoRA 按节点 id 精确指定
    vae_map = {"36": "minimax_h3_video_vae_fp16.safetensors",
               "37": "minimax_h3_audio_vae_fp32.safetensors"}
    for nid, name in vae_map.items():
        if nid in wf:
            wf[nid]["inputs"]["vae_name"] = name
            print(f"  VAELoader#{nid} -> {name}")
    lora_map = {
        "342": "h3\\minimax_h3_turbo_4步加速_DasiwaREF2VAHybridV1_"
               "curveproj1025_compat_v001-T8.safetensors",
        "343": "H3_Combat_V2.safetensors",
        "53": "h3\\minimax_h3_turbo_4步加速_DasiwaREF2VAHybridV1_"
              "curveproj1025_compat_v001-T8.safetensors",
        "400": "h3\\MysticXXX_MMH3-V2.safetensors",
        # 344/345 是金鱼原图的战斗系 LoRA（H3_Fight_Flow / Motion_Repair），
        # 审讯场景用不到，但节点在主链上必须给合法值，
        # 否则报 required_input_missing。用强度 0 等效旁路。
        "344": "h3\\minimax_h3_turbo_v4_step600_ema_DasiwaREF2VAHybridV1_"
               "0_curveproj1025_compat_v001.safetensors",
        "345": "h3\\minimax_h3_turbo_v4_step600_ema_DasiwaREF2VAHybridV1_"
               "0_curveproj1025_compat_v001.safetensors",
    }
    for nid, name in lora_map.items():
        if nid in wf:
            wf[nid]["inputs"]["lora_name"] = name
            print(f"  Lora#{nid} -> {name}")
    # 战斗系 LoRA 强度归零，等效旁路
    for nid in ("344", "345"):
        if nid in wf:
            wf[nid]["inputs"]["strength_model"] = 0.0

    # 采样器与调度器：COMBO 型枚举，object_info 只给类型名，
    # 必须显式指定合法值（SelfLift 只接受标准 Euler）
    #
    # 本地单卡 16GB 关掉「两段采样」（低分辨率 -> 升采样 -> 高分辨率）。
    # 原参数 transition_step=6 / lowres_scale=0.5 会把 20 步拆成
    #   低分辨率  6 步 × 290s = 1740s
    #   过渡升采样          =   30s
    #   高分辨率 14 步 × 176s = 2464s
    # 合计约 70 分钟，本地跑不动。
    #
    # 关掉的办法（注意 transition_step 的 min 是 1，不能填 0）：
    #   lowres_scale    = 1.0   低分辨率段与目标同尺寸 —— 关键就是这一条，
    #                             它让「低分辨率段」退化成全分辨率的一段，
    #                             于是两段变一段、NFE 不变
    #   w_max           = 0.0   关掉 VAE 像素锚点修正，省掉一次 VAE 往返
    #   upscaler_model  = none   不用学习式 latent upscaler
    #   transition_step = 1     取 schema 允许的最小值，只做 1 次低分辨率评估
    #                             就立刻升到高分辨率，实质跳过低分辨率段
    # 4 步 turbo 加速 LoRA 已挂（Lora#342 / Lora#53）；
    # 二采已关（见下方 SelfLift 参数段）。
    STEPS = 4
    # 0.6MP -> 1056x608，15 秒 @25fps = 375 帧。
    # 注意 H3 要求宽高被 32 整除，ResolutionSelector 会自动对齐。
    MEGAPIXELS = 0.6
    FRAMES = 375
    for nid in by_cls("KSamplerSelect"):
        wf[nid]["inputs"]["sampler_name"] = "euler"
    for nid in by_cls("BasicScheduler"):
        # 注意必须显式赋值，不能 setdefault——
        # 控件重铺阶段已把 object_info 的默认值（steps=20）写进来了。
        wf[nid]["inputs"]["scheduler"] = "simple"
        wf[nid]["inputs"]["steps"] = STEPS
        wf[nid]["inputs"]["denoise"] = 1.0
        print(f"  BasicScheduler#{nid} -> simple / steps={STEPS}")

    for nid in by_cls("SelfLiftH3Sampler"):
        wf[nid]["inputs"].update({
            # 关掉两段采样的三步走（节点自身有互斥校验，见 comfyui-SelfLift/nodes.py:500）：
            #   1) transition_step=1 -> 低分段只做 1 次评估，剩下全给高分辨率段
            #   2) lowres_scale=1.0  -> 低分段与目标同尺寸，nearest 直接升采样退化为恒等
            #   3) rho 给小正值过校验，但 w_max=0 -> need_pix = rho>0 and w_max>0 为假，
            #      完全跳过 VAE 解码+重编码的像素锚往返（本地单卡最吃显存的一步）
            #      校验拦的是 rho==0 and upscaler_model=="none"，所以 rho 不能填 0
            "transition_step": 1,
            "lowres_scale": 1.0,
            "rho": 0.05,                  # 仅用于越过互斥校验，w_max=0 时修正被短路
            "w_min": 0.0,
            "w_max": 0.0,                  # 关键：关掉像素-VAE 锚点修正
            "upscaler_model": "none",     # 不加载外部 latent upscaler（省一份显存）
            "highres_tiling": False,
            "upscaler_unload": True,
            "cfg": 5.0,
        })
        print(f"  SelfLift#{nid} -> 单段全分辨率（两段采样已关闭）")

    for nid in by_cls("ResolutionSelector"):
        wf[nid]["inputs"]["megapixels"] = MEGAPIXELS
        print(f"  ResolutionSelector#{nid} -> {MEGAPIXELS}MP")

    # Lora 的 model 若不是连线形式，补接到 UNETLoader
    unet = next((n for n in by_cls("UNETLoader")), None)
    if unet:
        fixed = 0
        for nid in by_cls("LoraLoaderModelOnly"):
            v = wf[nid]["inputs"].get("model")
            if not (isinstance(v, list) and len(v) == 2 and str(v[0]) in wf):
                wf[nid]["inputs"]["model"] = [unet, 0]
                fixed += 1
        if fixed:
            print(f"补齐 LoraLoader.model -> UNETLoader#{unet}：{fixed} 处")

    # ---- 3. 填素材与提示词 ----
    # 注意：object_info 的 default 回填对「动态输入」无效——
    # VHS_LoadVideo.video 是运行时扫描 input/ 目录生成的，
    # PrimitiveFloat.value 这类更是没有 schema，
    # 所以它们必须显式指定，否则报 missing 1 required positional argument。
    for nid in by_cls("VHS_LoadVideo"):
        wf[nid]["inputs"]["video"] = vids[0]
        wf[nid]["inputs"]["format"] = "H3"
        wf[nid]["inputs"]["force_rate"] = 0
    for nid in by_cls("PrimitiveFloat"):
        wf[nid]["inputs"]["value"] = FRAMES   # 目标帧长，约 4 秒 @25fps

    # ComfyMathExpression 的 values.a / values.b 是「由表达式里出现的变量名」
    # 动态生成的输入槽，object_info 里查不到，必须显式给。
    # 金鱼原图里 a=来自 PrimitiveFloat 的帧长、b=未接（表达式 a + b）。
    for nid in by_cls("ComfyMathExpression"):
        wf[nid]["inputs"]["values.a"] = FRAMES
        wf[nid]["inputs"]["values.b"] = 0
        wf[nid]["inputs"]["expression"] = "a"
        print(f"  ComfyMathExpression#{nid} -> a={FRAMES}, 表达式简化为 a")
    for i, nid in enumerate(by_cls("LoadImage")):
        wf[nid]["inputs"]["image"] = imgs[i % len(imgs)]
    for i, nid in enumerate(by_cls("LoadAudio")):
        wf[nid]["inputs"]["audio"] = auds[i % len(auds)]
    prompt = PROMPT_TXT.read_text(encoding="utf-8").strip()
    for nid in by_cls("Text"):
        wf[nid]["inputs"]["text"] = prompt
    print(f"LoadImage {len(by_cls('LoadImage'))} / "
          f"LoadAudio {len(by_cls('LoadAudio'))} / 提示词 {len(prompt)} 字")

    Path("F:/h3tmp/jinyu_ref3_submitted.json").write_text(
        json.dumps(wf, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- 提交前自检：可达性 + 悬空连线 ----
    # 教训：ComfyUI 只执行「能到达 OUTPUT 节点」的路径。
    # 若图里混进了 RunningHub 的分组标注节点（本身是 OUTPUT_NODE），
    # 整张主链会被判不可达 -> 20 秒空跑、status 仍报 success、
    # history.outputs 为空、磁盘无产出。提交前先自检能省掉一整轮等待。
    oi_ids = set(oi)
    unknown = sorted({v["class_type"] for v in wf.values()
                      if v["class_type"] not in oi_ids})
    if unknown:
        print(f"⚠ 本地不存在的节点类型：{unknown}")
    dangling = [(k, kk, vv) for k, v in wf.items()
                for kk, vv in v["inputs"].items()
                if isinstance(vv, list) and len(vv) == 2
                and isinstance(vv[0], str) and vv[0] not in wf]
    if dangling:
        print(f"⚠ 悬空连线：{dangling}")

    consumers: dict[str, set] = {}
    for v in wf.values():
        for vv in v["inputs"].values():
            if isinstance(vv, list) and len(vv) == 2 and str(vv[0]) in wf:
                consumers.setdefault(str(vv[0]), set()).add(v["class_type"])
    # object_info 里没有 output_node 字段（那是 ComfyUI 内建的执行标记），
    # 所以按「没有任何下游消费者」反推输出节点。
    outputs = [nid for nid in wf if nid not in consumers]
    reachable: set[str] = set()
    stack = list(outputs)
    while stack:
        cur = stack.pop()
        if cur in reachable:
            continue
        reachable.add(cur)
        for vv in wf[cur]["inputs"].values():
            if isinstance(vv, list) and len(vv) == 2 and str(vv[0]) in wf:
                stack.append(str(vv[0]))
    dead = sorted(set(wf) - reachable)
    print(f"输出节点 {outputs}；可达 {len(reachable)}/{len(wf)}；"
          f"不可达 {len(dead)} 个 {dead if dead else ''}")
    if not outputs:
        print("⚠ 没有输出节点，整图不会执行")

    try:
        pid = api("/prompt", {"prompt": wf,
                              "client_id": str(uuid.uuid4())})["prompt_id"]
    except urllib.error.HTTPError as e:
        print(f"\nHTTP {e.code}：\n{e.read().decode('utf-8', 'replace')[:2500]}")
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
                    if (isinstance(m, list) and isinstance(m[1], dict)
                            and "exception_message" in m[1]):
                        print(f"  错误节点 {m[1].get('node_id')} "
                              f"[{m[1].get('node_type')}]")
                        print("   ", m[1]["exception_message"].strip()[:300])
                return
            for out in h[pid]["outputs"].values():
                for v in out.get("gifs", []) + out.get("videos", []):
                    print("  产出:", v.get("filename"))
            return
        print(f"耗时 {time.time()-t0:.0f}s  "
              f"pending={len(api('/queue').get('queue_pending', []))}")
        time.sleep(20)


if __name__ == "__main__":
    main()
