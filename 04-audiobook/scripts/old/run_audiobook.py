"""红绳 第1章 - MOSS TTS 多角色有声书测试（9角色音色克隆）"""
import json, torch, soundfile as sf, os, glob
from transformers import AutoModel, AutoProcessor

torch.backends.cuda.enable_cudnn_sdp(False)
torch.backends.cuda.enable_flash_sdp(True)
torch.backends.cuda.enable_mem_efficient_sdp(True)
torch.backends.cuda.enable_math_sdp(True)

MODEL = r"F:/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/ComfyUI/models/moss_tts/MOSS-TTS-Local-Transformer-v1.5"
CODEC = r"F:/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/ComfyUI/models/moss_tts/MOSS-Audio-Tokenizer-v2"
REF_DIR = r"D:/编曲工程/ai视频/红绳有声书/参考音色"
OUT_DIR = r"D:/编曲工程/ai视频/红绳有声书"
device = "cuda"; dtype = torch.bfloat16
os.makedirs(OUT_DIR, exist_ok=True)

# Load models
print("Loading models...")
processor = AutoProcessor.from_pretrained(MODEL, trust_remote_code=True, codec_path=CODEC)
model = AutoModel.from_pretrained(
    MODEL, trust_remote_code=True, attn_implementation="sdpa", torch_dtype=dtype,
).to(device)
model.eval()
print(f"VRAM: {torch.cuda.memory_allocated()/1024**3:.1f}GB")

# Voice assignments
ref_files = {
    "旁白":   os.path.join(REF_DIR, "旁白.wav"),
    "林晓":   os.path.join(REF_DIR, "林晓.wav"),
    "梅林明": os.path.join(REF_DIR, "梅林明.wav"),
    "陈小雨": os.path.join(REF_DIR, "陈小雨.wav"),
    "王老师": os.path.join(REF_DIR, "王老师.wav"),
    "李老师": os.path.join(REF_DIR, "李老师.wav"),
    "赵小伟": os.path.join(REF_DIR, "赵小伟.wav"),
    "妈妈":   os.path.join(REF_DIR, "妈妈.wav"),
    "周芳":   os.path.join(REF_DIR, "周芳.wav"),
}

# Parse script
with open(r"D:/HermesWorkspace/ai小说/红绳/chapters/红绳_ch01_有声剧本.json", "r", encoding="utf-8") as f:
    script = json.load(f)

lines_raw = script["juben"].strip().split("\n")
script_lines = []
for line in lines_raw:
    if ":" not in line: continue
    colon = line.index(":")
    char_name = line[:colon].strip("（）").strip()
    text = line[colon+1:].strip()
    if text.startswith("（") and text.endswith("）"): continue
    if not text: continue
    script_lines.append((char_name, text))

print(f"Total script lines: {len(script_lines)}")
# Pick a few representative lines from key characters for the demo
demo_lines = []
for char_name, text in script_lines:
    if char_name in ("旁白", "林晓", "梅林明", "陈小雨", "王老师"):
        demo_lines.append((char_name, text))
    elif len(demo_lines) > 30:
        break

print(f"Demo lines: {len(demo_lines)}")

# Generate audio segments
audio_segments = []
sample_rate = processor.model_config.sampling_rate  # 48000

for i, (char_name, text) in enumerate(demo_lines):
    ref_path = ref_files.get(char_name, ref_files["旁白"])
    print(f"[{i+1}/{len(demo_lines)}] [{char_name}] {text}")
    
    conv = [processor.build_user_message(text=text, reference=[ref_path], language="Chinese")]
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
            audio = msg.audio_codes_list[0]  # [ch, samples]
            dur = audio.shape[1] / sample_rate
            print(f"  → {dur:.1f}s")
            audio_segments.append(audio.cpu())
            break
    
    # Save individual line
    line_audio = audio_segments[-1]
    line_out = os.path.join(OUT_DIR, f"lines/{i:03d}_{char_name}.wav")
    os.makedirs(os.path.dirname(line_out), exist_ok=True)
    sf.write(line_out, line_audio.T.numpy(), sample_rate)

# Concatenate all segments
print(f"\nConcatenating {len(audio_segments)} segments...")
all_audio = torch.cat(audio_segments, dim=1)
all_out = os.path.join(OUT_DIR, "红绳_ch01_有声书测试.wav")
sf.write(all_out, all_audio.T.numpy(), sample_rate)
dur = all_audio.shape[1] / sample_rate
print(f"✅ Complete audiobook: {all_out}")
print(f"   Total duration: {dur:.1f}s ({dur/60:.1f}min)")
print(f"   Lines: {len(audio_segments)}")
print(f"   VRAM: {torch.cuda.memory_allocated()/1024**3:.1f}GB")
