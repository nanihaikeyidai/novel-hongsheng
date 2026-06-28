"""生成剩余段落后合并"""
import os
os.add_dll_directory(r'E:/ffmpeg-master-latest-win64-gpl-shared/bin')

import torch, soundfile as sf, glob
from transformers import AutoModel, AutoProcessor

torch.backends.cuda.enable_cudnn_sdp(False)
torch.backends.cuda.enable_flash_sdp(True)
torch.backends.cuda.enable_mem_efficient_sdp(True)
torch.backends.cuda.enable_math_sdp(True)

MP = r"F:/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/ComfyUI/models/moss_tts/MOSS-TTS-Local-Transformer-v1.5"
MC = r"F:/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/ComfyUI/models/moss_tts/MOSS-Audio-Tokenizer-v2"
RF = r"D:/编曲工程/ai视频/红绳有声书/参考音色"
OT = r"D:/编曲工程/ai视频/红绳有声书"
device = "cuda"
os.makedirs(OT+"/lines", exist_ok=1)

# Continue from segment 9 (009 onwards)
remaining = [
    (9,"旁白","旁白.wav","他的头发剪得很短。"),
    (10,"林晓","林晓.wav","你叫什么？"),
    (11,"梅林明","梅林明.wav","林明。"),
    (12,"旁白","旁白.wav","她闻到了一股淡淡的肥皂味。"),
    (13,"妈妈","妈妈.wav","林晓！"),
    (14,"旁白","旁白.wav","林晓醒了，天已经亮了。"),
    (15,"旁白","旁白.wav","校园里那棵老榕树又长高了。"),
    (16,"王老师","王老师.wav","大家以后要互相帮助。"),
    (17,"旁白","旁白.wav","阳光洒在操场上，金灿灿的。"),
    (18,"赵小伟","赵小伟.wav","新同学好搞笑。"),
    (19,"旁白","旁白.wav","林晓低下头，嘴角忍不住上扬。"),
]

print("Loading...", flush=True)
proc = AutoProcessor.from_pretrained(MP, trust_remote_code=True, codec_path=MC)
proc.audio_tokenizer = proc.audio_tokenizer.to(device)
model = AutoModel.from_pretrained(MP, trust_remote_code=True, attn_implementation="sdpa", torch_dtype=torch.bfloat16).to(device)
model.eval()

sr = proc.model_config.sampling_rate
for i,c,f,t in remaining:
    print(f"[{i}] {c}: {t}", flush=True)
    cv = [proc.build_user_message(text=t, reference=[f"{RF}/{f}"], language="Chinese")]
    b = proc([cv], mode="generation")
    with torch.no_grad():
        o = model.generate(b["input_ids"].to(device), b["attention_mask"].to(device),
            max_new_tokens=4096, do_sample=1, audio_temperature=1.7, audio_top_p=0.8, audio_top_k=25)
        for m in proc.decode(o):
            if m is None: continue
            a = m.audio_codes_list[0]; d = a.shape[1]/sr
            print(f"  {d:.1f}s", flush=True)
            sf.write(f"{OT}/lines/{i:03d}_{c}.wav", a.T.cpu().numpy(), sr)
            break

# Merge all WAV files
print("\nMerging all segments...", flush=True)
files = sorted(glob.glob(f"{OT}/lines/[0-9][0-9][0-9]_*.wav"))
if not files:
    print("No WAV files found!")
    exit(1)

all_a = []
for f in files:
    d, sr = sf.read(f)
    all_a.append(torch.from_numpy(d.T if d.ndim > 1 else d[np.newaxis]))

merged = torch.cat(all_a, dim=1)
out = f"{OT}/红绳_多角色测试_完整.wav"
sf.write(out, merged.T.numpy(), sr)
print(f"\n✅ {out}")
print(f"   Segments: {len(files)}, Total: {merged.shape[1]/sr:.1f}s ({merged.shape[1]/sr/60:.1f}min)")
