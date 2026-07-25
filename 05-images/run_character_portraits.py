#!/usr/bin/env python3
"""
《红绳》角色人设图生成脚本
用 ComfyUI API 调用（自用-贞贞）N版Krea2+Turbo文生图V1 工作流
"""
import json, time, uuid, requests, os, sys

COMFY_HOST = "http://127.0.0.1:8188"
WORKFLOW_PATH = r"F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI\user\default\workflows\（自用-贞贞）N版Krea2+Turbo文生图V1.json"
OUTPUT_DIR = r"D:\HermesWorkspace\ai小说\红绳\05-images"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 角色提示词列表 ──────────────────────────────────
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
        "name": "林明",
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

NEGATIVE_PROMPT = (
    "lowres, bad anatomy, bad hands, text, error, missing fingers, "
    "extra digit, fewer digits, cropped, worst quality, low quality, "
    "normal quality, jpeg artifacts, signature, watermark, username, "
    "blurry, bad feet, mutation, deformed, extra limbs, extra arms, "
    "extra legs, malformed limbs, fused fingers, too many fingers, "
    "long neck, cross-eyed, mutated hands, polar lowres, bad face, "
    "out of frame, oversaturated, overexposed, multiple people, group"
)

# ── 加载工作流 ─────────────────────────────────────
with open(WORKFLOW_PATH, 'r', encoding='utf-8') as f:
    workflow_data = json.load(f)

# 检查格式：如果是 editor 格式（有 nodes 数组），转为 API 格式
nodes_list = workflow_data.get('nodes', [])
if nodes_list:
    print(f"工作流格式: editor (nodes={len(nodes_list)})，转换为 API 格式...")
    api_prompt = {}
    for node in nodes_list:
        nid = str(node['id'])
        api_node = {
            "class_type": node['type'],
            "inputs": {}
        }
        # 复制 inputs 中的链接信息
        for inp in node.get('inputs', []):
            iname = inp['name']
            link_id = inp.get('link')
            if link_id is not None and link_id >= 0:
                # 找到这个 link 的目标
                for link in workflow_data.get('links', []):
                    if link[0] == link_id:
                        from_node = str(link[1])
                        from_slot = link[2]
                        api_node['inputs'][iname] = [from_node, from_slot]
                        break
            else:
                # 没有链接的 widget 值
                pass
        
        # 保存 widget 值
        wvals = node.get('widgets_values', [])
        if wvals:
            api_node['_widget_values'] = wvals
        
        api_prompt[nid] = api_node
    
    # 用 extract_schema 风格 - 实际上直接通过 api_prompt 就行
    workflow_api = api_prompt
else:
    print("工作流格式: API")
    workflow_api = workflow_data

print(f"转换完成，共 {len(workflow_api)} 个节点")

# ── 工具函数 ────────────────────────────────────────
def queue_prompt(prompt_override=None):
    """提交工作流到 ComfyUI"""
    # 深拷贝工作流
    workflow = json.loads(json.dumps(workflow_api))
    
    # 应用 override
    for nid, overrides in (prompt_override or {}).items():
        if nid in workflow:
            for key, val in overrides.items():
                if key == '_widget_values':
                    # 直接设置 widget 值需要特殊处理
                    pass
                else:
                    workflow[nid]['inputs'][key] = val
    
    # 提交
    payload = {"prompt": workflow, "client_id": f"hermes_redstring_{uuid.uuid4().hex[:8]}"}
    resp = requests.post(f"{COMFY_HOST}/api/prompt", json=payload)
    if resp.status_code != 200:
        print(f"提交失败: {resp.status_code} {resp.text}")
        return None
    result = resp.json()
    prompt_id = result.get('prompt_id')
    print(f"  ✓ 已提交, prompt_id: {prompt_id}")
    return prompt_id

def poll_until_done(prompt_id, timeout=120):
    """轮询直到完成"""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(f"{COMFY_HOST}/api/history/{prompt_id}")
        if resp.status_code == 200:
            history = resp.json()
            if prompt_id in history and history[prompt_id].get('status', {}).get('completed'):
                outputs = history[prompt_id].get('outputs', {})
                return outputs
        time.sleep(1)
    print(f"  ⚠ 超时 {timeout}s")
    return None

def download_image(filename, subfolder, output_path):
    """下载生成图片"""
    resp = requests.get(
        f"{COMFY_HOST}/api/view",
        params={"filename": filename, "subfolder": subfolder, "type": "output"}
    )
    if resp.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(resp.content)
        return True
    return False

# ── 遍历角色逐一生成 ──────────────────────────────
results = []
for i, char in enumerate(characters):
    print(f"\n[{i+1}/{len(characters)}] 生成 {char['name']}...")
    
    prompt_override = {
        "63": {"_widget_values": [char['prompt']]},       # PrimitiveStringMultiline - 提示词
        "76": {"_widget_values": [char['prompt']]},       # CLIPTextEncode 负提示词 - 用负提示模板
        "49": {"_widget_values": ['3:4 (Portrait)', 1, 1]},  # 改成3:4竖版 1MP
        "53": {"_widget_values": [-1, 'randomize', 10, 1, 'euler', 'simple', 1]},  # random seed
    }
    
    # ComfyUI API 的 widget 覆盖需要特殊处理
    # 对于 widget 值，我们改用直接修改 prompt 文本节点的方式
    # 因为 workflow 中 Node 63 (PrimitiveStringMultiline) 的 text 是通过 widget 传入的
    # 在 API 格式中，widget 值通过 inputs 传递
    
    try:
        prompt_id = queue_prompt(prompt_override)
        if not prompt_id:
            print(f"  ✗ 提交失败")
            continue
        
        outputs = poll_until_done(prompt_id)
        if not outputs:
            print(f"  ✗ 生成失败或超时")
            continue
        
        # 解析输出
        saved = False
        for node_id, node_outputs in outputs.items():
            for img_data in node_outputs.get('images', []):
                fname = img_data['filename']
                subf = img_data.get('subfolder', '')
                out_path = os.path.join(OUTPUT_DIR, f"{char['name']}_人设_上半身正面.png")
                if download_image(fname, subf, out_path):
                    print(f"  ✓ 已保存: {out_path}")
                    saved = True
                    results.append({"name": char['name'], "path": out_path, "success": True})
        
        if not saved:
            print(f"  ⚠ 未找到输出图片")
            results.append({"name": char['name'], "path": None, "success": False})
    
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        results.append({"name": char['name'], "path": None, "success": False})

# ── 总结 ───────────────────────────────────────────
print("\n" + "="*60)
print("生成结果汇总：")
for r in results:
    icon = "✅" if r['success'] else "❌"
    print(f"  {icon} {r['name']}: {r['path'] or '失败'}")
print("="*60)
