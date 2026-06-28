"""红绳 - MOSS TTS 多角色有声书测试（完整版9角色）"""
import os
os.add_dll_directory(r'E:/ffmpeg-master-latest-win64-gpl-shared/bin')

import torch, soundfile as sf
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

print("Loading...", flush=True)
proc = AutoProcessor.from_pretrained(MP, trust_remote_code=True, codec_path=MC)
proc.audio_tokenizer = proc.audio_tokenizer.to(device)  # move to GPU
model = AutoModel.from_pretrained(MP, trust_remote_code=True, attn_implementation="sdpa", torch_dtype=torch.bfloat16).to(device)
model.eval()
print(f"VRAM={torch.cuda.memory_allocated()/1024**3:.1f}GB", flush=True)

# Full script lines - first 30 lines covering all 9 characters
tests = [
    ("旁白","旁白.wav","新学期第一天，林晓起晚了。"),
    ("林晓","林晓.wav","来了来了！"),
    ("梅林明","梅林明.wav","谢谢。"),
    ("旁白","旁白.wav","妈妈把早饭塞进她书包。"),
    ("陈小雨","陈小雨.wav","你怎么又晚了？"),
    ("林晓","林晓.wav","闹钟没响。"),
    ("陈小雨","陈小雨.wav","不过王老师带了个新同学。"),
    ("旁白","旁白.wav","教室里响起稀稀拉拉的掌声。"),
    ("王老师","王老师.wav","这是梅林明同学，从隔壁市转学过来。"),
    ("赵小伟","赵小伟.wav","他好黑啊。"),
    ("王老师","王老师.wav","你就坐第三排靠窗吧。"),
    ("旁白","旁白.wav","林晓的心跳莫名其妙快了一拍。"),
    ("旁白","旁白.wav","他的脚步很轻。"),
    ("旁白","旁白.wav","他的头发剪得很短。"),
    ("林晓","林晓.wav","你叫什么？"),
    ("梅林明","梅林明.wav","林明。"),
    ("旁白","旁白.wav","她闻到了一股淡淡的肥皂味。"),
    ("妈妈","妈妈.wav","林晓！"),
    ("旁白","旁白.wav","林晓醒了，天已经亮了。"),
    ("旁白","旁白.wav","校园里那棵老榕树又长高了。"),
]

sr = proc.model_config.sampling_rate
all_a = []

for i,(c,f,t) in enumerate(tests):
    print(f"[{i+1}/{len(tests)}] {c}: {t}", flush=True)
    cv = [proc.build_user_message(text=t, reference=[f"{RF}/{f}"], language="Chinese")]
    b = proc([cv], mode="generation")
    with torch.no_grad():
        o = model.generate(b["input_ids"].to(device), b["attention_mask"].to(device),
            max_new_tokens=4096, do_sample=1, audio_temperature=1.7, audio_top_p=0.8, audio_top_k=25)
        for m in proc.decode(o):
            if m is None: continue
            a = m.audio_codes_list[0]; d = a.shape[1]/sr
            print(f"  {d:.1f}s", flush=True)
            all_a.append(a.cpu()); break
    sf.write(f"{OT}/lines/{i:03d}_{c}.wav", all_a[-1].T.numpy(), sr)

c = torch.cat(all_a, dim=1)
sf.write(f"{OT}/红绳_多角色测试.wav", c.T.numpy(), sr)
print(f"\n✅ DONE! {c.shape[1]/sr:.1f}s ({c.shape[1]/sr/60:.1f}min), {len(all_a)} segments", flush=True)
