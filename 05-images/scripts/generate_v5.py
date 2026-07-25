#!/usr/bin/env python3
"""
《红绳》第一章 六角色 Krea2 四格人设图生成脚本 v5
基于小说原文提取的角色特征，四格分屏格式 (1920×1024)

用法：
  # 单角色
  python 05-images/scripts/generate_v5.py --character 林晓
  
  # 全部角色
  python 05-images/scripts/generate_v5.py --all
  
  # 指定 Day
  python 05-images/scripts/generate_v5.py --day 1

依赖：requests（或 urllib）
ComfyUI API @ http://127.0.0.1:8188
"""

import json, time, uuid, os, sys, argparse
from urllib.request import Request, urlopen
from urllib.parse import urlencode

COMFY_HOST = "http://127.0.0.1:8188"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "05-images")

NEGATIVE = (
    "lowres, bad anatomy, bad hands, text, error, missing fingers, "
    "extra digit, fewer digits, cropped, worst quality, low quality, "
    "normal quality, jpeg artifacts, signature, watermark, username, "
    "blurry, bad feet, mutation, deformed, extra limbs, extra arms, "
    "extra legs, malformed limbs, fused fingers, too many fingers, "
    "long neck, cross-eyed, mutated hands, polar lowres, bad face, "
    "out of frame, oversaturated, overexposed, multiple people, group"
)

# ── 四格提示词框架 ──────────────────────────────────
FOUR_GRID_PREFIX = (
    "人物概念设计图的并排四格分屏构图，四个格子从左到右均匀排列，每个格子独立且完整:\n"
    "第一格为人物头部到胸口的精致半身特写，面部居中比例协调不溢出；\n"
    "第二格为人物正面全身站姿从头到脚完整显示；\n"
    "第三格为人物侧面全身站姿从头到脚完整显示；\n"
    "第四格为人物背面全身站姿从头到脚完整显示，脚踩地面。\n\n"
)

# ── 角色数据（基于小说原文） ──────────────────────────
CHARACTERS = [
    {
        "name": "林晓",
        "seed": 909746541,
        "day": 1,
        "prompt": FOUR_GRID_PREFIX + (
            "A teenage girl with long black hair tied in a high ponytail, "
            "straight neat bangs across the forehead, large bright eyes with notably long eyelashes, "
            "fair porcelain skin, small and delicate features, "
            "a calm and reserved expression with a hint of gentleness. "
            "Wearing a white Chinese high school uniform shirt with a navy blue pleated skirt, "
            "white socks and black loafers. "
            "A faded dark red string bracelet tied tightly around her right wrist, "
            "an old small wooden bead hanging beside the knot. "
            "In her right hand she holds a small eraser printed with a cartoon cat, edges worn smooth. "
            "Her left hand holds a black umbrella with a thin red string wrapped around its handle, "
            "matching the color of the bracelet. "
            "A pink candy wrapper peeks out of her skirt pocket. "
            "Pure white background with soft studio lighting, "
            "clean and minimal composition, anime illustration style, "
            "high detail, delicate rendering, elegant and pure atmosphere."
        )
    },
    {
        "name": "林明",
        "seed": 909746542,
        "day": 2,
        "prompt": FOUR_GRID_PREFIX + (
            "A teenage boy with tanned wheat-colored skin, "
            "thick dark eyebrows, big deep eyes with notably long eyelashes, "
            "straight nose bridge, lean face shape, short neat black hair. "
            "A distant, introverted expression, looking slightly downward, "
            "shoulders slightly hunched as if trying not to be noticed. "
            "Wearing a simple white Chinese high school uniform shirt with dark trousers, "
            "plain black shoes. No accessories or jewelry at all. "
            "A faint old scar visible at his left shoulder, partially hidden by the collar. "
            "Lean build, standing with hands in pockets. "
            "Pure white background with soft diffused lighting, "
            "clean and minimal composition, anime illustration style, "
            "high detail, quiet and melancholic atmosphere, gentle masculinity."
        )
    },
    {
        "name": "王老师",
        "seed": 909746543,
        "day": 3,
        "prompt": FOUR_GRID_PREFIX + (
            "A middle-aged female teacher, 40-50 years old, "
            "short neat permed hair, round glasses, "
            "warm but authoritative expression, slight smile. "
            "Wearing a professional dark-colored blazer over a light blouse, "
            "dark straight-cut trousers, low-heeled shoes. "
            "Holding a piece of white chalk in her right hand, "
            "an old-fashioned teacher's posture. "
            "Pure white background with soft office lighting, "
            "clean and minimal composition, anime illustration style, "
            "high detail, approachable but professional educator atmosphere."
        )
    },
    {
        "name": "李想",
        "seed": 909746544,
        "day": 3,
        "prompt": FOUR_GRID_PREFIX + (
            "A teenage boy, 17-18 years old, "
            "short slightly messy hair, regular handsome features, "
            "lively mischievous eyes with a playful grin on his face, "
            "tan skin, slightly athletic build. "
            "Wearing the same Chinese high school uniform but with the shirt "
            "partially untucked, sleeves rolled up casually. "
            "Standing with a relaxed, confident posture, one hand on his hip, "
            "the other raised as if telling a story. "
            "Pure white background with bright daylight lighting, "
            "clean and minimal composition, anime illustration style, "
            "high detail, energetic and cheerful atmosphere, sunny and outgoing."
        )
    },
    {
        "name": "妈妈",
        "seed": 909746545,
        "day": 4,
        "prompt": FOUR_GRID_PREFIX + (
            "A middle-aged woman, 40-50 years old, "
            "weary and tired expression, dark circles under eyes, "
            "shoulder-length black hair with some grey strands, "
            "plain simple features, no makeup. "
            "Wearing a plain dark-colored work apron over a simple blouse and trousers, "
            "slightly rumpled from a long day, a faint kitchen oil smell implied. "
            "Holding a small sticky note in her hand. "
            "Posture slightly stooped from exhaustion. "
            "Pure white background with soft warm lighting, "
            "clean and minimal composition, anime illustration style, "
            "high detail, tired but caring motherly atmosphere, warm and hardworking."
        )
    },
    {
        "name": "陈老师",
        "seed": 909746546,
        "day": 4,
        "prompt": FOUR_GRID_PREFIX + (
            "A middle-aged male math teacher, 40-55 years old, "
            "thinning grey-black hair combed simply, "
            "narrow glasses, sharp intelligent eyes, "
            "focused and slightly impatient expression, "
            "mouth slightly open as if speaking rapidly. "
            "Wearing a plain button-up shirt with a tie slightly loosened, "
            "dark trousers, formal leather shoes. "
            "Holding a piece of white chalk and a math textbook. "
            "Lean build, standing with energetic teaching posture. "
            "Pure white background with bright classroom lighting, "
            "clean and minimal composition, anime illustration style, "
            "high detail, sharp and quick-talking educator atmosphere."
        )
    }
]

CHARACTER_MAP = {c["name"]: c for c in CHARACTERS}


def build_workflow(character, extra_loras=True):
    """构造 ComfyUI API 工作流"""
    c = character
    model_node = "55"
    current_model = model_node
    
    nodes = {
        model_node: {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "krea2_turbo_nvfp4.safetensors",
                "weight_dtype": "default"
            }
        },
        "56": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "qwen3vl_4b_fp8_scaled.safetensors",
                "type": "krea2"
            }
        },
        "57": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "qwen_image_vae.safetensors"
            }
        },
        "51": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["56", 0],
                "text": c["prompt"]
            }
        },
        "76": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["56", 0],
                "text": NEGATIVE
            }
        },
        "77": {
            "class_type": "ConditioningZeroOut",
            "inputs": {
                "conditioning": ["51", 0]
            }
        },
        "52": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 1920,
                "height": 1024,
                "batch_size": 1
            }
        },
        "53": {
            "class_type": "KSampler",
            "inputs": {
                "model": [current_model, 0],
                "positive": ["51", 0],
                "negative": ["77", 0],
                "latent_image": ["52", 0],
                "seed": c["seed"],
                "steps": 8,
                "cfg": 1.0,
                "sampler_name": "er_sde",
                "scheduler": "simple",
                "denoise": 1.0
            }
        },
        "54": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["53", 0],
                "vae": ["57", 0]
            }
        },
        "29": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["54", 0],
                "filename_prefix": f"红绳_{c['name']}_四格人设"
            }
        }
    }
    
    # Add 3 LoRAs
    if extra_loras:
        loras = [
            ("krea2-Cc风情万种-风格.safetensors", 1.0),
            ("krea2-Cc-天魔-身材.safetensors", 1.0),
            ("krea2-Cc风情万种-人像.safetensors", 1.0),
        ]
        prev = model_node
        for i, (lora_name, strength) in enumerate(loras):
            node_id = f"80" if i == 0 else (f"81" if i == 1 else "82")
            nodes[node_id] = {
                "class_type": "LoraLoaderModelOnly",
                "inputs": {
                    "model": [prev, 0],
                    "lora_name": lora_name,
                    "strength_model": strength
                }
            }
            prev = node_id
        
        # Update KSampler to use last LoRA output
        nodes["53"]["inputs"]["model"] = [prev, 0]
    
    return nodes


def submit_and_wait(workflow, timeout=180):
    """提交工作流并等待完成"""
    client_id = f"hermes_rs_{uuid.uuid4().hex[:6]}"
    payload = {"prompt": workflow, "client_id": client_id}
    
    data = json.dumps(payload).encode("utf-8")
    req = Request(f"{COMFY_HOST}/api/prompt", data=data,
                  headers={"Content-Type": "application/json"})
    
    try:
        resp = urlopen(req, timeout=30)
        result = json.loads(resp.read())
    except Exception as e:
        print(f"  提交失败: {e}")
        return None
    
    prompt_id = result["prompt_id"]
    print(f"  提交成功, prompt_id: {prompt_id}")
    
    # 轮询
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = urlopen(f"{COMFY_HOST}/api/history/{prompt_id}", timeout=10)
            history = json.loads(r.read())
            if prompt_id in history and history[prompt_id].get("status", {}).get("completed"):
                return history[prompt_id].get("outputs", {})
        except Exception:
            pass
        time.sleep(1)
    
    print(f"  超时! (>{timeout}s)")
    return None


def download_image(img_data, save_path):
    """下载生成的图片"""
    fname = img_data["filename"]
    subf = img_data.get("subfolder", "")
    params = urlencode({"filename": fname, "subfolder": subf, "type": "output"})
    url = f"{COMFY_HOST}/api/view?{params}"
    
    try:
        r = urlopen(url, timeout=30)
        with open(save_path, "wb") as f:
            f.write(r.read())
        return True
    except Exception as e:
        print(f"  下载失败: {e}")
        return False


def generate_character(character):
    """生成单个角色的四格人设图"""
    name = character["name"]
    seed = character["seed"]
    print(f"\n{'='*60}")
    print(f"【生成】{name} (seed={seed})")
    print(f"{'='*60}")
    
    workflow = build_workflow(character)
    outputs = submit_and_wait(workflow, timeout=300)
    
    if not outputs:
        print(f"  ❌ {name} 生成失败")
        return False
    
    # 找到输出图像
    char_dir = os.path.join(OUTPUT_DIR, name)
    os.makedirs(char_dir, exist_ok=True)
    save_path = os.path.join(char_dir, f"{name}_四格人设_v1.png")
    
    saved = False
    for node_id, node_out in outputs.items():
        for img in node_out.get("images", []):
            if download_image(img, save_path):
                print(f"  ✅ 已保存: {save_path}")
                saved = True
    
    if saved:
        # 也保存到根目录作为备份
        backup_path = os.path.join(OUTPUT_DIR, f"{name}_四格人设_v1.png")
        if save_path != backup_path:
            import shutil
            shutil.copy2(save_path, backup_path)
            print(f"  ✅ 备份: {backup_path}")
        return True
    else:
        print(f"  ❌ 保存失败")
        return False


def check_comfyui():
    """检查 ComfyUI 是否正在运行"""
    try:
        r = urlopen(f"{COMFY_HOST}/api/object_info", timeout=5)
        info = json.loads(r.read())
        # 检查模型可用性
        unet_list = info.get("UNETLoader", {}).get("input", {}).get("required", {}).get("unet_name", [[], {}])[0]
        krea_models = [m for m in unet_list if "krea" in m.lower()]
        print(f"  ComfyUI ✅  (可用 Krea 模型: {len(krea_models)} 个)")
        for m in krea_models[:5]:
            print(f"    - {m}")
        return True
    except Exception as e:
        print(f"  ComfyUI ❌  连接失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="红绳 六角色 Krea2 四格人设图生成")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="生成全部 6 个角色")
    group.add_argument("--character", type=str, help="角色名: 林晓/林明/王老师/李想/妈妈/陈老师")
    group.add_argument("--day", type=int, choices=[1,2,3,4], help="Day 编号: 1=林晓, 2=林明, 3=王老师+李想, 4=妈妈+陈老师")
    args = parser.parse_args()
    
    print("=" * 60)
    print("《红绳》Krea2 四格人设图生成器 v5")
    print("=" * 60)
    
    # 检查 ComfyUI
    print("\n📡 检查 ComfyUI 状态...")
    if not check_comfyui():
        print("\n❌ ComfyUI 未运行！请先启动 ComfyUI:")
        print("   cd /path/to/ComfyUI")
        print("   python main.py")
        sys.exit(1)
    
    # 确定要生成的角色
    targets = []
    if args.character:
        if args.character not in CHARACTER_MAP:
            print(f"❌ 未知角色: {args.character}，可选: {list(CHARACTER_MAP.keys())}")
            sys.exit(1)
        targets = [CHARACTER_MAP[args.character]]
    elif args.day:
        targets = [c for c in CHARACTERS if c["day"] == args.day]
    else:  # --all
        targets = CHARACTERS
    
    print(f"\n🎯 目标: {len(targets)} 个角色")
    for c in targets:
        print(f"   - {c['name']} (Day {c['day']}, seed={c['seed']})")
    
    # 逐角色生成
    results = []
    for c in targets:
        ok = generate_character(c)
        results.append({"name": c["name"], "success": ok})
    
    # 汇总
    print(f"\n{'='*60}")
    print("【生成汇总】")
    for r in results:
        icon = "✅" if r["success"] else "❌"
        path = os.path.join(OUTPUT_DIR, r["name"], f"{r['name']}_四格人设_v1.png")
        print(f"  {icon} {r['name']}: {path}")
    print(f"{'='*60}")
    
    all_ok = all(r["success"] for r in results)
    if all_ok:
        print("\n✨ 全部生成成功！可以用 git 提交了。")
    else:
        print(f"\n⚠ 有 {sum(1 for r in results if not r['success'])} 个角色生成失败")


if __name__ == "__main__":
    main()
