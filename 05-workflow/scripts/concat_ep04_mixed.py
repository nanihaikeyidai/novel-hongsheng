"""拼接混版成片：09c(v4) + 10a(v5) + 10b(v5) + 10c(v5 或 v6)。

concat_ep04_film.py 只支持统一后缀，这里按片段分别指定版本文件名。
"""
import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep04")
FF = "ffmpeg"


def probe(dur: float) -> None:
    r = subprocess.run(
        [FF, "-v", "error", "-y",
         "-f", "lavfi", "-t", f"{dur:.6f}", "-i", f"color=c=black:s=1280x720:r=25",
         "-f", "lavfi", "-t", f"{dur:.6f}", "-i", "anullsrc=r=44100:cl=stereo",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
         "-shortest", "-video_track_timescale", "25000",
         r"F:\h3tmp\black_gap.mp4"],
        capture_output=True, text=True,
    )
    if r.returncode:
        raise SystemExit("间隔片生成失败：" + r.stderr[-500:])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", nargs="+", required=True,
                    help="每项格式 片段ID:版本后缀，如 09c:_v4 10a:_v5")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    files = []
    for s in args.spec:
        sid, suf = s.split(":", 1)
        folder = next(ROOT.glob(f"红绳片段{sid}_*"))
        cand = sorted((folder / "视频草稿").glob(f"E04-{sid}_*{suf}_未审核草稿.mp4"))
        if not cand:
            raise SystemExit(f"[{sid}] 找不到后缀 {suf} 的成片")
        src = cand[-1]
        asc = Path("F:/h3tmp") / f"cc_{sid}.mp4"
        asc.write_bytes(src.read_bytes())
        files.append((sid, asc))
        print(f"  {sid}  {src.name}")

    gap = Path("F:/h3tmp/black_gap.mp4")
    probe(0.25)

    norm = []
    for sid, p in files:
        out = Path("F:/h3tmp") / f"norm_{sid}.mp4"
        subprocess.run(
            [FF, "-v", "error", "-y", "-i", str(p),
             "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,"
                    "pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=25,format=yuv420p",
             "-af", "aresample=44100",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18",
             "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
             "-video_track_timescale", "25000", str(out)],
            check=True, capture_output=True)
        norm.append((sid, out))

    # 段间插黑场
    inputs = []
    for _, p in norm:
        inputs += ["-i", str(p)]
    inputs += ["-i", str(gap)]
    gi = len(norm)
    filt = []
    labels = []
    for i, (sid, _) in enumerate(norm):
        # 视频流 i、音频流 i 一一对应（前面每段只传了视频+音频两个流）
        filt.append(f"[{i}:v]setpts=PTS-STARTPTS[v{i}];"
                    f"[{i}:a]aresample=44100,asetpts=PTS-STARTPTS[a{i}]")
        labels.append(f"[v{i}][a{i}]")
        if i < len(norm) - 1:
            filt.append(f"[{gi}:v]setpts=PTS-STARTPTS[vg{i}];"
                        f"[{gi}:a]asetpts=PTS-STARTPTS[ag{i}]")
            labels.append(f"[vg{i}][ag{i}]")
    fc = ";".join(filt) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=1:a=1[vo][ao]"
    subprocess.run(
        [FF, "-v", "error", "-y", *inputs,
         "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
         "-movflags", "+faststart", "-video_track_timescale", "25000",
         args.out],
        check=True, capture_output=True)
    print("输出 ->", args.out)


if __name__ == "__main__":
    main()
