"""红绳 - 多角色音色克隆测试（精简版3角色验证）"""
import sys, json, torch, soundfile as sf, os
from transformers import AutoModel, AutoProcessor

torch.backends.cuda.enable_cudnn_sdp(False)
torch.backends.cuda.enable_flash_sdp(True)
torch.backends.cuda.enable_mem_efficient_sdp(True)
torch.backends.cuda.enable_math_sdp(True)

MODEL = r"F:/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/ComfyUI/models/moss_tts/MOSS-TTS-Local-Transformer-v1.5"
CODEC = r"F:/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/ComfyUI/models/moss_tts/MOSS-Audio-Tokenizer-v2"
REF = r"D:/编曲工程/ai视频/红绳有声书/参考音色"
OUT = r"D:/编曲工程/ai视频/红绳有声书"
device = "cuda"; dtype = torch.bfloat16
os.makedirs(OUT, exist_ok=True)

print("Loading...", flush=True)
processor = AutoProcessor.from_pretrained(MODEL, trust_remote_code=True, codec_path=CODEC)
model = AutoModel.from_pretrained(
    MODEL, trust_remote_code=True, attn_implementation="sdpa", torch_dtype=dtype,
).to(device)
model.eval()
print(f"VRAM: {torch.cuda.memory_allocated()/1024**3:.1f}GB", flush=True)

# Test: 3 characters, first few lines from the script
tests = [
    ("旁白",   os.path.join(REF, "旁白.wav"),   "新学期第一天，林晓起晚了。"),
    ("林晓",   os.path.join(REF, "林晓.wav"),   "来了来了！"),
    ("梅林明", os.path.join(REF, "梅林明.wav"), "谢谢。"),
    ("旁白",   os.path.join(REF, "旁白.wav"),   "妈妈把早饭塞进她书包。"),
    ("陈小雨", os.path.join(REF, "陈小雨.wav"), "你怎么又晚了？"),
    ("林晓",   os.path.join(REF, "林晓.wav"),   "闹钟没响。"),
    ("旁白",   os.path.join(REF, "旁白.wav"),   "教室里响起稀稀拉拉的掌声。"),
    ("王老师", os.path.join(REF, "王老师.wav"), "这是梅林明同学，从隔壁市转学过来。"),
    ("旁白",   os.path.join(REF, "旁白.wav"),   "林晓的心跳莫名其妙快了一拍。"),
]

sr = processor.model_config.sampling_rate
all_audio = []

for i, (char, ref_path, text) in enumerate(tests):
    print(f"[{i+1}/{len(tests)}] {char}: {text}", flush=True)
    conv = [processor.build_user_message(text=text, reference=[ref_path], language="Chinese")]
    batch = processor([conv], mode="generation")
    ids = batch["input_ids"].to(device)
    mask = batch["attention_mask"].to(device)
    with torch.no_grad():
        out = model.generate(ids, mask, max_new_tokens=4096, do_sample=True,
            audio_temperature=1.7, audio_top_p=0.8, audio_top_k=25)
        for msg in processor.decode(out):
            if msg is None: continue
            audio = msg.audio_codes_list[0]
            dur = audio.shape[1] / sr
            print(f"  → {dur:.1f}s", flush=True)
            all_audio.append(audio.cpu())
            break
    # Save individual
    sf.write(os.path.join(OUT, f"lines/{i:03d}_{char}.wav"), all_audio[-1].T.numpy(), sr)

# Concatenate and save
combined = torch.cat(all_audio, dim=1)
out_path = os.path.join(OUT, "红绳_多角色测试.wav")
sf.write(out_path, combined.T.numpy(), sr)
total_dur = combined.shape[1] / sr
print(f"\n✅ Done! {out_path}")
print(f"   Duration: {total_dur:.1f}s, Segments: {len(all_audio)}")
