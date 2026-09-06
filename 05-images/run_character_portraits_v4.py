#!/usr/bin/env python3
"""
《红绳》角色人设图生成脚本 v4
用 urllib（内置库）替代 requests
"""
import json, time, uuid, os, sys
from urllib.request import Request, urlopen
from urllib.parse import urlencode

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

def api_post(path, data=None):
    """POST JSON to ComfyUI"""
    url = f"{COMFY_HOST}{path}"
    body = json.dumps(data).encode('utf-8') if data else b''
    req = Request(url, data=body, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))

def api_get(path):
    """GET from ComfyUI"""
    with urlopen(f"{COMFY_HOST}{path}", timeout=30) as resp:
        return resp.read()

def build_prompt(positive_text, seed=-1):
    if seed < 0:
        seed = int(time.time() * 1000) % 2**32
    
    return {
        "55": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "krea2_turbo_mxfp8.safetensors",
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
        "80": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["55", 0],
                "lora_name": "realism_engine_krea2_v2.safetensors",
                "strength_model": 1.0
            }
        },
        "51": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["56", 0],
                "text": positive_text
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
                "width": 768,
                "height": 1024,
                "batch_size": 1
            }
        },
        "53": {
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
                "filename_prefix": "红绳_人设"
            }
        }
    }

def submit_and_wait(prompt_data, timeout=300):
    client_id = f"hermes_rs_{uuid.uuid4().hex[:6]}"
    payload = {"prompt": prompt_data, "client_id": client_id}
    
    try:
        result = api_post("/api/prompt", payload)
    except Exception as e:
        print(f"  提交失败: {e}")
        return None
    
    prompt_id = result['prompt_id']
    print(f"  prompt_id: {prompt_id}")
    
    start = time.time()
    last_status = ""
    while time.time() - start < timeout:
        try:
            r = urlopen(f"{COMFY_HOST}/api/history/{prompt_id}", timeout=10)
            history = json.loads(r.read().decode('utf-8'))
            if prompt_id in history:
                status = history[prompt_id].get('status', {})
                if status.get('completed'):
                    return history[prompt_id].get('outputs', {})
                # Show progress
                progress = status.get('progress', 0)
                if progress != last_status:
                    print(f"    进度: {progress}%")
                    last_status = progress
        except:
            pass
        time.sleep(2)
    
    print(f"  超时")
    return None

def download_image(img_data, save_path):
    params = urlencode({
        "filename": img_data['filename'],
        "subfolder": img_data.get('subfolder', ''),
        "type": "output"
    })
    try:
        data = api_get(f"/api/view?{params}")
        with open(save_path, 'wb') as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"  下载失败: {e}")
        return False

# ── 先试跑一张林晓 ──────────────────────────────────
print("=" * 60)
print("【验证阶段】先跑一张林晓测试全链路...")
print("=" * 60)
sys.stdout.flush()

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
            sys.stdout.flush()
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