"""把 ASR 反推结果烧成字幕，供人工核对（可选）。同时输出逐段对照表。
"""
import json
import re
import subprocess
from pathlib import Path

W = Path("F:/h3tmp/r2t2_ep04")
SK = Path(r"C:\Users\Administrator\.workbuddy\skills\r2t2-video-subtitle\scripts")

# R2T2 明显识别错的地方（人名/专有词），用提示词原文修正
FIX = {
    "现在到底适适什么机构？": "你们到底是什么机构？",
    "你父亲不是得道之人，是不世之人。": "你父亲不是普通人，他做的事也不是普通事。",
    "而不是被台词带后。": "（此处串入创作说明，非台词）",
}

tr = json.loads((W / "transcript.json").read_text(encoding="utf-8"))
out = []
for s in tr["segments"]:
    t = s.get("text", "").strip()
    if not t:
        continue
    st = s["start_sample"] / 16000
    dur = (s["end_sample"] - s["start_sample"]) / 16000
    fixed = FIX.get(t, t)
    out.append({"start": round(st, 2), "duration": round(dur, 2),
                "asr": t, "corrected": fixed})

(W / "asr_corrected.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

# 输出逐句对照
print("=" * 74)
print("逐句对照：ASR 听到的  vs  提示词写的")
print("=" * 74)
for o in out:
    mark = "  " if o["asr"] == o["corrected"] else "✗ "
    print(f"{mark}[{o['start']:6.2f}s-{o['start']+o['duration']:5.2f}s] "
          f"{o['corrected']}")
    if o["asr"] != o["corrected"]:
        print(f"{'':18}ASR 原样: {o['asr']}")

# 生成 ASS
lines = ["[Script Info]",
         "ScriptType: v4.00+",
         "PlayResX: 1280", "PlayResY: 720",
         "", "[V4+ Styles]",
         "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
         "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
         "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
         "Alignment, MarginL, MarginR, MarginV, Encoding",
         "Style: S,Microsoft YaHei,34,&H00FFFFFF,&H000000FF,&H00202020,"
         "&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,60,60,44,1",
         "", "[Events]",
         "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]


def tc(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


for o in out:
    txt = o["corrected"].replace("\n", "\\N")
    lines.append(f"Dialogue: 0,{tc(o['start'])},{tc(o['start']+o['duration'])},"
                 f"S,,0,0,0,,{txt}")

(W / "asr_subtitles.ass").write_text("\n".join(lines), encoding="utf-8")
print(f"\n字幕已存 {W/'asr_subtitles.ass'}")
