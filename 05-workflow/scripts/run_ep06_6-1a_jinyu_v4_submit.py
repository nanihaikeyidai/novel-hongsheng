# -*- coding: utf-8 -*-
"""EP06 6-1a｜云端金鱼 H3 Ref2VA Plus 提交（v4 · 静态降级版）。

触发：2026-11-14 用户判 v3「不行，还是控制不住，不用表达跳车动作，只表达
开门动作准备跳的东西，然后镜头切蓝隼脸部邪恶笑容特写，再切到装过来的车，
旁边背景不用动，看隼正面对着车不是侧面」→ 先出 6 宫格图确认镜头理解 →
用户 13:16「可以，生视频」＝该次已确认（David §一.17），**只提交 1 次**。

v4 相对 v3（G19 静态降级）：
  1) 删除整条复杂动作链：跳车／脚踢／空中旋转／落地爆炸全部物理清零（G16），
     连否定句都不写（A 型：写「不要爆炸」等于把爆炸放回潜空间）。
  2) 全片只剩 3 类可静止表达的状态变化：两扇前门打开、笑容变大、车距缩短；
     时间推进靠切镜，不靠模型算物理。
  3) STATIC SHOT LOCK：每镜 ONE FIXED camera，柱子／灯管／停车线／远车影
     逐帧同屏幕坐标；G17 的 MOTION UNITY LOCK / INHERITING 与 K 型的
     ACCELERATES HARD / SPEED LINES / motion blur / GROWS LARGER 全部清零
     （用户明说「背景不用动」，与 G17 互斥，见避坑手册约束块 9c）。
  4) FRONT-FACING LOCK：蓝隼每镜 FULL FRONT VIEW、双肩平齐、墨镜对称，
     按 G14 把方向锚在「车头双灯 → 蓝隼胸口」两主体相对关系上。
  5) 人物口径不变：安娜主驾 LEFT、陆沉副驾 RIGHT，二人 hips STILL ON THE
     SEAT / REMAINS INSIDE，只开门不跳车；蓝隼墨镜 NEVER removed。

闸门 EP06_6_1A_V4_CONFIRMED=1 仅用于防误触；提交与轮询拆开（G09），
本地断连只续轮询同一 taskId，绝不二次提交。

参考槽位（G05）：51=<Picture 1> 安娜 / 49=<Picture 2> 车库 / 50=<Picture 3> 蓝隼。
48/14/15 音频槽默认 None；本段 0 台词不绑音频（P02 先例、G13）。
素材沿用 `上传包_云端/` 三张已验收图，**6 宫格确认图不得喂进 <Picture N>**。

应用 2110357037929558018｜16:9 / 15s / 1.5MP / simple / 12 步 → 1664×928。
预估约 76–82 积分，实际以回执 usage.settleMode 为准（G12）。
⚠️ Windows Schannel 的 curl 需 --ssl-no-revoke（G11）。
"""
from __future__ import annotations

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

PROMPT = SEG / "金鱼_H3纯提示词_EP06_6-1a_v4.txt"
REFS = [
    PACK / "ep06s01c_anna.png",           # 51 -> <Picture 1>
    PACK / "ep06s01c_garage.png",         # 49 -> <Picture 2>
    PACK / "ep06s01c_lansun_clean.png",   # 50 -> <Picture 3>
]
AUDIOS: list[Path] = []
IMAGE_NODES = ("51", "49", "50")
AUDIO_NODES: tuple[str, ...] = ()
TASKID_FILE = SEG / "_jinyu_v4.taskid"

HARD_LOCKS = (
    "SETTING FIRST", "STATIC SHOT LOCK", "FRONT-FACING LOCK", "FULL FRONT VIEW",
    "WINDSHIELD INTERIOR POV", "SAME screen coordinates", "STILL ON THE SEAT",
    "REMAINS INSIDE", "WIDE SINISTER SMIRK", "NEVER removed", "BLUE-BLACK",
    "ZERO dialogue", "NEVER reverses", "BEFORE contact", "SHRINKS",
    "AT Lan Sun", "CUT to", "FIXED",
)
# G16：上一版动作词物理清零 + G19：K 型加速词/运动锁清零 + A 型事故形态
BANNED = (
    "punch", "fist", "kick", "right boot lands", "SPINNING", "corkscrew",
    "EXPLODES", "explosion", "WHITE-hot flash", "BLUE-WHITE shockwave",
    "BLACK smoke", "bail", "leap", "jump", "tumble", "roll out",
    "MOTION UNITY LOCK", "INHERITING", "ACCELERATES HARD", "SPEED LINES",
    "motion blur", "GROWS LARGER", "cuts get SHORTER", "cuts shorten",
    "camera SHAKES", "ONE SINGLE PUNCH", "half-turn in mid-air",
    "coasts", "rolls forward", "MOTIONLESS", "Hold >=", "slow motion",
    "freeze frames", "gentle", "steady", "piano", "musical instrument",
    "wooden", "energy thread", "negativePrompt", "SALE",
)


def main() -> int:
    if os.environ.get("EP06_6_1A_V4_CONFIRMED") != "1":
        raise SystemExit(
            "EP06 6-1a v4: 未获确认，拒绝提交视频生成（约 76-82 积分，POINT 结算）。"
            "用户已确认后请设 EP06_6_1A_V4_CONFIRMED=1 再运行。"
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
        raise ValueError("EP06 6-1a v4: H3 gate failed (6 labels order)")
    nbytes = len(prompt.encode("utf-8"))
    if nbytes > 5000:
        raise ValueError(f"EP06 6-1a v4: prompt too long {nbytes} bytes")
    pics = set(re.findall(r"<Picture (\d+)>", prompt))
    if pics != {str(i + 1) for i in range(len(REFS))}:
        raise ValueError(f"EP06 6-1a v4: picture mismatch prompt={pics} bound={len(REFS)}")
    declared = len(set(re.findall(r"<Audio (\d+)>", prompt)))
    if declared != len(AUDIOS):
        raise ValueError(f"EP06 6-1a v4: audio mismatch prompt={declared} bound={len(AUDIOS)}")
    for stale in BANNED:
        if stale.lower() in prompt.lower():
            raise ValueError(f"EP06 6-1a v4: banned concept/word: {stale}")
    for hard in HARD_LOCKS:
        if hard not in prompt:
            raise ValueError(f"EP06 6-1a v4: missing hard lock: {hard}")
    if prompt.count("AT Lan Sun") < 2:
        raise ValueError("EP06 6-1a v4: direction anchor to person missing")
    if len(re.findall(r"\[Shot \d+\]", prompt)) != 5:
        raise ValueError("EP06 6-1a v4: expected 5 shots")
    for f in REFS + AUDIOS:
        if not f.exists():
            raise FileNotFoundError(f"EP06 6-1a v4: missing asset {f}")
    if TASKID_FILE.exists():
        raise SystemExit(
            f"EP06 6-1a v4: taskId 已存在 ({TASKID_FILE.read_text(encoding='utf-8').strip()})，"
            "拒绝二次提交；请用 resume 脚本续轮询（G09）。"
        )

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
        f"=== EP06 6-1a v4 静态降级 | 云端金鱼 {APP_ID} | "
        f"{nbytes} bytes | 15s | 1.5MP | 12 steps | 0 audio ===",
        flush=True,
    )
    for i, r in enumerate(REFS):
        print(f"  image{i+1} node {IMAGE_NODES[i]} -> {r.name}", flush=True)
    print("  G19: FIXED cameras / background at SAME screen coordinates / 3 static state changes", flush=True)
    print("  G16: jump-kick-spin-explode chain physically removed (no denial either)", flush=True)
    print("  G14: nose+headlights AT Lan Sun's chest; Lan Sun FULL FRONT VIEW every shot", flush=True)
    print("  estimated ~76-82 POINT (usage receipt wins, G12)", flush=True)

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
            fatal = any(k in low for k in (
                "balance", "coin", "insufficient", "recharge", "余额", "金币",
                "invalid_key", "unauthorized", "401", "403", "not enough",
            ))
            if fatal:
                raise RuntimeError(f"EP06 6-1a v4: FATAL submit refused (no retry): {msg}") from exc
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
        raise RuntimeError("EP06 6-1a v4: submit returned no data")

    task_id = str(data["taskId"])
    TASKID_FILE.write_text(task_id, encoding="utf-8")
    print(f"taskId = {task_id}", flush=True)
    print(f"taskId saved to {TASKID_FILE}", flush=True)
    print("SUBMIT DONE — poll/download with resume_ep06_6-1a_jinyu_v4.py, NEVER resubmit", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
