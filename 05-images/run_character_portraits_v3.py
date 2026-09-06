#!/usr/bin/env python3
"""
《红绳》角色人设图生成脚本 v3
用 ComfyUI API 直接构造请求（修正版）
"""
import json, time, uuid, requests, os

COMFY_HOST = "http://127.0.0.1:8188"
OUTPUT_DIR = r"D:\HermesWorkspace\ai小说\红绳\05-images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

NEGATIVE = (
    "lowres, bad anatomy, bad hands, text, error, missing fingers, "
    "extra digit, fewer digits, cropped, worst quality, low quality, "
    "normal quality, jpeg artifacts, signature, watermark, username, "
    "blurry, bad feet, mutation, deformed, extra limbs, extra arms, "
    "extra legs, malformed limbs, fused fingers, too many fingers, "
    "long neck, cross-eyed, mutated hands, polar lowres, bad face, "
    "out of frame, oversaturated, overexposed, multiple people, group"
)

characters = [
    {
        "name": "林晓",
        "prompt": (
            "A high school girl's upper body portrait, front-facing, looking at the camera with a gentle but reserved expression. "
            "Long black hair tied in a high ponytail, straight bangs across the forehead, big bright eyes with long eyelashes, "
            "fair porcelain skin. Wearing a white Chinese school uniform shirt, a faded red string bracelet tied tightly around her right wrist. "
            "Pure white background, soft natural lighting, anime illustration style, semi-realistic painting, delicate facial features, "
            "elegant and pure atmosphere, soft pastel tones, 8k quality, upper body framing, centered composition."
        )
    },
    {
        "name": "陆沉",
        "prompt": (
            "A high school boy's upper body portrait, front-facing, looking at the camera with a slightly distant and introverted expression. "
            "Tanned wheat-colored skin, thick expressive eyebrows, big deep eyes with notably long eyelashes, straight nose bridge, lean face shape. "
            "Short black neat hair. Wearing a simple white Chinese school uniform shirt, no accessories. "
            "Pure white background, soft diffused lighting, anime illustration style, semi-realistic, delicate rendering, "
            "quiet and melancholic atmosphere, gentle masculinity, 8k quality, upper body framing, centered composition."
        )
    },
    {
        "name": "陈小雨",
        "prompt": (
            "A cheerful teenage girl's upper body portrait, front-facing, smiling brightly at the camera with lively eyes. "
            "Short shoulder-length black hair with a cute hair clip on one side, round face with curved smiling eyes, slightly rosy cheeks. "
            "Wearing a Chinese school uniform. Pure white background, warm bright lighting, anime illustration style, semi-realistic, "
            "vibrant and energetic atmosphere, friendly expression, 8k quality, upper body framing, centered composition."
        )
    },
    {
        "name": "赵小伟",
        "prompt": (
            "A teenage boy's upper body portrait, front-facing, smirking playfully at the camera with mischievous eyes. "
            "Short messy hair, regular handsome features, slightly athletic build visible through the unzipped school jacket. "
            "Casual confident posture. Pure white background, bright daylight lighting, anime illustration style, semi-realistic, "
            "energetic and slightly rebellious atmosphere, friendly grin, 8k quality, upper body framing, centered composition."
        )
    },
    {
        "name": "苏晴",
        "prompt": (
            "A confident teenage girl's upper body portrait, front-facing, gazing calmly at the camera with a composed and slightly proud expression. "
            "Long black hair naturally falling over shoulders, oval face with strikingly beautiful features, almond-shaped eyes with a hint of confidence. "
            "Wearing a neatly pressed Chinese school uniform with an elegant hair accessory. "
            "Pure white background, soft cool-toned lighting, anime illustration style, semi-realistic, "
            "refined and elegant atmosphere, cool beauty aura, 8k quality, upper body framing, centered composition."
        )
    }
]

def build_prompt(positive_text, seed=-1):
    """构造 API 格式的工作流 prompt"""
    if seed < 0:
        seed = int(time.time() * 1000) % 2**32
    
    return {
        "55": {  # UNETLoader
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "krea2_turbo_mxfp8.safetensors",
                "weight_dtype": "default"
            }
        },
        "56": {  # CLIPLoader
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "qwen3vl_4b_fp8_scaled.safetensors",
                "type": "krea2"
            }
        },
        "57": {  # VAELoader
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "qwen_image_vae.safetensors"
            }
        },
        "80": {  # LoraLoaderModelOnly
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["55", 0],
                "lora_name": "realism_engine_krea2_v2.safetensors",
                "strength_model": 1.0
            }
        },
        "51": {  # CLIPTextEncode - positive prompt
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["56", 0],
                "text": positive_text
            }
        },
        "76": {  # CLIPTextEncode - negative prompt
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["56", 0],
                "text": NEGATIVE
            }
        },
        "77": {  # ConditioningZeroOut - for negative conditioning
            "class_type": "ConditioningZeroOut",
            "inputs": {
                "conditioning": ["51", 0]
            }
        },
        "52": {  # EmptyLatentImage - 3:4 portrait
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 768,
                "height": 1024,
                "batch_size": 1
            }
        },
        "53": {  # KSampler
            "class_type": "KSampler",
            "inputs": {
                "model": ["80", 0],
                "positive": ["51", 0],
                "negative": ["77", 0],
                "latent_image": ["52", 0],
                "seed": seed,
                "steps": 10,
                "cfg": 1,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0
            }
        },
        "54": {  # VAEDecode
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["53", 0],
                "vae": ["57", 0]
            }
        },
        "29": {  # SaveImage
            "class_type": "SaveImage",
            "inputs": {
                "images": ["54", 0],
                "filename_prefix": "红绳_人设"
            }
        }
    }

def submit_and_wait(prompt_data, timeout=180):
    """提交并等待完成"""
    client_id = f"hermes_rs_{uuid.uuid4().hex[:6]}"
    payload = {"prompt": prompt_data, "client_id": client_id}
    
    resp = requests.post(f"{COMFY_HOST}/api/prompt", json=payload)
    if resp.status_code != 200:
        print(f"  提交失败: {resp.status_code} {resp.text[:300]}")
        return None
    
    prompt_id = resp.json()['prompt_id']
    print(f"  prompt_id: {prompt_id}")
    
    # 轮询
    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(f"{COMFY_HOST}/api/history/{prompt_id}")
        if r.status_code == 200:
            history = r.json()
            if prompt_id in history and history[prompt_id].get('status', {}).get('completed'):
                return history[prompt_id].get('outputs', {})
        time.sleep(1)
    
    # 超时后检查最后一次状态
    r = requests.get(f"{COMFY_HOST}/api/history/{prompt_id}")
    if r.status_code == 200:
        history = r.json()
        if prompt_id in history:
            print(f"  状态: {json.dumps(history[prompt_id].get('status', {}), indent=2)[:200]}")
    
    print(f"  超时!")
    return None

def download_image(img_data, save_path):
    fname = img_data['filename']
    subf = img_data.get('subfolder', '')
    r = requests.get(f"{COMFY_HOST}/api/view", params={"filename": fname, "subfolder": subf, "type": "output"})
    if r.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(r.content)
        return True
    print(f"  下载失败: {r.status_code}")
    return False

# ── 先试跑一张林晓 ──────────────────────────────────
print("=" * 60)
print("【验证阶段】先跑一张林晓测试全链路...")
print("=" * 60)

prompt = build_prompt(characters[0]["prompt"])
outputs = submit_and_wait(prompt, timeout=300)

if outputs:
    saved = False
    for node_id, node_out in outputs.items():
        for img in node_out.get('images', []):
            out_path = os.path.join(OUTPUT_DIR, f"林晓_人设_上半身正面.png")
            if download_image(img, out_path):
                print(f"  ✅ 验证成功！已保存: {out_path}")
                saved = True
    
    if saved:
        print("\n✅ 验证通过！开始批量生成全部角色...\n")
        
        results = [{"name": "林晓", "success": True}]
        
        for i, char in enumerate(characters[1:], 2):
            print(f"[{i}/{len(characters)}] {char['name']}...")
            prompt = build_prompt(char["prompt"], seed=-1)
            outputs = submit_and_wait(prompt, timeout=300)
            
            ok = False
            if outputs:
                for node_id, node_out in outputs.items():
                    for img in node_out.get('images', []):
                        out_path = os.path.join(OUTPUT_DIR, f"{char['name']}_人设_上半身正面.png")
                        if download_image(img, out_path):
                            print(f"  ✅ 已保存: {out_path}")
                            ok = True
            results.append({"name": char['name'], "success": ok})
            if not ok:
                print(f"  ❌ 生成失败")
        
        # 汇总
        print("\n" + "=" * 60)
        print("【生成汇总】")
        for r in results:
            icon = "✅" if r['success'] else "❌"
            path = os.path.join(OUTPUT_DIR, f"{r['name']}_人设_上半身正面.png")
            print(f"  {icon} {r['name']}: {path}")
        print("=" * 60)
    else:
        print("  ⚠ 验证图保存失败")
else:
    print("  ❌ 验证生成失败，检查 ComfyUI 和模型")
    
    # 检查 ComfyUI available
    try:
        r = requests.get(f"{COMFY_HOST}/api/object_info", timeout=5)
        print(f"  ComfyUI 连接: OK")
        # Check model availability
        unet_list = r.json()['UNETLoader']['input']['required']['unet_name'][0]
        if 'krea2_turbo_mxfp8.safetensors' in unet_list:
            print(f"  模型存在 ✓")
        else:
            print(f"  模型不在列表中! 可用Krea模型: {[m for m in unet_list if 'krea' in m.lower()]}")
    except Exception as e:
        print(f"  ComfyUI 连接失败: {e}")
