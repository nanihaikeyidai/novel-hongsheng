#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地 ComfyUI MOSS 文生图（t2i）通用提交脚本。

用途：红绳项目所有「生图 / 参考视图」统一走本地 ComfyUI 的 MOSS 工作流
      （【WorkFisher】全能生图王 _ 适配所有类型.json 的精简 API 版）。

链路：UNETLoader(moss_image_sft) -> LoraLoaderModelOnly(KOOK-MOSS-SFT-观澜)
      -> SkipLayerGuidanceDiTSimple -> KSampler -> VAEDecode -> SaveImage
      CLIPLoader(qwen3.5_9b_int8_convrot, type=moss_image) + flux2-vae

用法示例：
  python gen_image_moss_local.py --prompt "..." --out "D:/.../view.png"
  python gen_image_moss_local.py --prompt-file prompt.txt --ratio "16:9 (Widescreen)" --mp 2.0 --seed 123 --steps 25
  python gen_image_moss_local.py --dry-run   # 只打印最终 prompt，不提交
"""
import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

HOST = "http://127.0.0.1:8188"
TEMPLATE = Path(r"D:/HermesWorkspace/ai小说/红绳/05-workflow/ep05/营救陆沉/_ripple_doc/moss_t2i_prompt_template.json")

# 访问本地服务必须绕过系统代理
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def build_prompt(args):
    p = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    # 模板里的 63 号节点是超长提示词文档（Note 用途），无任何节点引用，剔除以减小提交体
    p.pop("63", None)

    text = args.prompt_file.read_text(encoding="utf-8").strip() if args.prompt_file else args.prompt
    p["57"]["inputs"]["value"] = text
    p["36"]["inputs"]["text"] = args.negative
    p["19"]["inputs"]["aspect_ratio"] = args.ratio
    p["19"]["inputs"]["megapixels"] = args.mp
    p["31"]["inputs"]["seed"] = args.seed
    p["31"]["inputs"]["steps"] = args.steps
    p["31"]["inputs"]["cfg"] = args.cfg
    p["9"]["inputs"]["filename_prefix"] = args.prefix
    p["28"]["inputs"]["unet_name"] = args.unet
    p["41"]["inputs"]["strength_model"] = args.lora
    return p, text


def post_prompt(prompt):
    data = json.dumps({"prompt": prompt, "client_id": "moss-local-gen"}).encode("utf-8")
    req = urllib.request.Request(f"{HOST}/prompt", data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with OPENER.open(req, timeout=60) as r:
            return json.loads(r.read())["prompt_id"]
    except urllib.error.HTTPError as e:
        print("提交失败 HTTP", e.code, e.read().decode("utf-8", "replace")[:2000], flush=True)
        raise


def wait_result(pid, timeout=1800):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with OPENER.open(f"{HOST}/history/{pid}", timeout=30) as r:
                h = json.loads(r.read())
            if pid in h:
                item = h[pid]
                st = item.get("status", {})
                if st.get("completed") or st.get("status_str") == "success":
                    return item
                if st.get("status_str") == "error":
                    print("执行失败:", json.dumps(st, ensure_ascii=False)[:2000], flush=True)
                    return None
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(5)
    print("\n超时", flush=True)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", default="")
    ap.add_argument("--prompt-file", type=Path)
    ap.add_argument("--negative", default="插画，卡通，3D渲染，CG，塑料皮肤，变形的手，多余的手指，肢体错误，文字，标牌，水印，模糊，低分辨率，畸变，不自然比例")
    ap.add_argument("--ratio", default="16:9 (Widescreen)")
    ap.add_argument("--mp", type=float, default=2.0)
    ap.add_argument("--seed", type=int, default=20261105)
    ap.add_argument("--steps", type=int, default=25)
    ap.add_argument("--cfg", type=float, default=3.0)
    ap.add_argument("--prefix", default="moss_hongsheng")
    ap.add_argument("--unet", default="moss_image_sft_bf16.safetensors",
                    help="moss_image_sft_bf16.safetensors 或 moss_image_sft_int8_convrot.safetensors")
    ap.add_argument("--lora", type=float, default=1.0)
    ap.add_argument("--out", type=Path, required=True, help="成图保存路径（本地绝对路径）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    prompt, text = build_prompt(args)
    print(f"=== MOSS 本地生图 | {len(text)} 字 | {args.ratio} {args.mp}MP | {args.steps} 步 | {args.unet} ===", flush=True)
    if args.dry_run:
        print(json.dumps(prompt, ensure_ascii=False, indent=1)[:4000], flush=True)
        return

    pid = post_prompt(prompt)
    print("prompt_id =", pid, flush=True)
    item = wait_result(pid)
    if not item:
        sys.exit(1)
    imgs = item["outputs"]["9"]["images"]
    print("\n输出:", imgs, flush=True)
    info = imgs[0]
    url = f"{HOST}/view?filename={urllib.parse.quote(info['filename'])}&subfolder={urllib.parse.quote(info.get('subfolder',''))}&type={info.get('type','output')}"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with OPENER.open(url, timeout=300) as r, open(args.out, "wb") as f:
        f.write(r.read())
    print("saved", args.out, flush=True)


if __name__ == "__main__":
    import urllib.parse  # noqa: E402
    main()
