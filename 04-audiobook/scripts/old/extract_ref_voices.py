"""从800+音色合集中提取角色匹配的参考音频"""
import zipfile, os, soundfile as sf, librosa

OUT = r"D:/编曲工程/ai视频/红绳有声书/参考音色"
os.makedirs(OUT, exist_ok=True)

assignments = [
    ("旁白",   "不同年龄人群音色.zip", "不同年龄人群音色/热门音色/中音磁性女声旁白.wav"),
    ("林晓",   "不同年龄人群音色.zip", "不同年龄人群音色/孩童/女-10-12岁孩.wav"),
    ("梅林明", "不同年龄人群音色.zip", "不同年龄人群音色/孩童/男-十二到十四岁的男孩.wav"),
    ("陈小雨", "不同年龄人群音色.zip", "不同年龄人群音色/孩童/女-可爱、甜美、活泼.wav"),
    ("王老师", "克隆参考音色.zip",     "克隆参考音色/常用配音/云静芳.WAV"),
    ("李老师", "不同年龄人群音色.zip", "不同年龄人群音色/中年-男声/男-和蔼、温暖、中年.wav"),
    ("赵小伟", "不同年龄人群音色.zip", "不同年龄人群音色/孩童/小龄男书童试听.wav"),
    ("妈妈",   "不同年龄人群音色.zip", "不同年龄人群音色/热门音色/叶子温柔师姐-中文.wav"),
    ("周芳",   "不同年龄人群音色.zip", "不同年龄人群音色/孩童/女-温暖、内敛.wav"),
]

ZIP_DIR = r"D:/HermesWorkspace/800+音色合集"

for char_name, zip_name, zip_path in assignments:
    zip_file = os.path.join(ZIP_DIR, zip_name)
    try:
        with zipfile.ZipFile(zip_file, 'r') as zf:
            info = zf.getinfo(zip_path)
            data = zf.read(zip_path)
            temp = os.path.join(OUT, f"_temp_{char_name}{os.path.splitext(zip_path)[1]}")
            with open(temp, 'wb') as f:
                f.write(data)
            
            # Convert to 48kHz mono WAV (best for MOSS TTS cloning)
            y, sr = sf.read(temp)
            if len(y.shape) > 1:
                y = y.mean(axis=1)  # mono
            if sr != 48000:
                y = librosa.resample(y, orig_sr=sr, target_sr=48000)
            
            out_path = os.path.join(OUT, f"{char_name}.wav")
            sf.write(out_path, y, 48000)
            os.remove(temp)
            print(f"✅ {char_name:5s} → {out_path} ({len(y)/48000:.1f}s, {sr}→48kHz)")
    except Exception as e:
        print(f"❌ {char_name:5s} → {e}")

print(f"\n✅ All done! Check {OUT}")
os.system(f"ls -la \"{OUT}\"")
