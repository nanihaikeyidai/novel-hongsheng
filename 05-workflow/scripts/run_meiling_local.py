"""梅林全流程工作流 -> 本地 ComfyUI 提交器（API 格式）。

背景
----
梅林全流程（`user/default/workflows/梅林全流程.json`，107 节点）是界面用的
前端 JSON，不能直接 POST。前端在提交前会做几件事，这里全部复现：

  1. Reroute 直通压平（9 个）—— 后端查不到该类型，直接删会断流
  2. 删纯前端节点：MarkdownNote / Note / 忽略多组孤海
     —— 「忽略多组孤海」是 RunningHub 分组标注，本身带 OUTPUT_NODE，
        不删会抢走执行，表现为 20 秒空跑
  3. Fast Groups Bypasser (rgthree) —— 界面分组开关，图转 API 后失效
  4. 控件重铺：widgets_values 顺序与 object_info.required 顺序不一定对齐
     （RunningHub 有自定义控件），所以按 object_info 的 default 重铺
  5. 动态输入显式赋值（object_info 的 default 对它们无效）

梅林与金鱼的关键差异：**没有 SelfLift，天然单段采样，不需要关二采。**

用法
----
  python run_meiling_local.py --clip 红绳片段12g_你在骗我
  python run_meiling_local.py --clip 红绳片段12g_你在骗我 --megapixels 0.35 --frames 97
  python run_meiling_local.py --dry-run          # 只打印计划不提交
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

HOST = "http://127.0.0.1:8188"
PROJ = Path(r"D:\HermesWorkspace\ai小说\红绳")
WF_SRC = Path(r"F:\Work-Fisher纯净包2026.8.7\ComfyUI\user\default\workflows\梅林全流程.json")
API_TMP = Path("F:/h3tmp/meiling_api.json")

EP04 = PROJ / "05-workflow" / "ep04"
ASSET = EP04 / "归档素材"

COMFY = Path(r"F:\Work-Fisher纯净包2026.8.7\ComfyUI")
INPUT_DIR = COMFY / "input"

# 参考图按角色配对：审讯场景 2 人 + 1 场景 = 3 张（用户要求参考图不超过 6 张）
# LoadImage 只能读 ComfyUI/input/，素材在项目盘，所以提交前先拷进去。
REF_ASSETS = [
    EP04 / "归档素材" / "人物" / "陆沉_人设.png",
    EP04 / "归档素材" / "人物" / "审讯员老韩_人设_单人.png",
    PROJ / "05-images" / "场景" / "场景_ND审问室_日漫v3.png",
]
# 主视频槽位 6 个参考图：人物各占 1，其余用场景图补齐
REF_SLOTS = 6
# 实际接几张（审讯场景 = 2 人 + 1 场景）
REF_IMAGES = 3


def stage_images() -> list[str]:
    """把参考图拷进 ComfyUI/input/，返回可用的文件名列表。"""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    names: list[str] = []
    for src in REF_ASSETS:
        if not src.exists():
            sys.exit(f"[缺素材] {src}")
        dst = INPUT_DIR / src.name
        if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
            shutil.copy2(src, dst)
        names.append(src.name)
    # 第 3 个（场景）铺满剩余槽位
    while len(names) < REF_SLOTS:
        names.append(REF_ASSETS[-1].name)
    return names[:REF_SLOTS]


def res_16x9(megapixels: float) -> tuple[int, int]:
    """megapixels -> 16:9 且被 32 整除的宽高。

    H3 要求宽高必须被 32 整除，否则 latent 对齐会报错。
    做法：先按面积和比例解出理论高，再各自对齐到 32。
    """
    h = round((megapixels * 1_000_000 * 9 / 16) ** 0.5 / 32) * 32
    w = round(h * 16 / 9 / 32) * 32
    return int(w), int(h)


def api(method: str, path: str, body=None):
    url = f"{HOST}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def repour_controls(wf: dict, oi: dict) -> None:
    """按 object_info 补齐缺失控件。

    只补缺失，不动已有值 —— 理由见函数体内注释。

    为什么必须重铺：widgets_values 是前端控件顺序，与 object_info.required
    的顺序在 RunningHub 自定义控件上对不上，直接塞会张冠李戴。
    """
    for nid, n in wf.items():
        # 注意：这里只「补缺失」，绝不清空重铺。
        # expand_setget.py 已经按 object_info 的 required 顺序把 widgets_values
        # 正确映射成 API 的 inputs 了；清空再按 default 重填会把 unet_name、
        # clip_name 这类必填项丢成 None（因为它们的 default 就是类型名本身）。
        spec = oi.get(n["class_type"], {}).get("input", {}).get("required", {})
        for k, meta in spec.items():
            if k in n["inputs"]:
                continue          # 已有值（含连线），不动
            head = meta[0]
            default = meta[1] if len(meta) > 1 and isinstance(meta[1], dict) else {}
            dv = default.get("default")
            # 必填但无 default 的控件（COMBO 型）：从 meta[0] 的首项取
            if isinstance(head, list):
                n["inputs"][k] = head[0] if head else ""
                continue
            if dv is None:
                continue
            # default 恰好等于输入类型名（MODEL/VAE/CLIP/...）=> 需连线对象，跳过
            if isinstance(dv, str) and dv == head and (head.isupper()
                                                       or head.endswith("Manager")):
                continue
            n["inputs"][k] = dv

        # 补 optional 里 object_info 给了 default 的项（如 upscaler_unload）
        for k, meta in oi.get(n["class_type"], {}).get("input", {}) \
                .get("optional", {}).items():
            if k in n["inputs"] or not isinstance(meta[0], str):
                continue
            default = meta[1] if len(meta) > 1 and isinstance(meta[1], dict) else {}
            if "default" in default:
                n["inputs"][k] = default["default"]


def mark_bypassed(wf: dict) -> int:
    """标出主视频链之外的所有节点（旁支生图 / SeedVR 放大 / 标注）。

    判定方式：以 VHS_VideoCombine（主视频输出）反向追溯到的节点集合 =
    主链。其余全部是「角色资产生成 / 三视图生成 / 场景资产生成 / SeedVR 放大」
    这些旁支，它们在原图里都是 mode=4（bypass）。

    API 图没有 bypass 语义，旁支会照样参与校验并因缺必填输入报错
    （TextEncodeQwenImage21 缺 negative_prompt、
    MiniMaxH3LightX2VSLAAuditT8Advanced 缺 runtime/av_latent）。
    补默认值是错的做法 —— 补了值反而会把关闭的支线跑起来。正确做法是整条删掉。
    """
    src = json.loads(WF_SRC.read_text(encoding="utf-8"))
    snodes = {n["id"]: n for n in src["nodes"]}
    by_link = {l[0]: l for l in src["links"]}

    # 找到主视频输出节点（VHS_VideoCombine）
    main_out = next((i for i, n in snodes.items()
                     if n["type"] == "VHS_VideoCombine"
                     and not n.get("mode")), None)
    if main_out is None:
        sys.exit("[致命] 原图里找不到启用的 VHS_VideoCombine")

    main: set[int] = set()

    def walk(nid: int) -> None:
        if nid in main:
            return
        main.add(nid)
        n = snodes.get(nid)
        if not n:
            return
        for i in n.get("inputs", []):
            if i.get("link"):
                walk(by_link[i["link"]][1])

    walk(main_out)

    marked = 0
    for nid in list(wf):
        if int(nid) not in main:
            wf[nid]["_bypass"] = True
            marked += 1
    print(f"  主视频链 {len(main)} 节点，旁支 {marked} 节点（生图/放大/标注）")
    return marked


def drop_bypassed(wf: dict) -> int:
    """删除标记为 _bypass 的节点，并清理指向它们的连线。"""
    dead = {nid for nid, n in wf.items() if n.get("_bypass")}
    before = len(wf)
    for nid in dead:
        wf.pop(nid, None)
    for n in wf.values():
        for k, v in list(n["inputs"].items()):
            if isinstance(v, list) and len(v) == 2 and str(v[0]) not in wf:
                n["inputs"].pop(k)
        n.pop("_bypass", None)
    return before - len(wf)


def apply_clip(wf: dict, clip_dir: Path, megapixels: float, frames: int,
               steps: int, ref_images: int = 3,
               args_spark: bool = True) -> None:
    """填入片段提示词、素材与渲染参数。"""

    def by_cls(t: str) -> list[str]:
        return [nid for nid, n in wf.items() if n["class_type"] == t]

    # ---- 提示词：所有 CR Text / Text 都用本片段的 ----
    prompt_file = clip_dir / "动作流_H3纯提示词.txt"
    if not prompt_file.exists():
        sys.exit(f"[缺文件] {prompt_file}")
    prompt = prompt_file.read_text(encoding="utf-8").strip()
    n_text = 0
    for t in ("CR Text", "Text", "Textbox",
              "PrimitiveStringMultiline", "PrimitiveString"):
        for nid in by_cls(t):
            # 键名按节点实际签名决定：CR Text 用 text，
            # Primitive* 系列用 value（不能靠「inputs 里有没有该键」来猜，
            # 因为控件补齐阶段可能还没写进去）
            if t.startswith("Primitive"):
                key = "value"
            elif "text" in wf[nid]["inputs"]:
                key = "text"
            else:
                key = "text"
            wf[nid]["inputs"][key] = prompt
            n_text += 1
    if n_text == 0:
        sys.exit("[致命] 没找到任何提示词节点，主视频链不完整")
    print(f"  提示词 {len(prompt)} 字 -> {n_text} 个文本节点")

    # ---- 参考图：人物 + 场景（LoadImage 只能读 ComfyUI/input/）----
    # 关键：H3 的视觉 token 数随参考图数量线性增长，接满 6 槽会在
    # SamplerCustomAdvanced 报 mat1/mat2 形状不匹配（实测 3925x2560 vs 5120x5376）。
    # 审讯场景只需 2 人 + 1 场景 = 3 张（用户明确要求参考图不超过 6 张）。
    imgs = stage_images()[:ref_images]
    load = by_cls("LoadImage")
    for i, nid in enumerate(load):
        wf[nid]["inputs"]["image"] = imgs[i % len(imgs)]
    # 多余的参考图槽位（ref_image_3..5）直接断开连线，
    # 让 H3 节点的 AUTOGROW 列表只拿到 3 张
    cut = 0
    for nid in by_cls("MiniMaxH3ReferenceToVideo"):
        for k in list(wf[nid]["inputs"]):
            if k.startswith("ref_images.ref_image_") and k not in {
                f"ref_images.ref_image_{i}" for i in range(len(imgs))}:
                wf[nid]["inputs"].pop(k)
                cut += 1
    print(f"  参考图 {len(imgs)} 张 -> {len(load)} 个 LoadImage，断开多余槽位 {cut} 处")

    # ---- 渲染参数 ----
    # 注意：ResolutionSelector 有两个 —— #115 是主视频分辨率，#213 喂给
    # EmptyLatentImage(209) 走生图支线。只改 #115，别把生图尺寸一起压。
    # aspect_ratio 也必须显式写回 16:9：控件重铺会把它覆成 object_info
    # 枚举里的第一项（1:1 Square），出片会变正方形。
    for nid in by_cls("ResolutionSelector"):
        if nid == "115":
            wf[nid]["inputs"]["aspect_ratio"] = "16:9 (Widescreen)"
            wf[nid]["inputs"]["megapixels"] = megapixels

    # EmptyLatentImage 的 244/269 是三视图/立绘支线的 latent（竖屏 1080x1920），
    # 控件重铺会把它们覆成 object_info 默认的 1024x1024，这里按原图尺寸还原。
    # 209 是生图支线（原本 1024x1024），保持不变。
    VERTICAL = {"244": (1080, 1920), "269": (1080, 1920)}
    for nid, (w, h) in VERTICAL.items():
        if nid in wf and wf[nid]["class_type"] == "EmptyLatentImage":
            wf[nid]["inputs"]["width"] = w
            wf[nid]["inputs"]["height"] = h

    for nid in by_cls("BasicScheduler"):
        wf[nid]["inputs"]["scheduler"] = "simple"
        wf[nid]["inputs"]["steps"] = steps
        wf[nid]["inputs"]["denoise"] = 1.0
    for nid in by_cls("KSamplerSelect"):
        wf[nid]["inputs"]["sampler_name"] = "euler"
    for nid in by_cls("PrimitiveFloat"):
        wf[nid]["inputs"]["value"] = frames

    # MiniMaxH3ReferenceToVideo 的帧数参数叫 length（不是 num_frames），
    # 且 width/height 必须与 ResolutionSelector 输出一致。
    # 16:9 下按 megapixels 反算，再对齐到 32（H3 硬约束）。
    vw, vh = res_16x9(megapixels)
    for nid in by_cls("MiniMaxH3ReferenceToVideo"):
        wf[nid]["inputs"]["length"] = frames
        wf[nid]["inputs"]["width"] = vw
        wf[nid]["inputs"]["height"] = vh

    # SPARK 稀疏注意力的参数必须跟它自带的官方工作流对齐。
    # 官方 spark_h3_lbh_official_lightx2v_4step_5p2s_i2va.json 的取值是
    # warmup_ratio=0.0 / topk_ratio=0.1（梅林原图写的是 0.2/0.2）。
    # steps 必须等于 BasicScheduler 的步数，否则稀疏节奏与实际采样步错位。
    for nid in by_cls("MiniMaxH3SparkAttentionSM89"):
        wf[nid]["inputs"]["steps"] = steps
        wf[nid]["inputs"]["warmup_ratio"] = 0.0
        wf[nid]["inputs"]["warmup_steps"] = 0
        wf[nid]["inputs"]["topk_ratio"] = 0.1
        # enabled=False 时节点直通，等价于「不启用稀疏加速」，
        # 用于排查 mat1/mat2 形状不匹配
        if args_spark is False:
            wf[nid]["inputs"]["enabled"] = False

    # LoRA 必须回读原图真值：控件补齐阶段会把两个不同 LoRA 都填成
    # object_info 枚举首项（实测两个都成了 H3_Combat_V2）。
    src = json.loads(WF_SRC.read_text(encoding="utf-8"))
    for n in src["nodes"]:
        t, wv = n.get("type"), n.get("widgets_values") or []
        if t == "LoraLoaderBypassModelOnly" and str(n["id"]) in wf:
            if wv:
                wf[str(n["id"])]["inputs"]["lora_name"] = wv[0]
            if len(wv) > 1:
                wf[str(n["id"])]["inputs"]["strength_model"] = wv[1]
    print(f"  LoRA {[wf[x]['inputs']['lora_name'] for x in wf if wf[x]['class_type']=='LoraLoaderBypassModelOnly']}")
    print(f"  视频尺寸 {vw}x{vh}")

    # ---- 输出前缀标记来源片段 ----
    tag = clip_dir.name.replace("红绳片段", "")
    for nid in by_cls("VHS_VideoCombine"):
        wf[nid]["inputs"]["filename_prefix"] = f"红绳_ep04/{tag}"

    print(f"  参数 {megapixels}MP / {frames}帧 / {steps}步")
    for nid in ("115", "244", "269"):
        if nid in wf:
            print(f"    #{nid} {wf[nid]['class_type']} "
                  f"{json.dumps(wf[nid]['inputs'], ensure_ascii=False)[:90]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip", required=True, help="片段目录名，如 红绳片段12g_你在骗我")
    ap.add_argument("--megapixels", type=float, default=0.6)
    ap.add_argument("--frames", type=int, default=192)
    ap.add_argument("--steps", type=int, default=15)
    ap.add_argument("--ref-images", type=int, default=REF_IMAGES,
                    help="接几张参考图（2 人 + 1 场景 = 3）")
    ap.add_argument("--spark", dest="spark", action="store_true", default=True,
                    help="启用 SPARK 稀疏注意力（默认开）")
    ap.add_argument("--no-spark", dest="spark", action="store_false",
                    help="关闭 SPARK，用于排查形状不匹配")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    clip_dir = EP04 / args.clip
    if not clip_dir.exists():
        sys.exit(f"[缺目录] {clip_dir}")

    print(f"=== 片段 {args.clip} ===")
    wf = json.loads(API_TMP.read_text(encoding="utf-8"))
    oi = api("GET", "/object_info")

    marked = mark_bypassed(wf)
    print(f"  标记 bypass 节点 {marked} 个")

    repour_controls(wf, oi)
    print(f"  控件补齐完成（{len(wf)} 节点）")

    # ---- 删掉 mode!=0（bypass / 关闭）的节点及其下游 ----
    # 梅林原图把「角色资产生成 / 三视图生成 / SeedVR 放大」这些支线整条设为
    # mode=4（bypass）。bypass 是前端概念，API 图里没有，
    # 节点仍会参与校验并因缺必填输入而报错（如 MiniMaxH3LightX2VSLAAuditT8Advanced
    # 的 runtime/av_latent）。正确做法是整条删掉，而不是补默认值 ——
    # 补了值反而会把关闭的支线跑起来。
    dropped = drop_bypassed(wf)
    print(f"  删除已关闭(bypass)节点 {dropped} 个及其下游")

    apply_clip(wf, clip_dir, args.megapixels, args.frames, args.steps,
               ref_images=args.ref_images, args_spark=args.spark)

    # ---- 提交前自检：可达性 ----
    cons: dict[str, set] = {}
    for n in wf.values():
        for v in n["inputs"].values():
            if (isinstance(v, list) and len(v) == 2
                    and isinstance(v[0], (int, str)) and str(v[0]) in wf):
                cons.setdefault(str(v[0]), set()).add(n["class_type"])
    outs = [nid for nid in wf if nid not in cons]
    reach: set[str] = set()
    stack = list(outs)
    while stack:
        cur = stack.pop()
        if cur in reach:
            continue
        reach.add(cur)
        for v in wf[cur]["inputs"].values():
            if (isinstance(v, list) and len(v) == 2
                    and isinstance(v[0], (int, str)) and str(v[0]) in wf):
                stack.append(str(v[0]))
    dead = sorted(set(wf) - reach)
    print(f"  输出节点 {sorted(outs, key=int)}")
    print(f"  可达 {len(reach)}/{len(wf)}  不可达 {dead if dead else '0 个'}")

    if args.dry_run:
        Path("F:/h3tmp/meiling_submitted.json").write_text(
            json.dumps(wf, ensure_ascii=False, indent=1), encoding="utf-8")
        print("\n[dry-run] 图已存 F:/h3tmp/meiling_submitted.json，未提交")
        return

    # ---- 提交 ----
    cid = str(uuid.uuid4())
    try:
        r = api("POST", "/prompt", {"prompt": wf, "client_id": cid})
    except urllib.error.HTTPError as e:
        print("[提交失败]", e.read().decode()[:800])
        sys.exit(1)
    pid = r["prompt_id"]
    print(f"\nprompt_id = {pid}")

    t0 = time.time()
    while True:
        time.sleep(20)
        el = int(time.time() - t0)
        h = api("GET", f"/history/{pid}")
        if pid in h:
            st = h[pid]["status"]
            print(f"  耗时 {el}s  状态 {st.get('status_str')}")
            if st.get("status_str") == "error":
                for m in st.get("messages", []):
                    print("   ", str(m)[:300])
                sys.exit(1)
            for f in h[pid]["outputs"].values():
                for k in ("images", "gifs"):
                    for im in f.get(k, []):
                        print(f"   产出 {im.get('filename')}")
            break
        print(f"  耗时 {el}s  pending={len(api('GET','/queue').get('queue_running',[]))}")


if __name__ == "__main__":
    main()
