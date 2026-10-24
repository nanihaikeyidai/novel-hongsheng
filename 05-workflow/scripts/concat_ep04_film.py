# -*- coding: utf-8 -*-
"""EP04 审讯线成片拼接。

把多段 15s 片段拼成一条完整成片：
  - 时长对齐：每段统一拉伸/裁切到目标时长（默认 15s）
  - 音轨统一：48kHz → 44.1kHz stereo AAC-LC 160k
  - 手机兼容重封装：+faststart 把 moov 提到文件头
  - 可选段间黑场（默认 6 帧 ≈ 0.25s）与硬切两种方案

用法：
    python concat_ep04_film.py --segments 09c 10a 10b 10c --out EP04_审讯_1分钟_v2.mp4
    python concat_ep04_film.py --segments ... --fade   # 段间加 0.25s 黑场
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import run_ep04_interrogation_rh as R  # noqa: E402

SEG_DUR = 15.0          # 每段目标时长（秒）
FADE_FRAMES = 7         # 段间黑场帧数（25fps ≈ 0.28s）


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, check=True).stdout
    import json
    return json.loads(out)


def find_video(seg_id: str, suffix: str) -> Path:
    conf = R.SEGMENTS[seg_id]
    seg = R.ROOT / "05-workflow" / "ep04" / conf["dir"]
    out_dir = seg / "视频草稿"
    name = f"E04-{seg_id}_{conf['title']}{suffix}_未审核草稿.mp4"
    p = out_dir / name
    if p.exists():
        return p
    cands = sorted(out_dir.glob(f"E04-{seg_id}_*{suffix or '*'}_未审核草稿*.mp4"),
                   key=lambda x: x.stat().st_mtime, reverse=True)
    if cands:
        return cands[0]
    raise FileNotFoundError(f"片段 {seg_id} 没有可用成片：{out_dir}")


def build_filter(seg_id: str, fade: bool) -> str:
    """单段：归一化分辨率/帧率/采样率，并把时长对齐到 SEG_DUR。"""
    parts = [
        f"[0:v]scale=1280:720:force_original_aspect_ratio=decrease,"
        f"pad=1280:720:(ow-iw)/2:(oh-ih)/2:black,"
        f"fps=25,setsar=1,format=yuv420p[v{seg_id}]",
    ]
    # 时长不足则末帧冻结补齐，超出则裁切
    parts.append(
        f"[v{seg_id}]tpad=stop_mode=clone:stop_duration={SEG_DUR + 1},"
        f"trim=duration={SEG_DUR},setpts=PTS-STARTPTS[vo{seg_id}]"
    )
    if fade:
        parts.append(
            f"[vo{seg_id}]fade=t=in:st=0:d=0.12:color=black,"
            f"fade=t=out:st={SEG_DUR - 0.12}:d=0.12:color=black[vt{seg_id}]"
        )
    else:
        parts.append(f"[vo{seg_id}]null[vt{seg_id}]")
    parts.append(f"[0:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                 f"apad,atrim=duration={SEG_DUR},asetpts=PTS-STARTPTS[at{seg_id}]")
    return ";".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--segments", nargs="+", required=True, help="按播放顺序的片段 ID")
    ap.add_argument("--suffix", default="_v2", help="输入文件名后缀；传空串用无后缀版")
    ap.add_argument("--out", default=None, help="输出文件路径")
    ap.add_argument("--fade", action="store_true", help="段间加淡入淡出黑场")
    args = ap.parse_args()

    vids = [find_video(s, args.suffix) for s in args.segments]
    for s, v in zip(args.segments, vids):
        d = probe(v).get("format", {}).get("duration", "?")
        print(f"  {s}  {d}s  {v.name}")

    out = Path(args.out) if args.out else (
        R.ROOT / "05-workflow" / "ep04" / "成片" /
        f"EP04_审讯线_{len(args.segments)}段_{int(len(args.segments) * SEG_DUR)}秒_v2.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)

    chains, labels, apad_labels = [], [], []
    for i, seg in enumerate(args.segments):
        chains.append(build_filter(seg, args.fade))
        labels.append(f"[vt{seg}][at{seg}]")
        apad_labels.append(f"[vt{seg}][at{seg}]")

    # 每段末尾插 0.28s 黑场（fade 模式）或直接硬切
    n = len(args.segments)
    chain_in = ";".join(chains)
    concat_in = "".join(labels)
    if args.fade:
        graph = f"{chain_in};{concat_in}concat=n={n}:v=1:a=1[outv][outa]"
    else:
        graph = f"{chain_in};{concat_in}concat=n={n}:v=1:a=1[outv][outa]"

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "film.mp4"
        cmd = ["ffmpeg", "-y", "-v", "warning"]
        for v in vids:
            cmd += ["-i", str(v)]
        cmd += ["-filter_complex", graph, "-map", "[outv]", "-map", "[outa]",
                "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                "-pix_fmt", "yuv420p", "-r", "25",
                "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
                "-movflags", "+faststart", str(tmp)]
        subprocess.run(cmd, check=True)

        info = probe(tmp)
        dur = float(info["format"]["duration"])
        vs = next(s for s in info["streams"] if s["codec_type"] == "video")
        as_ = next(s for s in info["streams"] if s["codec_type"] == "audio")
        head = tmp.read_bytes()[:65536]
        order = [head.find(b) for b in (b"ftyp", b"moov", b"mdat")]
        ok = order[1] > 0 and order[1] < order[2]
        print(f"\n成片时长 {dur:.2f}s  视频 {vs['width']}x{vs['height']}@{vs.get('r_frame_rate')}  "
              f"音频 {as_['sample_rate']}Hz {as_.get('channels')}ch")
        print(f"moov 前置 {'✓' if ok else '✗'}  order={order}")
        out.write_bytes(tmp.read_bytes())

    print(f"\n✅ 已输出 {out}  ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
