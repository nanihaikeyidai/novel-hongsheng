"""红绳 第1章 - MOSS TTS 多角色有声书测试"""
import json, torch, soundfile as sf
import os, glob
from transformers import AutoModel, AutoProcessor

torch.backends.cuda.enable_cudnn_sdp(False)
torch.backends.cuda.enable_flash_sdp(True)
torch.backends.cuda.enable_mem_efficient_sdp(True)
torch.backends.cuda.enable_math_sdp(True)

MODEL = r"F:/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/ComfyUI/models/moss_tts/MOSS-TTS-Local-Transformer-v1.5"
CODEC = r"F:/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/ComfyUI/models/moss_tts/MOSS-Audio-Tokenizer-v2"
ASSETS = r"D:/HermesWorkspace/MOSS-TTS/assets/audio"
device = "cuda"; dtype = torch.bfloat16

# Load script
with open(r"D:/HermesWorkspace/ai小说/红绳/chapters/红绳_ch01_有声剧本.json", "r", encoding="utf-8") as f:
    script = json.load(f)

role_list = {r["name"]: r for r in script["role_list"]}

# Assign reference audio to each character
# Using available assets - different audios for different voice types
ref_assign = {
    "旁白":   ASSETS + "/reference_zh.wav",      # 成年女性，沉稳
    "林晓":   ASSETS + "/reference_zh_0.wav",     # 年轻女性
    "梅林明": ASSETS + "/reference_02_s1.wav",     # 低沉声音（16kHz）
    "陈小雨": ASSETS + "/reference_zh_2.wav",      # 年轻女性活泼
    "王老师": ASSETS + "/reference_zh.wav",        # 成年女性
    "李老师": ASSETS + "/reference_02_s2.wav",     # 可能的男声
    "赵小伟": ASSETS + "/reference_02_s1.wav",     # 男童声
    "妈妈":   ASSETS + "/reference_zh_1.wav",      # 成年女性温柔
    "周芳":   ASSETS + "/reference_zh_0.wav",      # 年轻女性
}

# Parse juben into lines
lines_raw = script["juben"].strip().split("\n")
lines = []
for line in lines_raw:
    if ":" not in line:
        continue
    colon = line.index(":")
    char_name = line[:colon].strip("（").strip("）").strip()
    text = line[colon+1:].strip()
    # Skip non-dialogue content
    if text.startswith("（") and text.endswith("）"):
        continue
    if not text:
        continue
    lines.append((char_name, text))

print(f"Total lines: {len(lines)}")
print(f"Characters: {set(c for c,_ in lines)}")

# Load models
print("\nLoading processor...")
processor = AutoProcessor.from_pretrained(MODEL, trust_remote_code=True, codec_path=CODEC)
print("Loading model...")
model = AutoModel.from_pretrained(
    MODEL, trust_remote_code=True, attn_implementation="sdpa", torch_dtype=dtype,
).to(device)
model.eval()
print(f"Model loaded, VRAM: {torch.cuda.memory_allocated()/1024**3:.1f}GB")

# Generate! Process first 3 characters' lines for demo
char_samples = {}
for char_name, text in lines[:30]:  # first 30 lines
    if char_name not in char_samples:
        char_samples[char_name] = []
    char_samples[char_name].append(text)

# Generate one sample per character
output_dir = r"D:/编曲工程/ai视频/红绳有声书"
os.makedirs(output_dir, exist_ok=True)

print("Generating voice samples...")
for char_name, texts in char_samples.items():
    ref_path = ref_assign.get(char_name, ASSETS + "/reference_zh.wav")
    sample_text = texts[0]  # use first line
    desc = role_list.get(char_name, {}).get("instruct", char_name)
    
    print(f"\n[{char_name}] {desc}")
    print(f"  Text: {sample_text}")
    
    # Build conversation with reference
    conv = [processor.build_user_message(
        text=sample_text,
        reference=[ref_path],
        language="Chinese"
    )]
    batch = processor([conv], mode="generation")
    input_ids = batch["input_ids"].to(device)
    attention_mask = batch["attention_mask"].to(device)
    
    with torch.no_grad():
        outputs = model.generate(
            input_ids=input_ids, attention_mask=attention_mask,
            max_new_tokens=4096, do_sample=True,
            audio_temperature=1.7, audio_top_p=0.8, audio_top_k=25,
        )
        for msg in processor.decode(outputs):
            if msg is None: continue
            audio = msg.audio_codes_list[0]
            out = os.path.join(output_dir, f"{char_name}.wav")
            sr = processor.model_config.sampling_rate
            sf.write(out, audio.T.cpu().numpy(), sr)
            dur = audio.shape[1] / sr
            print(f"  ✅ Generated: {dur:.1f}s -> {out}")

print(f"\nAll done! Files in: {output_dir}")
