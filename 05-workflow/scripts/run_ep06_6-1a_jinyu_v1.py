# -*- coding: utf-8 -*-
"""EP06 6-1a 跳车掀车｜RunningHub 云端金鱼 H3 Ref2VA Plus 提交（v1）。

触发：2026-11-12 David「重新生成视频，用云端金鱼工作流」。
按 David §一.17：用户明说「重新生成」＝该次已确认，本脚本**只提交 1 次**，
出片后不自动迭代第二版。闸门 EP06_6_1A_CONFIRMED=1 仅用于防误触。

上一次（2026-11-11）本地梅林 v1 画面完全跑偏（安娜弹钢琴、无车库/蓝隼/车），
根因 G08 上下文预算超支。本轮改走云端金鱼 1.5MP / 12 步，按该链路已跑通
提示词基线 4712-4940 bytes 写稿（不是本地梅林 1185 字符基线）。

参考槽位（与本地梅林同源，G05 已核对）：
  51 = image1 = <Picture 1> 安娜
  49 = image2 = <Picture 2> 车库
  50 = image3 = <Picture 3> 蓝隼
  48/14/15 三个音频槽默认 None；本段 0 台词，不绑音频（P02 无对白先例）。

应用：2110357037929558018（YZ金鱼 H3 Ref2VA Plus）
规格：16:9 / 15s / 1.5MP / simple / 12 步 → 1664×928
预计币耗：约 379-425 币（P04a 4 图+1 音频实测 449 币，本轮 3 图 0 音频）。

⚠️ 本机 Windows curl 走 Schannel，会报
   CRYPT_E_REVOCATION_OFFLINE (0x80092013)，需给所有 curl 调用注入
   --ssl-no-revoke；否则 get_node_info / submit / download 全部失败。
   这里用 subprocess.run 包装器统一注入，不改全局 skill 库文件。
"""
from __future__ import annotations

import json
import os
import re
import subprocess as _sp
import sys
import time
from pathlib import Path

RUNNINGHUB_SCRIPTS = Path(r"C:\Users\Administrator\.codex\skills\runninghub\scripts")
sys.path.insert(0, str(RUNNINGHUB_SCRIPTS))

_orig_run = _sp.run


def _patched_run(*args, **kwargs):
    """注入 --ssl-no-revoke（Schannel 吊销检查离线）+ UTF-8 容错解码。"""
    cmd = args[0] if args else kwargs.get("args")
    if isinstance(cmd, (list, tuple)) and cmd and str(cmd[0]).lower().endswith("curl"):
        cmd = list(cmd)
        if "--ssl-no-revoke" not in cmd:
            cmd.insert(1, "--ssl-no-revoke")
        if args:
            args = (cmd,) + args[1:]
        else:
            kwargs["args"] = cmd
    if kwargs.get("text") or kwargs.get("universal_newlines"):
        kwargs.setdefault("encoding", "utf-8")
        kwargs.setdefault("errors", "replace")
    return _orig_run(*args, **kwargs)


_sp.run = _patched_run

from runninghub import download_file, fix_mov_to_mp4, poll_task, require_api_key  # noqa: E402
from runninghub_app import apply_modifications, get_node_info, submit_task  # noqa: E402

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
APP_ID = "2110357037929558018"
SEG = ROOT / "05-workflow" / "ep06" / "6-1a_跳车掀车"
PACK = SEG / "上传包_云端"

PROMPT = SEG / "金鱼_H3纯提示词_EP06_6-1a_v1.txt"
REFS = [
    PACK / "ep06s01c_anna.png",           # 51 -> <Picture 1>
    PACK / "ep06s01c_garage.png",         # 49 -> <Picture 2>
    PACK / "ep06s01c_lansun_clean.png",   # 50 -> <Picture 3>
]
AUDIOS: list[Path] = []
IMAGE_NODES = ("51", "49", "50")
AUDIO_NODES: tuple[str, ...] = ()
OUT = SEG / "视频草稿" / "EP06_6-1a_金鱼_v1.mp4"
RECEIPT = SEG / "RH任务回执_金鱼_EP06_6-1a_v1.json"


def main() -> int:
    if os.environ.get("EP06_6_1A_CONFIRMED") != "1":
        raise SystemExit(
            "EP06 6-1a v1: 未获确认，拒绝提交视频生成（约 379-425 币）。"
            "确认后请设 EP06_6_1A_CONFIRMED=1 再运行。"
        )
    api_key = require_api_key(
        os.environ.get("RH_API_KEY") or os.environ.get("RUNNINGHUB_API_KEY")
    )

    prompt = PROMPT.read_text(encoding="utf-8").strip()
    labels = [
        "subject_definitions:",
        "summary:",
        "retention_analysis:",
        "detailed_description:",
        "overall_soundscape:",
        "non_diegetic_music:",
    ]
    pos = [prompt.find(l) for l in labels]
    if any(i < 0 for i in pos) or pos != sorted(pos) or not prompt.startswith("subject_definitions:"):
        raise ValueError("EP06 6-1a: H3 gate failed (6 labels order)")
    nbytes = len(prompt.encode("utf-8"))
    if nbytes > 5000:
        raise ValueError(f"EP06 6-1a: prompt too long {nbytes} bytes")
    pics = set(re.findall(r"<Picture (\d+)>", prompt))
    if pics != {str(i + 1) for i in range(len(REFS))}:
        raise ValueError(f"EP06 6-1a: picture mismatch prompt={pics} bound={len(REFS)}")
    declared = len(set(re.findall(r"<Audio (\d+)>", prompt)))
    if declared != len(AUDIOS):
        raise ValueError(f"EP06 6-1a: audio mismatch prompt={declared} bound={len(AUDIOS)}")
    if "negativePrompt" in prompt:
        raise ValueError("EP06 6-1a: no negativePrompt segment on cloud Jinyu (A-type leakage)")
    # A 型：禁止把 v1 事故形态（钢琴/木墙/能量丝）写进负向清单
    for stale in ("piano", "musical instrument", "wooden", "energy thread", "SALE"):
        if stale.lower() in prompt.lower():
            raise ValueError(f"EP06 6-1a: stale negative concept: {stale}")
    for hard in (
        "SETTING FIRST", "BLUE-BLACK", "NEVER removed", "BARE FIST",
        "ZERO dialogue", "NEVER reverses", "MOTIONLESS",
    ):
        if hard not in prompt:
            raise ValueError(f"EP06 6-1a: missing hard lock: {hard}")
    if len(re.findall(r"\[Shot \d+\]", prompt)) != 5:
        raise ValueError("EP06 6-1a: expected 5 shots")
    for f in REFS + AUDIOS:
        if not f.exists():
            raise FileNotFoundError(f"EP06 6-1a: missing asset {f}")

    node_args = [
        f"263:text={prompt}",
        "252:aspect_ratio=16:9 (Widescreen)",
        "252:megapixels=1.5",
        "259:value=15",
        "261:scheduler=simple",
        "261:steps=12",
    ]
    file_args = [f"{IMAGE_NODES[i]}:image={REFS[i]}" for i in range(len(REFS))]
    file_args += [f"{AUDIO_NODES[i]}:audio={AUDIOS[i]}" for i in range(len(AUDIOS))]

    print(
        f"=== EP06 6-1a v1 跳车掀车 | 云端金鱼 {APP_ID} | "
        f"{nbytes} bytes | 15s | 1.5MP | 12 steps | 0 audio ===",
        flush=True,
    )
    for i, r in enumerate(REFS):
        print(f"  image{i+1} node {IMAGE_NODES[i]} -> {r.name}", flush=True)
    print("  audio: none (0 dialogue; P02 precedent)", flush=True)

    def _rh_call(fn, *args, **kwargs):
        real_exit = sys.exit

        def _trap(code=0):
            raise RuntimeError(f"RH_API_EXIT code={code}")

        sys.exit = _trap  # type: ignore[assignment]
        try:
            return fn(*args, **kwargs)
        finally:
            sys.exit = real_exit

    delay = 45
    data = None
    nodes = None
    for attempt in range(1, 13):
        try:
            if nodes is None:
                nodes = _rh_call(
                    apply_modifications,
                    api_key,
                    _rh_call(get_node_info, api_key, APP_ID),
                    node_args,
                    file_args,
                )
            data = _rh_call(submit_task, api_key, APP_ID, nodes)
            break
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            print(f"submit error attempt {attempt}: {msg}", flush=True)
            low = msg.lower()
            # 余额／鉴权／参数类硬失败：立刻停，绝不重试（一次反馈=一次生成）
            fatal = any(k in low for k in (
                "balance", "coin", "insufficient", "recharge", "余额", "金币",
                "invalid_key", "unauthorized", "401", "403", "not enough",
            ))
            if fatal:
                raise RuntimeError(f"EP06 6-1a: FATAL submit refused (no retry): {msg}") from exc
            retryable = (
                "RH_API_EXIT" in msg or "421" in msg
                or "queue" in msg.lower() or "QUEUE" in msg
            )
            if not retryable or attempt == 12:
                raise
            nodes = None
            print(f"sleep {delay}s then retry...", flush=True)
            time.sleep(delay)
            delay = min(delay + 30, 180)

    if not data:
        raise RuntimeError("EP06 6-1a: submit returned no data")

    task_id = str(data["taskId"])
    print(f"taskId = {task_id}", flush=True)

    final = poll_task(api_key, task_id)
    results = final.get("results") or []
    if not results:
        raise RuntimeError("EP06 6-1a: task done but no files")

    usage = final.get("usage") or {}
    print("status:", final.get("status"), "usage:", usage, flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    saved = []
    for idx, item in enumerate(results, start=1):
        url = item.get("url") or item.get("outputUrl")
        if not url:
            continue
        dest = OUT if len(results) == 1 else OUT.with_name(f"{OUT.stem}_{idx}{OUT.suffix}")
        download_file(url, str(dest))
        fix_mov_to_mp4(str(dest))
        saved.append(dest)
        print(f"saved {dest} ({dest.stat().st_size // 1024} KB)", flush=True)

    receipt = {
        "unit": "EP06_6-1a_v1_jinyu",
        "versionNote": (
            "从本地梅林 v1 未达标试片改走云端金鱼；场景动作前置、4957 bytes（云端已跑通基线内）；"
            "3 张预缩放同画风域参考图、蓝隼残留能量丝已物理清除；0 音频槽（全段无对白）；"
            "不含 negativePrompt 段与任何事故形态负向词。一次反馈=一次生成，未迭代第二版"
        ),
        "workflow": "金鱼云端",
        "appId": APP_ID,
        "taskId": task_id,
        "status": final.get("status"),
        "usage": usage,
        "promptBytes": nbytes,
        "params": "16:9 / 15s / 1.5MP / simple / 12",
        "refs": [str(r) for r in REFS],
        "audios": [],
        "nodes": {"prompt": "263", "images": list(IMAGE_NODES), "audios": []},
        "saved": [str(s) for s in saved],
        "tlsFix": "curl --ssl-no-revoke (Schannel CRYPT_E_REVOCATION_OFFLINE)",
    }
    RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"done": "EP06_6-1a_v1", "taskId": task_id,
                      "saved": [str(s) for s in saved]}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
