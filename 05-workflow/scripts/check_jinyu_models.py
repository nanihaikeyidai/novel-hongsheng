"""核对金鱼工作流所需模型/LoRA 在本地的存在情况。"""
from pathlib import Path

COMFY = Path(r"F:\Work-Fisher纯净包2026.8.7\ComfyUI")

# 从工作流里提取到的全部模型需求
NEED = [
    ("主模型", "models/diffusion_models", "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors"),
    ("主模型(备)", "models/diffusion_models", "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors"),
    ("CLIP", "models/text_encoders", "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"),
    ("视频VAE(金鱼用int8)", "models/vae", "minimax_h3_video_vae_int8_convrot.safetensors"),
    ("视频VAE(本地用fp16)", "models/vae", "minimax_h3_video_vae_fp16.safetensors"),
    ("音频VAE", "models/vae", "minimax_h3_audio_vae_fp32.safetensors"),
    ("LoRA dmad4步", "models/loras", "minimax_h3_dmad_full_dareties_v4_step600_comfy_fro.safetensors"),
    ("LoRA 战斗V2", "models/loras", "H3_Combat_V2.safetensors"),
    ("LoRA 速度滑杆", "models/loras", "H3_speed_slider_1.1.safetensors"),
    ("LoRA 动作修复", "models/loras", "Motion_Repair_V2.safetensors"),
    ("LoRA 战斗流", "models/loras", "H3_Fight_Flow_V1.safetensors"),
    ("LoRA Mystic", "models/loras", "MysticXXX_MMH3-V1.safetensors"),
    ("超分模型(SelfLift)", "models/upscale_models", "minimax_h3_latent_upscaler_3d_fp16_V2.safetensors"),
    ("预览覆盖模型", "models/unet", "taeh3.safetensors"),
]

print("=" * 76)
print("模型/LoRA 需求核对")
print("=" * 76)
miss = []
for label, sub, fname in NEED:
    d = COMFY / sub
    direct = d / fname
    found = None
    if direct.exists():
        found = direct
    else:
        for alt in (COMFY / "models").rglob(fname):
            found = alt
            break
    if found:
        sz = found.stat().st_size / 1024**3
        print(f"  ✓ {label:24s} {fname}")
        print(f"      {found.relative_to(COMFY)}  ({sz:.2f} GB)")
    else:
        print(f"  ✗ {label:24s} {fname}")
        miss.append((label, fname))

print()
print("=" * 76)
print(f"缺失 {len(miss)} 个：")
for label, f in miss:
    print(f"  · {label}: {f}")

# 顺便列出本地所有 h3 相关 lora
print()
print("=" * 76)
print("本地已有 H3 相关 LoRA")
print("=" * 76)
for d in ("models/loras", "models/loras/h3"):
    p = COMFY / d
    if not p.exists():
        continue
    for f in sorted(p.rglob("*h3*")) + sorted(p.rglob("*H3*")):
        if f.suffix == ".safetensors":
            print(f"  {f.relative_to(COMFY)}  ({f.stat().st_size/1024**2:.0f} MB)")

print()
print("=" * 76)
print("分辨率对照表（工作流内嵌，RH 用 megapixels 参数）")
print("=" * 76)
TABLE = [
    (0.2, "608x352"), (0.3, "736x416"), (0.4, "864x480"), (0.5, "960x544"),
    (0.6, "1056x608"), (0.7, "1152x640"), (0.8, "1216x672"), (0.9, "1280x736"),
    (0.98, "1344x768"), (1.0, "1376x768"), (1.2, "1504x832"), (1.5, "1664x928"),
    (1.8, "1824x1024"), (2.0, "1920x1088"),
]
print("  16:9 各档位输出（均被32 整除）：")
for mp, res in TABLE:
    mark = " ← RH 端用的档" if abs(mp - 1.5) < 1e-6 else ""
    print(f"    {mp:5.2f} MP → {res}{mark}")
print()
print("  注：本项目 EP04 用 0.5MP = 960x544（RH 实际输出）")
