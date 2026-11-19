# -*- coding: utf-8 -*-
"""EP06 6-1a｜云端金鱼 H3 Ref2VA Plus 提交（v5 · 加速版）。

触发：2026-11-14 用户判 v4「动作太慢了，动作要快，车速也要快，加速撞的感觉，
要夸张点增加速度赶，给一个车轮加速的镜头，现在是慢吞吞开过去」。
按 G20 本应先出加速版 6 宫格确认镜头理解，用户主动取消出图并选择「直接生成
v5 视频」＝该次已确认（David §一闸门），**只提交 1 次**；本轮豁免留痕在复盘。

v5 相对 v4（口径反转，G23 边界修正）：
  1) 恢复 K 型全部加速锚点：ACCELERATES HARD / SPEED LINES / motion blur /
     GROWS LARGER / SHRINKS FASTER / cuts get SHORTER / radial streaks。
     根因：G19 / 约束块 9c「用户说背景不用动时 K 型加速词一并清零」写得过宽，
     静态降级只该降「动作链复杂度」，不该连「速率」一起降 → v4 慢吞吞。
  2) 但「背景不用动」用户未撤回：BACKGROUND LOCK 仍锁柱子／灯管／停车线
     逐帧同屏幕坐标，速度线只贴车身／轮拱／地面反光带，NEVER over pillars。
     因此不写 9b 的 MOTION UNITY LOCK / INHERITING / pillars streak past
     （与背景静止锁互斥，二选一）。
  3) 新增 [Shot 5] 贴地车轮加速特写；全片 6 镜，末镜内 3 个短拍切回同机位。
  4) 动作链仍保持 G19 降级：不跳车、不踢、不翻、不爆炸（G16 物理清零，
     连否定句都不写）；只把「速率」加回来，门 SNAP open IN ONE BEAT。
  5) G21：蓝隼特写补机位层正轴锁，参考图行声明不继承 3/4 侧拍摄角度。
  6) G14 方向锁：车头双灯 → 蓝隼胸口，NEVER reverses / NEVER passes him。

闸门 EP06_6_1A_V5_CONFIRMED=1；提交与轮询拆开（G09），本地断连只续轮询
同一 taskId，绝不二次提交。

参考槽位（G05）：51=<Picture 1> 安娜 / 49=<Picture 2> 车库 / 50=<Picture 3> 蓝隼。
48/14/15 音频槽默认 None；本段 0 台词不绑音频（P02 先例、G13）。
素材沿用 `上传包_云端/` 三张已验收图；**宫格图不得喂进 <Picture N>**。

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

PROMPT = SEG / "金鱼_H3纯提示词_EP06_6-1a_v5.txt"
REFS = [
    PACK / "ep06s01c_anna.png",           # 51 -> <Picture 1>
    PACK / "ep06s01c_garage.png",         # 49 -> <Picture 2>
    PACK / "ep06s01c_lansun_clean.png",   # 50 -> <Picture 3>
]
AUDIOS: list[Path] = []
IMAGE_NODES = ("51", "49", "50")
AUDIO_NODES: tuple[str, ...] = ()
TASKID_FILE = SEG / "_jinyu_v5.taskid"

HARD_LOCKS = (
    "SETTING FIRST", "BACKGROUND LOCK", "SPEED LOCK", "FRONT-FACING LOCK",
    "ACCELERATES HARD", "SPEED LINES", "motion blur", "radial streaks",
    "cuts get SHORTER", "GROWS LARGER", "SHRINKS FASTER", "SNAP open IN ONE BEAT",
    "FULL FRONT VIEW", "CAMERA ON HIS CENTRAL AXIS", "BOTH EARS VISIBLE",
    "lenses EQUAL width", "WINDSHIELD INTERIOR POV", "GROUND-LEVEL WHEEL CLOSE-UP",
    "THREE SHORT BEATS", "SAME screen coordinates", "no background drift",
    "STILL ON THE SEAT", "REMAINS INSIDE", "WIDE SINISTER SMIRK", "NEVER removed",
    "BLUE-BLACK", "ZERO dialogue", "NEVER reverses", "NEVER passes him",
    "BEFORE contact", "AT Lan Sun", "CUT to", "DO NOT inherit its camera angle",
    "URGENT", "RISING in pitch",
)
# G16 旧动作链清零 + G19 静态词清零 + G17 运动锁互斥 + A 型事故形态
BANNED = (
    "STATIC SHOT LOCK", "still tension", "Hold >=", "MOTIONLESS", "slow motion",
    "gentle", "steady", "quiet", "coasts", "rolls forward", "freeze frames",
    "MOTION UNITY LOCK", "INHERITING", "pillars streak past", "no speed lines",
    "no motion blur", "cuts carry the timeline",
    "punch", "fist", "kick", "right boot lands", "spinning", "corkscrew",
    "EXPLODES", "explosion", "WHITE-hot flash", "BLUE-WHITE shockwave",
    "BLACK smoke", "bail", "leap", "jump", "tumble", "roll out",
    "piano", "musical instrument", "wooden", "energy thread", "negativePrompt", "SALE",
)


def main() -> int:
    if os.environ.get("EP06_6_1A_V5_CONFIRMED") != "1":
        raise SystemExit(
            "EP06 6-1a v5: 未获确认，拒绝提交视频生成（约 76-82 积分，POINT 结算）。"
            "用户已确认后请设 EP06_6_1A_V5_CONFIRMED=1 再运行。"
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
        raise ValueError("EP06 6-1a v5: H3 gate failed (6 labels order)")
    nbytes = len(prompt.encode("utf-8"))
    if nbytes > 5000:
        raise ValueError(f"EP06 6-1a v5: prompt too long {nbytes} bytes")
    pics = set(re.findall(r"<Picture (\d+)>", prompt))
    if pics != {str(i + 1) for i in range(len(REFS))}:
        raise ValueError(f"EP06 6-1a v5: picture mismatch prompt={pics} bound={len(REFS)}")
    declared = len(set(re.findall(r"<Audio (\d+)>", prompt)))
    if declared != len(AUDIOS):
        raise ValueError(f"EP06 6-1a v5: audio mismatch prompt={declared} bound={len(AUDIOS)}")
    for stale in BANNED:
        if stale.lower() in prompt.lower():
            raise ValueError(f"EP06 6-1a v5: banned concept/word: {stale}")
    for hard in HARD_LOCKS:
        if hard not in prompt:
            raise ValueError(f"EP06 6-1a v5: missing hard lock: {hard}")
    if prompt.count("AT Lan Sun") < 2:
        raise ValueError("EP06 6-1a v5: direction anchor to person missing")
    if len(re.findall(r"\[Shot \d+\]", prompt)) != 6:
        raise ValueError("EP06 6-1a v5: expected 6 shots")
    for f in REFS + AUDIOS:
        if not f.exists():
            raise FileNotFoundError(f"EP06 6-1a v5: missing asset {f}")
    if TASKID_FILE.exists():
        raise SystemExit(
            f"EP06 6-1a v5: taskId 已存在 ({TASKID_FILE.read_text(encoding='utf-8').strip()})，"
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
        f"=== EP06 6-1a v5 加速版 | 云端金鱼 {APP_ID} | "
        f"{nbytes} bytes | 15s | 1.5MP | 12 steps | 0 audio ===",
        flush=True,
    )
    for i, r in enumerate(REFS):
        print(f"  image{i+1} node {IMAGE_NODES[i]} -> {r.name}", flush=True)
    print("  G23: K 型加速全开 + 背景坐标仍锁死（速度放主体/切镜，不放背景位移）", flush=True)
    print("  NEW [Shot 5]: ground-level wheel close-up, radial spoke streaks", flush=True)
    print("  G16: jump-kick-spin-explode chain still physically removed", flush=True)
    print("  G21: frontal axis lock on Lan Sun close-up; ref angle NOT inherited", flush=True)
    print("  G14: nose+headlights AT Lan Sun's chest; NEVER reverses / NEVER passes him", flush=True)
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
                raise RuntimeError(f"EP06 6-1a v5: FATAL submit refused (no retry): {msg}") from exc
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
        raise RuntimeError("EP06 6-1a v5: submit returned no data")

    task_id = str(data["taskId"])
    TASKID_FILE.write_text(task_id, encoding="utf-8")
    print(f"taskId = {task_id}", flush=True)
    print(f"taskId saved to {TASKID_FILE}", flush=True)
    print("SUBMIT DONE — poll/download with resume_ep06_6-1a_jinyu_v5.py, NEVER resubmit", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
