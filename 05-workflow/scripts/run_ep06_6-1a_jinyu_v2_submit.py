# -*- coding: utf-8 -*-
"""EP06 6-1a 跳车掀车｜云端金鱼 H3 Ref2VA Plus 提交（v2）。

触发：2026-11-13 David「不合格，方向不对，车头要对着蓝隼，跳车时车是加速
状态，撞向蓝隼，蓝隼一拳把车整个掀翻，要动态强，速度快，重新生成」。
按 David §一.17：用户明说「重新生成」＝该次已确认，本脚本**只提交 1 次**，
出片后不自动迭代第三版。闸门 EP06_6_1A_V2_CONFIRMED=1 仅用于防误触。

v1 不合格归因（详见 EP06_6-1a_金鱼_v2_复盘.md）：
  1) J 型方向锁锚错参照系：v1 写「nose into depth toward the exit ramp」，
     方向锚在「画面深处/坡道」这个相机坐标系上，机位一换就漂；成片从车尾
     拍、车头朝外，蓝隼成了远处小人影，读不出「车头对着蓝隼」。
     v2 改成**相对人物锚**：NOSE + BOTH headlights aim AT Lan Sun's chest、
     IN THE HEADLIGHT CONE、bumper→boots 距离 SHRINKS frame by frame、
     每镜 LOW three-quarter FRONT-SIDE 同框。
  2) K 型运动速率未定义 / 未遵循既有规则：v1 用 coasts / rolls forward /
     MOTIONLESS / fixed / Hold >=0.5s，全是惯性滑行＋定机位。v2 按避坑手册
     约束块 9 补满 ACCELERATES HARD / SPEED LINES / motion blur / GROWS
     LARGER / cuts get SHORTER，并删净全部「稳／慢」字眼。
  3) 「一拳掀翻整车」：v1 写「拳压凹车头→车尾掀起→绕车头侧转」，成片是
     车头被压凹后侧倒。v2 写 ONE SINGLE PUNCH → ENTIRE car LAUNCHED off
     the ground / all four wheels leaving / half-turn in mid-air。

本脚本只负责提交并落盘 taskId；轮询下载见 resume_ep06_6-1a_jinyu_v2.py
（G09：提交与轮询拆开，本地进程超时≠生成失败，绝不二次提交）。

参考槽位（G05 已核对）：51=<Picture 1> 安娜 / 49=<Picture 2> 车库 / 50=<Picture 3> 蓝隼。
48/14/15 三个音频槽默认 None；本段 0 台词，不绑音频（P02 先例、G13）。
应用 2110357037929558018｜16:9 / 15s / 1.5MP / simple / 12 步 → 1664×928。
结算：v1 回执为 settleMode=POINT、chargedPoint=82.45（金币 0 仍跑通，G12）；
本轮按同规格预估约 82 积分，实际以回执 usage 为准。

⚠️ Windows Schannel 的 curl 需 --ssl-no-revoke（G11），用 subprocess.run
   包装器统一注入 + UTF-8 容错解码，不改全局 skill 库。
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

from runninghub import require_api_key  # noqa: E402
from runninghub_app import apply_modifications, get_node_info, submit_task  # noqa: E402

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
APP_ID = "2110357037929558018"
SEG = ROOT / "05-workflow" / "ep06" / "6-1a_跳车掀车"
PACK = SEG / "上传包_云端"

PROMPT = SEG / "金鱼_H3纯提示词_EP06_6-1a_v2.txt"
REFS = [
    PACK / "ep06s01c_anna.png",           # 51 -> <Picture 1>
    PACK / "ep06s01c_garage.png",         # 49 -> <Picture 2>
    PACK / "ep06s01c_lansun_clean.png",   # 50 -> <Picture 3>
]
AUDIOS: list[Path] = []
IMAGE_NODES = ("51", "49", "50")
AUDIO_NODES: tuple[str, ...] = ()
TASKID_FILE = SEG / "_jinyu_v2.taskid"

# v2 硬锁：场景/方向/加速/一拳掀翻/人物/无对白，逐条断言
HARD_LOCKS = (
    "SETTING FIRST", "DIRECTION LOCK", "SPEED LOCK", "ACCELERATES",
    "ONE SINGLE PUNCH", "ENTIRE", "SHRINKS", "GROWS LARGER", "SPEED LINES",
    "BLUE-BLACK", "NEVER removed", "BARE FIST", "ZERO dialogue",
    "NEVER reverses", "feet planted", "camera SHAKES", "FRONT-SIDE",
    "TRACKING", "all four wheels leaving", "half-turn in mid-air",
)
# A 型：事故形态负向词；K 型：拖节奏字眼，一律禁止进入提示词
BANNED = (
    "piano", "musical instrument", "wooden", "energy thread", "negativePrompt",
    "SALE", "coasts", "rolls forward", "MOTIONLESS", "Hold >=",
    "slow motion", "freeze frames", "gentle", "steady", "never break stride",
)


def main() -> int:
    if os.environ.get("EP06_6_1A_V2_CONFIRMED") != "1":
        raise SystemExit(
            "EP06 6-1a v2: 未获确认，拒绝提交视频生成（约 82 积分，POINT 结算）。"
            "确认后请设 EP06_6_1A_V2_CONFIRMED=1 再运行。"
        )
    api_key = require_api_key(
        os.environ.get("RH_API_KEY") or os.environ.get("RUNNINGHUB_API_KEY")
    )

    prompt = PROMPT.read_text(encoding="utf-8").strip()
    labels = [
        "subject_definitions:", "summary:", "retention_analysis:",
        "detailed_description:", "overall_soundscape:", "non_diegetic_music:",
    ]
    pos = [prompt.find(l) for l in labels]
    if any(i < 0 for i in pos) or pos != sorted(pos) or not prompt.startswith("subject_definitions:"):
        raise ValueError("EP06 6-1a v2: H3 gate failed (6 labels order)")
    nbytes = len(prompt.encode("utf-8"))
    if nbytes > 5000:
        raise ValueError(f"EP06 6-1a v2: prompt too long {nbytes} bytes")
    pics = set(re.findall(r"<Picture (\d+)>", prompt))
    if pics != {str(i + 1) for i in range(len(REFS))}:
        raise ValueError(f"EP06 6-1a v2: picture mismatch prompt={pics} bound={len(REFS)}")
    declared = len(set(re.findall(r"<Audio (\d+)>", prompt)))
    if declared != len(AUDIOS):
        raise ValueError(f"EP06 6-1a v2: audio mismatch prompt={declared} bound={len(AUDIOS)}")
    for stale in BANNED:
        if stale.lower() in prompt.lower():
            raise ValueError(f"EP06 6-1a v2: banned concept/word: {stale}")
    for hard in HARD_LOCKS:
        if hard not in prompt:
            raise ValueError(f"EP06 6-1a v2: missing hard lock: {hard}")
    if prompt.count("AT Lan Sun") < 6:
        raise ValueError("EP06 6-1a v2: direction anchor not restated enough")
    if len(re.findall(r"\[Shot \d+\]", prompt)) != 5:
        raise ValueError("EP06 6-1a v2: expected 5 shots")
    for f in REFS + AUDIOS:
        if not f.exists():
            raise FileNotFoundError(f"EP06 6-1a v2: missing asset {f}")

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
        f"=== EP06 6-1a v2 跳车掀车 | 云端金鱼 {APP_ID} | "
        f"{nbytes} bytes | 15s | 1.5MP | 12 steps | 0 audio ===",
        flush=True,
    )
    for i, r in enumerate(REFS):
        print(f"  image{i+1} node {IMAGE_NODES[i]} -> {r.name}", flush=True)
    print("  direction anchor: NOSE/headlights AT Lan Sun + gap SHRINKS (relative to person)", flush=True)
    print("  tempo: ACCELERATES HARD / SPEED LINES / GROWS LARGER / cuts SHORTER", flush=True)

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
                raise RuntimeError(f"EP06 6-1a v2: FATAL submit refused (no retry): {msg}") from exc
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
        raise RuntimeError("EP06 6-1a v2: submit returned no data")

    task_id = str(data["taskId"])
    TASKID_FILE.write_text(task_id, encoding="utf-8")
    print(f"taskId = {task_id}", flush=True)
    print(f"taskId saved to {TASKID_FILE}", flush=True)
    print("SUBMIT DONE — poll/download with resume_ep06_6-1a_jinyu_v2.py, NEVER resubmit", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
