# -*- coding: utf-8 -*-
"""EP04 审讯线 RunningHub 金鱼工作流统一提交脚本。

支持片段：
  07 — 审问室空镜（纯空镜，无对白）
  08 — 破冰·老韩进门与第一句台词（一句话对白）

共同参数：YZ金鱼-MiniMax H3 终极篇-文武双全
AI应用 2093984226331938818 · 15秒 · 0.5MP · 二采倍率1 · 16:9
场景图统一使用日漫版 `场景_ND审问室_日漫v3.png`
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

RUNNINGHUB_SCRIPTS = Path(r"C:\Users\Administrator\.codex\skills\runninghub\scripts")
sys.path.insert(0, str(RUNNINGHUB_SCRIPTS))

from runninghub import download_file, fix_mov_to_mp4, poll_task, require_api_key  # noqa: E402
from runninghub_app import apply_modifications, get_node_info, submit_task  # noqa: E402

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
APP_ID = "2093984226331938818"
SCENE = ROOT / "05-images" / "场景" / "场景_ND审问室_日漫v3.png"
LUCHEN = ROOT / "05-workflow" / "ep04" / "归档素材" / "人物" / "陆沉_人设.png"
LAOHAN = ROOT / "05-workflow" / "ep04" / "归档素材" / "人物" / "审讯员老韩_人设_单人.png"
LUDINGTIAN_PHOTO = ROOT / "05-images" / "人物" / "陆定天_军装照_日漫.png"
CHENPHOTO = ROOT / "05-images" / "人物" / "陈玥_照片_日漫.png"
OBSERVATORY = ROOT / "05-images" / "场景" / "场景_ND观察廊_夜_日漫.png"

# 槽位节点沿用 ep03 已跑通映射；第4槽 43 用于道具（陆定天军装照 / 陈玥照片）
SLOT_NODES = ("51", "49", "50", "43")

# 金鱼工作流的 3 个音频槽位节点（实测线上节点表）
AUDIO_SLOT_NODES = ("48", "14", "15")
VOICE_DIR = ROOT / "人物参考音色"

SEGMENTS = {
    "07": {
        "dir": "红绳片段07_审问室空镜",
        "title": "审问室空镜",
        "refs": [LUCHEN, SCENE],
        "audios": [],            # 纯空镜，无人声
    },
    "08": {
        "dir": "红绳片段08_破镜",
        "title": "破冰",
        "refs": [LUCHEN, LAOHAN, SCENE],
        # <Audio 1> = 老韩专属音色（IndexTTS2.5 克隆生成，F0 中位 105Hz，
        # 对应五十多岁中年男性）。节点48 只提供音色，台词取自提示词。
        "audios": [VOICE_DIR / "老韩.wav"],
    },
    # ---- 场 9｜父亲的名字（4 段）----
    # <Audio 1> = 老韩.wav；<Audio 2> = 陆沉.wav，仅在两人都有台词的片段（09d）绑定。
    "09a": {
        "dir": "红绳片段09a_父亲的铺垫",
        "title": "父亲的铺垫",
        "refs": [LUCHEN, LAOHAN, SCENE],
        "audios": [VOICE_DIR / "老韩.wav"],
    },
    "09b": {
        "dir": "红绳片段09b_松动的防线",
        "title": "松动的防线",
        "refs": [LUCHEN, LAOHAN, SCENE],
        "audios": [VOICE_DIR / "老韩.wav"],
    },
    "09c": {
        "dir": "红绳片段09c_陆定天的名字",
        "title": "陆定天的名字",
        "refs": [LUCHEN, LAOHAN, SCENE],
        "audios": [VOICE_DIR / "老韩.wav"],
    },
    "09d": {
        "dir": "红绳片段09d_六岁",
        "title": "六岁",
        "refs": [LUCHEN, LAOHAN, SCENE],
        # 陆沉首次开口 + 老韩画外追问，两条音色都要绑
        "audios": [VOICE_DIR / "老韩.wav", VOICE_DIR / "陆沉.wav"],
    },
    # ---- 场 10｜陆沉的反问（3 段）----
    # 桌面新增陆定天军装照（对应剧本场9 末尾老韩把照片放上桌），占第 4 参考图槽。
    "10a": {
        "dir": "红绳片段10a_看照片的人",
        "title": "看照片的人",
        "refs": [LUCHEN, LAOHAN, SCENE, LUDINGTIAN_PHOTO],
        "audios": [VOICE_DIR / "老韩.wav", VOICE_DIR / "陆沉.wav"],
    },
    "10b": {
        "dir": "红绳片段10b_到底是什么机构",
        "title": "到底是什么机构",
        "refs": [LUCHEN, LAOHAN, SCENE, LUDINGTIAN_PHOTO],
        "audios": [VOICE_DIR / "老韩.wav", VOICE_DIR / "陆沉.wav"],
    },
    "10c": {
        "dir": "红绳片段10c_笑容僵住",
        "title": "笑容僵住",
        "refs": [LUCHEN, LAOHAN, SCENE, LUDINGTIAN_PHOTO],
        "audios": [VOICE_DIR / "老韩.wav", VOICE_DIR / "陆沉.wav"],
    },
    # ---- 场 11｜能力试探（4 段）----
    "11a": {
        "dir": "红绳片段11a_换题",
        "title": "换题",
        "refs": [LUCHEN, LAOHAN, SCENE, LUDINGTIAN_PHOTO],
        "audios": [VOICE_DIR / "老韩.wav", VOICE_DIR / "陆沉.wav"],
    },
    "11b": {
        "dir": "红绳片段11b_可以被控制",
        "title": "可以被控制",
        "refs": [LUCHEN, LAOHAN, SCENE, LUDINGTIAN_PHOTO],
        "audios": [VOICE_DIR / "老韩.wav"],
    },
    "11c": {
        "dir": "红绳片段11c_巷子口",
        "title": "巷子口",
        "refs": [LUCHEN, LAOHAN, SCENE, LUDINGTIAN_PHOTO],
        "audios": [VOICE_DIR / "老韩.wav"],
    },
    "11d": {
        "dir": "红绳片段11d_我说话算话",
        "title": "我说话算话",
        "refs": [LUCHEN, LAOHAN, SCENE, LUDINGTIAN_PHOTO],
        "audios": [VOICE_DIR / "老韩.wav", VOICE_DIR / "陆沉.wav"],
    },
    # ---- 场 12｜母亲的名字（7 段，全集情绪最高点）----
    # 桌面新增陈玥照片（老韩从文件夹抽出，只放自己一侧，不递出）。
    # 工作流实测只有 4 个已验证图片槽（51/49/50/43），19/23 未验证，
    # 故本场用第 4 槽放陈玥照片，陆定天军装照退为提示词内的纯文字道具描述。
    "12a": {
        "dir": "红绳片段12a_换武器",
        "title": "换武器",
        "refs": [LUCHEN, LAOHAN, SCENE, CHENPHOTO],
        "audios": [VOICE_DIR / "老韩.wav"],
    },
    "12b": {
        "dir": "红绳片段12b_陈玥基因编码",
        "title": "陈玥，基因编码",
        "refs": [LUCHEN, LAOHAN, SCENE, CHENPHOTO],
        "audios": [VOICE_DIR / "老韩.wav"],
    },
    "12c": {
        "dir": "红绳片段12c_你说什么",
        "title": "你说什么",
        "refs": [LUCHEN, LAOHAN, SCENE, CHENPHOTO],
        "audios": [VOICE_DIR / "老韩.wav", VOICE_DIR / "陆沉.wav"],
    },
    "12d": {
        "dir": "红绳片段12d_可能不是意外",
        "title": "可能不是意外",
        "refs": [LUCHEN, LAOHAN, SCENE, CHENPHOTO],
        "audios": [VOICE_DIR / "老韩.wav", VOICE_DIR / "陆沉.wav"],
    },
    "12e": {
        "dir": "红绳片段12e_坐下",
        "title": "坐下",
        "refs": [LUCHEN, LAOHAN, SCENE, CHENPHOTO],
        "audios": [VOICE_DIR / "老韩.wav", VOICE_DIR / "陆沉.wav"],
    },
    "12e2": {
        "dir": "红绳片段12e2_解铐",
        "title": "解铐",
        "refs": [LUCHEN, LAOHAN, SCENE, CHENPHOTO],
        "audios": [VOICE_DIR / "老韩.wav"],
    },
    "12f": {
        "dir": "红绳片段12f_交换",
        "title": "交换",
        "refs": [LUCHEN, LAOHAN, SCENE, CHENPHOTO],
        "audios": [VOICE_DIR / "老韩.wav"],
    },
    "12g": {
        "dir": "红绳片段12g_你在骗我",
        "title": "你在骗我",
        "refs": [LUCHEN, LAOHAN, SCENE, CHENPHOTO],
        "audios": [VOICE_DIR / "老韩.wav", VOICE_DIR / "陆沉.wav"],
    },
    # ---- 场 13｜收尾（2 段）----
    "13a": {
        "dir": "红绳片段13a_比我想的难搞",
        "title": "比我想的难搞",
        "refs": [LUCHEN, LAOHAN, SCENE, CHENPHOTO],
        "audios": [VOICE_DIR / "老韩.wav"],
    },
    "13b": {
        "dir": "红绳片段13b_来的人不会跟你聊",
        "title": "来的人不会跟你聊",
        "refs": [LUCHEN, LAOHAN, SCENE, CHENPHOTO],
        "audios": [VOICE_DIR / "老韩.wav"],
    },
    # ---- 场 14｜独处（2 段）----
    # 老韩已离场，参考图里不再给他位置。
    "14a": {
        "dir": "红绳片段14a_捂脸",
        "title": "捂脸",
        "refs": [LUCHEN, SCENE, LUDINGTIAN_PHOTO],
        "audios": [],
    },
    "14b": {
        "dir": "红绳片段14b_我一定会查清楚",
        "title": "我一定会查清楚",
        "refs": [LUCHEN, SCENE, LUDINGTIAN_PHOTO],
        "audios": [VOICE_DIR / "陆沉.wav"],
    },
    # ---- 场 15｜观察廊（3 段）----
    # 15a/15b 场景切到单向玻璃另一侧的观察廊（用观察廊参考图替掉审问室）。
    "15a": {
        "dir": "红绳片段15a_观察廊汇报",
        "title": "观察廊汇报",
        "refs": [LAOHAN, OBSERVATORY],
        "audios": [VOICE_DIR / "老韩.wav"],
    },
    "15b": {
        "dir": "红绳片段15b_查是谁漏了口风",
        "title": "查是谁漏了口风",
        "refs": [LAOHAN, OBSERVATORY],
        "audios": [VOICE_DIR / "老韩.wav"],
    },
    # 15c 切回审问室，无对白。
    "15c": {
        "dir": "红绳片段15c_玻璃这边",
        "title": "玻璃这边",
        "refs": [LUCHEN, SCENE, LUDINGTIAN_PHOTO],
        "audios": [],
    },
}


def report_audio(video: Path, expect_voice: bool) -> None:
    """下载后立即校验音轨：有无音轨、时长、人声频段能量。

    金鱼工作流曾出现「提示词未绑音频槽→ 成片整段静音」的故障，
    仅靠肉眼看片发现太晚，故在保存环节强制体检。

    判定口径：
      - 无音轨流→ 报错（无论是否预期有人声）
      - 预期有人声但最大人声频段(85-255Hz)能量低于 -50dB → 报错
    """
    import json
    import subprocess

    def run(args: list[str]) -> bytes:
        return subprocess.run(args, capture_output=True).stdout

    info = run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                "-of", "json", str(video)])
    meta = json.loads(info or b"{}")
    streams = meta.get("streams") or []
    audio = [s for s in streams if s.get("codec_type") == "audio"]

    if not audio:
        print(f"❌ 音轨缺失：{video.name} 内无音频流", file=sys.stderr)
        return

    a = audio[0]
    dur = float(meta.get("format", {}).get("duration") or a.get("duration") or 0)
    print(f"音轨: {a.get('codec_name')} {a.get('sample_rate')}Hz "
          f"{a.get('channels')}ch · {dur:.2f}s", flush=True)

    if not expect_voice:
        print("  （本片段为纯空镜，不要求人声）", flush=True)
        return

    raw = run(["ffmpeg", "-v", "quiet", "-i", str(video),
               "-ac", "1", "-ar", "16000", "-f", "s16le", "-"])
    if not raw:
        print(f"❌ 音频解码失败：{video.name}", file=sys.stderr)
        return
    import numpy as np

    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    peak_db = 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
    # 人声基频带能量：逐 0.5s 取最大帧
    win = 8000
    best = -99.0
    for i in range(0, len(x) - win, win):
        seg = x[i:i + win] * np.hanning(win)
        spec = np.abs(np.fft.rfft(seg))
        freqs = np.fft.rfftfreq(win, 1 / 16000)
        m = (freqs >= 85) & (freqs < 255)
        best = max(best, 20 * np.log10(np.sqrt((spec[m] ** 2).sum()) / win + 1e-12))
    print(f"  整体RMS {peak_db:.1f}dB · 人声频段峰值 {best:.1f}dB", flush=True)
    if best < -50:
        print(f"❌ 人声疑似缺失：人声频段峰值 {best:.1f}dB 过低，"
              f"检查 <Audio N> 是否真正绑定到音频槽位", file=sys.stderr)


def normalize_for_phone(video: Path) -> Path:
    """重封装为手机可播的 MP4。

    RunningHub 返回的是 QuickTime MOV：moov（解码索引，含音轨描述符 esds）
    排在文件末尾，音轨是 32kHz AAC-LC。桌面 ffmpeg 能正常解码，
    但不少手机播放器读不到尾部索引就整条静音——成片必须在这里就修掉，
    否则交付到手机端才发现。

    处理：视频流 copy 不重编码；音轨重编为 44.1kHz 160k AAC-LC；
    -movflags +faststart 把 moov 提到文件头。原地覆盖，保持路径文件名不变。
    """
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "out.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(video),
             "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
             "-ar", "44100", "-ac", "2", "-movflags", "+faststart", str(tmp)],
            check=True,
        )
        if tmp.stat().st_size == 0:
            print(f"⚠️ 手机版重封装失败，保留原文件：{video.name}", file=sys.stderr)
            return video
        data = tmp.read_bytes()
    video.write_bytes(data)

    # 验证 moov 确实已前置，并确认音轨参数
    head = data[:65536]
    order = [head.find(b) for b in (b"ftyp", b"moov", b"mdat")]
    print(f"手机版重封装: ftyp/moov/mdat @ {order} "
          f"{'（moov 已前置 ✓）' if order[1] > 0 and order[1] < order[2] else '（⚠️ moov 未前置）'}",
          flush=True)
    return video


def run_segment(api_key: str, seg_id: str, suffix: str = "") -> int:
    conf = SEGMENTS[seg_id]
    seg = ROOT / "05-workflow" / "ep04" / conf["dir"]
    prompt_file = seg / "动作流_H3纯提示词.txt"
    out_dir = seg / "视频草稿"
    out = out_dir / f"E04-{seg_id}_{conf['title']}{suffix}_未审核草稿.mp4"

    audios = conf.get("audios", [])
    prompt = prompt_file.read_text(encoding="utf-8").strip()

    missing = [p for p in [prompt_file, *conf["refs"], *audios] if not Path(p).exists()]
    if missing:
        print("缺失文件:", *[str(m) for m in missing], sep="\n  ")
        return 1

    # H3 门禁：六段齐全且顺序正确
    labels = ["subject_definitions:", "summary:", "retention_analysis:",
              "detailed_description:", "overall_soundscape:", "non_diegetic_music:"]
    pos = [prompt.find(l) for l in labels]
    if any(i < 0 for i in pos) or pos != sorted(pos) or not prompt.startswith("subject_definitions:"):
        print("❌ 未通过 H3 标签门禁")
        return 1

    # 音频标签一致性：声明了 <Audio N> 就必须有对应音频文件，反之亦然
    declared = len(set(re.findall(r"<Audio (\d+)>", prompt)))
    if declared != len(audios):
        print(f"❌ 音频不一致：提示词声明 {declared} 个 <Audio N>，实际绑定 {len(audios)} 个音频")
        return 1
    # 每个发声事件只允许一次说话人标签
    for bad in re.findall(r"\(S\d+\)\s*<d>", prompt):
        print(f"❌ 检测到重复说话人标签：{bad}")
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    node_args = [
        f"263:text={prompt}",
        "252:aspect_ratio=16:9 (Widescreen)",
        "252:megapixels=0.5",
        "259:value=15",
        "283:value=1",
    ]
    file_args = [f"{SLOT_NODES[i]}:image={conf['refs'][i]}" for i in range(len(conf["refs"]))]
    file_args += [f"{AUDIO_SLOT_NODES[i]}:audio={audios[i]}" for i in range(len(audios))]

    print(f"\n=== 片段{seg_id} {conf['title']} ===", flush=True)
    print(f"提示词 {len(prompt)} 字 · 参考图 {len(conf['refs'])} 张 · 音频 {len(audios)} 条 · 15s · 0.5MP", flush=True)
    for i, r in enumerate(conf["refs"]):
        print(f"  @图片{i+1} -> {Path(r).name}", flush=True)
    for i, a in enumerate(audios):
        print(f"  <Audio {i+1}> -> {Path(a).name}", flush=True)

    nodes = apply_modifications(api_key, get_node_info(api_key, APP_ID), node_args, file_args)
    data = submit_task(api_key, APP_ID, nodes)
    task_id = str(data["taskId"])
    print(f"taskId = {task_id}", flush=True)

    final = poll_task(api_key, task_id)
    results = final.get("results") or []
    if not results:
        raise RuntimeError("任务完成但未返回文件")

    usage = final.get("usage") or {}
    print("状态:", final.get("status"), "消耗:", usage, flush=True)

    saved = []
    for idx, item in enumerate(results, start=1):
        url = item.get("url") or item.get("outputUrl")
        if not url:
            continue
        dest = out if len(results) == 1 else out.with_name(f"{out.stem}_{idx}{out.suffix}")
        download_file(url, str(dest))
        fix_mov_to_mp4(str(dest))
        dest = normalize_for_phone(dest)
        report_audio(dest, expect_voice=bool(audios))
        saved.append(dest)
        print(f"已保存 {dest} ({dest.stat().st_size // 1024} KB)", flush=True)

    (seg / "RH任务回执.json").write_text(
        json.dumps({"segment": seg_id, "taskId": task_id, "status": final.get("status"),
                    "usage": usage, "saved": [str(s) for s in saved]},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("segments", nargs="+", choices=sorted(SEGMENTS), help="片段编号，如 07 08")
    ap.add_argument("--suffix", default="", help="输出文件名后缀，如 _v2")
    args = ap.parse_args()

    api_key = require_api_key(os.environ.get("RH_API_KEY"))
    rc = 0
    for seg_id in args.segments:
        rc |= run_segment(api_key, seg_id, args.suffix)
    return rc


if __name__ == "__main__":
    sys.exit(main())