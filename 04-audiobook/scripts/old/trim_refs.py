"""裁剪参考音频到前15秒，并确保音频分词器在GPU"""
import os
os.add_dll_directory(r'E:/ffmpeg-master-latest-win64-gpl-shared/bin')

import soundfile as sf, librosa, numpy as np

REF = r"D:/编曲工程/ai视频/红绳有声书/参考音色"
MAX_SEC = 15  # 最多取前15秒

for f in os.listdir(REF):
    if not f.endswith(".wav"): continue
    path = os.path.join(REF, f)
    data, sr = sf.read(path)
    max_samples = int(MAX_SEC * sr)
    if len(data) > max_samples:
        data = data[:max_samples]
        sf.write(path, data, sr)
        dur = len(data) / sr
        print(f"Trimmed {f}: {dur:.1f}s")
    else:
        print(f"Kept {f}: {len(data)/sr:.1f}s")

print("Done trimming references!")
