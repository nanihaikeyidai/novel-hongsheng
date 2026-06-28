#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《红绳》第01章 Index-TTS 2.0 多角色有声书生成脚本

依赖：
  - Index-TTS 2.0 模型路径：F:/ComfyUI_V6.0/Index-tts-2.0-Windows-NVIDIA
  - 参考音色：D:/HermesWorkspace/ai小说/红绳/04-audiobook/参考音色
  - 剧本 JSON：红绳_第01章_有声小说.json

用法：
  cd "chinese-novelist/20260625-红绳/有声小说"
  "F:/ComfyUI_V6.0/Index-tts-2.0-Windows-NVIDIA/env/python.exe" generate_audiobook_index_tts.py
"""

import os
import sys
import json
import time
import warnings

warnings.filterwarnings("ignore")

# ==================== 配置 ====================
INDEX_TTS_DIR = r"F:/ComfyUI_V6.0/Index-tts-2.0-Windows-NVIDIA"
MODEL_DIR = os.path.join(INDEX_TTS_DIR, "checkpoints")
REF_DIR = r"D:/HermesWorkspace/ai小说/红绳/04-audiobook/参考音色"
SCRIPT_JSON = r"红绳_第01章_有声小说.json"
OUTPUT_DIR = r"index_tts_output"

# 角色到参考音色的映射
REF_VOICES = {
    "旁白":   os.path.join(REF_DIR, "旁白.wav"),
    "林明":   os.path.join(REF_DIR, "青年林明.wav"),
    "林晓":   os.path.join(REF_DIR, "青年林晓.wav"),
    "王老师": os.path.join(REF_DIR, "王老师.wav"),
    "李想":   os.path.join(REF_DIR, "赵小伟.wav"),  # 年轻男性音色，适配李想
}

# 情绪标签 -> Index-TTS 情感描述文本（use_emo_text）
EMOTION_MAP = {
    "neutral":   "自然平静的语气",
    "happy":     "高兴愉悦的语气",
    "sad":       "悲伤低落的语气",
    "angry":     "愤怒激动的语气",
    "fear":      "恐惧紧张的语气",
    "surprise":  "惊讶意外的语气",
    "excited":   "兴奋激动的语气",
    "calm":      "沉稳冷静的语气",
    "worried":   "担忧焦虑的语气",
    "cold":      "冷漠淡然的语气",
    "gentle":    "温柔柔和的语气",
    "fierce":    "凶狠严厉的语气",
    "mocking":   "嘲讽戏谑的语气",
    "desperate": "绝望无助的语气",
    "hopeful":   "充满希望的语气",
    "mysterious":"神秘低语的语气",
}

# 生成参数（参考 API.py 默认值）
GENERATION_KWARGS = {
    "do_sample": True,
    "top_p": 0.85,
    "top_k": 30,
    "temperature": 0.75,
    "length_penalty": 1.0,
    "num_beams": 1,
    "repetition_penalty": 1.0,
    "max_mel_tokens": 600,
}

# 测试模式：只生成前 N 行，用于验证模型可用性
TEST_MODE = False
TEST_LINE_COUNT = 5

# ==================== 加载 Index-TTS ====================
print("=" * 60)
print("《红绳》第01章 - Index-TTS 2.0 有声书生成")
print("=" * 60)

sys.path.insert(0, INDEX_TTS_DIR)
sys.path.insert(0, os.path.join(INDEX_TTS_DIR, "indextts"))

import torch
import soundfile as sf
import numpy as np

# 加载模型
print("\n[1/4] 正在加载 Index-TTS 2.0 模型...")
print(f"      Model dir: {MODEL_DIR}")

from indextts.infer_v2 import IndexTTS2

tts = IndexTTS2(
    model_dir=MODEL_DIR,
    cfg_path=os.path.join(MODEL_DIR, "config.yaml"),
    use_fp16=True,  # 根据显卡调整
)

print("[1/4] 模型加载完成")

# ==================== 读取剧本 ====================
print("\n[2/4] 读取有声小说剧本...")
with open(SCRIPT_JSON, "r", encoding="utf-8") as f:
    script = json.load(f)

chapter = script["chapters"][0]
lines = chapter["lines"]
if TEST_MODE:
    lines = lines[:TEST_LINE_COUNT]
    print(f"[2/4] 测试模式：共 {len(lines)} 行（原剧本 {len(chapter['lines'])} 行）")
else:
    print(f"[2/4] 共 {len(lines)} 行（旁白+对话）")

# 检查参考音频
print("\n[3/4] 检查参考音色文件...")
missing = []
for char, path in REF_VOICES.items():
    if not os.path.exists(path):
        missing.append((char, path))
        print(f"      [MISS] 缺失: {char} -> {path}")
    else:
        print(f"      [OK] {char} -> {os.path.basename(path)}")
if missing:
    raise FileNotFoundError(f"缺少 {len(missing)} 个参考音色文件")

# ==================== 生成音频 ====================
print("\n[4/4] 开始逐行生成音频...")
os.makedirs(OUTPUT_DIR, exist_ok=True)
seg_dir = os.path.join(OUTPUT_DIR, "segments")
os.makedirs(seg_dir, exist_ok=True)

# 断点续传：收集已生成的片段
existing_segments = set()
for fname in os.listdir(seg_dir):
    if fname.endswith(".wav") and fname[0:4].isdigit():
        existing_segments.add(int(fname[0:4]))

if existing_segments:
    print(f"      发现 {len(existing_segments)} 个已生成片段，将跳过")

audio_segments = []
sample_rate = None
skipped = []

for i, line in enumerate(lines):
    line_type = line["type"]
    content = line["content"].strip()
    emotion = line.get("emotion", "neutral")

    if not content:
        continue

    if line_type == "narration":
        char = "旁白"
    else:
        char = line.get("character", "旁白")

    ref_path = REF_VOICES.get(char, REF_VOICES["旁白"])
    emo_text = EMOTION_MAP.get(emotion, "自然平静的语气")

    seg_name = f"{i:04d}_{char}_{emotion}.wav"
    seg_path = os.path.join(seg_dir, seg_name)

    print(f"\n[{i+1}/{len(lines)}] {char} ({emotion}) | {content[:40]}{'...' if len(content) > 40 else ''}")

    # 断点续传：如果已存在则跳过生成，直接读取
    if i in existing_segments and os.path.exists(seg_path):
        print(f"      [SKIP] 已存在: {seg_name}")
        try:
            wav, sr = sf.read(seg_path)
            if wav.ndim > 1:
                wav = wav.mean(axis=1)
            if sample_rate is None:
                sample_rate = sr
            elif sr != sample_rate:
                import librosa
                wav = librosa.resample(wav.astype(float), orig_sr=sr, target_sr=sample_rate)
            audio_segments.append((seg_name, wav.astype(np.float32)))
            continue
        except Exception as e:
            print(f"      [WARN] 读取已存在片段失败，将重新生成: {e}")

    try:
        output_path = tts.infer(
            spk_audio_prompt=ref_path,
            text=content,
            output_path=seg_path,
            use_emo_text=True,
            emo_text=emo_text,
            verbose=False,
            max_text_tokens_per_segment=120,
            **GENERATION_KWARGS
        )

        # 读取生成音频
        wav, sr = sf.read(output_path)
        if wav.ndim > 1:
            wav = wav.mean(axis=1)
        if sample_rate is None:
            sample_rate = sr
        elif sr != sample_rate:
            # 简单重采样（如果采样率不一致）
            import librosa
            wav = librosa.resample(wav.astype(float), orig_sr=sr, target_sr=sample_rate)

        dur = len(wav) / sample_rate
        print(f"      -> {dur:.2f}s 已保存: {seg_name}")
        audio_segments.append((seg_name, wav))

    except Exception as e:
        print(f"      [WARN] 生成失败: {e}")
        skipped.append((i, char, content, str(e)))
        continue

# ==================== 合并音频 ====================
print("\n" + "=" * 60)
print("合并音频片段...")

if not audio_segments:
    raise RuntimeError("没有生成任何音频片段")

# 在片段之间添加短暂停顿（0.3秒静音）
silence = np.zeros(int(sample_rate * 0.3), dtype=np.float32)
all_audio = []
for idx, (name, wav) in enumerate(audio_segments):
    all_audio.append(wav.astype(np.float32))
    if idx < len(audio_segments) - 1:
        all_audio.append(silence)

combined = np.concatenate(all_audio)
final_path = os.path.join(OUTPUT_DIR, "红绳_第01章_有声书.wav")
sf.write(final_path, combined, sample_rate)

total_dur = len(combined) / sample_rate
print(f"[OK] 完成！")
print(f"   总时长: {total_dur:.1f}s ({total_dur/60:.1f} min)")
print(f"   成功行数: {len(audio_segments)}/{len(lines)}")
print(f"   输出文件: {final_path}")
print(f"   片段目录: {os.path.join(OUTPUT_DIR, 'segments')}")

if skipped:
    print(f"\n[WARN] 跳过了 {len(skipped)} 行:")
    for i, char, content, err in skipped[:10]:
        print(f"   [{i}] {char}: {content[:30]}... ({err[:50]})")

# 保存生成日志
log_path = os.path.join(OUTPUT_DIR, "generation_log.json")
with open(log_path, "w", encoding="utf-8") as f:
    json.dump({
        "script": SCRIPT_JSON,
        "total_lines": len(lines),
        "success": len(audio_segments),
        "skipped": len(skipped),
        "duration_seconds": total_dur,
        "ref_voices": REF_VOICES,
        "segments": [name for name, _ in audio_segments]
    }, f, ensure_ascii=False, indent=2)

print(f"   日志文件: {log_path}")
