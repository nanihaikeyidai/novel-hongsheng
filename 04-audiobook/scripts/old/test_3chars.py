"""红绳 第1章 - 多角色有声书测试（精简版先验证3角色）"""
import json, torch, soundfile as sf, os
from transformers import AutoModel, AutoProcessor

torch.backends.cuda.enable_cudnn_sdp(False)
torch.backends.cuda.enable_flash_sdp(True)
torch.backends.cuda.enable_mem_efficient_sdp(True)
torch.backends.cuda.enable_math_sdp(True)

MODEL = r"F:/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/ComfyUI/models/moss_tts/MOSS-TTS-Local-Transformer-v1.5"
CODEC = r"F:/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/ComfyUI/models/moss_tts/MOSS-Audio-Tokenizer-v2"
ASSETS = r"D:/HermesWorkspace/MOSS-TTS/assets/audio"
OUT = r"D:/编曲工程/ai视频/红绳有声书"
device = "cuda"; dtype = torch.bfloat16
os.makedirs(OUT, exist_ok=True)

# Load processor & model
print("Loading...")
processor = AutoProcessor.from_pretrained(MODEL, trust_remote_code=True, codec_path=CODEC)
model = AutoModel.from_pretrained(
    MODEL, trust_remote_code=True, attn_implementation="sdpa", torch_dtype=dtype,
).to(device)
model.eval()

# Test 3 characters with different reference audios
test_cases = [
    ("旁白", ASSETS + "/reference_zh.wav",  "新学期第一天，林晓起晚了。"),
    ("林晓", ASSETS + "/reference_zh_0.wav", "来了来了！"),
    ("梅林明", ASSETS + "/reference_02_s1.wav", "谢谢。"),
    ("陈小雨", ASSETS + "/reference_zh_2.wav", "你怎么又晚了？"),
]

for char_name, ref_path, text in test_cases:
    print(f"\n[{char_name}] {text}")
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
            audio = msg.audio_codes_list[0]
            out = os.path.join(OUT, f"{char_name}.wav")
            sf.write(out, audio.T.cpu().numpy(), processor.model_config.sampling_rate)
            dur = audio.shape[1] / processor.model_config.sampling_rate
            print(f"  ✅ {dur:.1f}s -> {out}")

print(f"\n✅ Done! Check {OUT}")
