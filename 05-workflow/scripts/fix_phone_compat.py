# -*- coding: utf-8 -*-
"""把已生成的 EP04 片段统一重封装为手机可播版本（原地覆盖）。

背景：RunningHub 返回的 MOV 把 moov（解码索引）放在文件末尾、音轨为 32kHz AAC-LC，
桌面播放器正常，手机端可能整条静音。这里批量修正历史上已产出的所有片段。

用法：python fix_phone_compat.py [--dry]
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

EP = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep04")


def inspect(p: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_type,codec_name,sample_rate,channels",
         "-show_entries", "format=duration", "-of", "json", str(p)],
        capture_output=True, text=True,
    )
    import json
    return json.loads(out.stdout or "{}")


def normalize(p: Path, dry: bool = False) -> str:
    data = p.read_bytes()
    head = data[:65536]
    moov = head.find(b"moov")
    mdat = head.find(b"mdat")
    already = moov > 0 and mdat > 0 and moov < mdat
    meta = inspect(p)
    audio = [s for s in meta.get("streams", []) if s.get("codec_type") == "audio"]
    sr = audio[0].get("sample_rate") if audio else "无音轨"

    if already and str(sr) == "44100":
        return f"跳过（已合规 moov@={moov} 音轨={sr}Hz）"

    if dry:
        return f"[dry] 需修复：moov@={moov} mdat@={mdat} 音轨={sr}Hz"

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "o.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(p),
             "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
             "-ar", "44100", "-ac", "2", "-movflags", "+faststart", str(tmp)],
            check=True,
        )
        p.write_bytes(tmp.read_bytes())

    data = p.read_bytes()
    head = data[:65536]
    o = [head.find(b) for b in (b"ftyp", b"moov", b"mdat")]
    meta2 = inspect(p)
    a2 = [s for s in meta2.get("streams", []) if s.get("codec_type") == "audio"]
    sr2 = a2[0].get("sample_rate") if a2 else "无音轨"
    return f"已修复 moov@={o[1]} 音轨={sr2}Hz"


def main() -> int:
    dry = "--dry" in sys.argv
    targets = sorted(EP.glob("红绳片段*/视频草稿/*.mp4"))
    targets = [t for t in targets if "手机" not in t.stem]
    print(f"扫描到 {len(targets)} 个片段\n")
    for p in targets:
        try:
            print(f"{p.relative_to(EP)}\n    {normalize(p, dry)}")
        except Exception as e:
            print(f"{p.relative_to(EP)}\n    ❌ {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())