# -*- coding: utf-8 -*-
"""EP06 6-1a｜云端金鱼 H3 提交（v6 · 完整跳车动作链）。

触发：2026-11-15 用户「修改，陆沉不是在后座在副驾，开门跳车动作一气呵成，
安娜拉着陆沉和陆沉从主驾跳出，然后抱着地上滚了几圈缓解冲击力」。
按「一次反馈＝一版修改＝一次生成」视为该次已确认，报点数后**只提交 1 次**。

v6 相对 v5（撤回静态降级，恢复完整动作链）：
  1) 座位写死：Anna DRIVER / LEFT FRONT seat；Lu Chen FRONT PASSENGER /
     RIGHT FRONT seat, SAME front row as Anna（用户「不是在后座在副驾」）。
     用正向位置锚（仪表盘在膝前／挡风玻璃在正前／与安娜同排），不写否定句（A 型）。
  2) 恢复跳车：G16 把 v5 的「STILL ON THE SEAT / REMAINS INSIDE / stay SEATED /
     只开门准备」全部物理清零并列入 BANNED。
  3) 同侧跳出：Anna CLAMPS Lu Chen's wrist + PULLS him across the centre console，
     两人 EXIT TOGETHER through that SAME LEFT front door（主驾侧），
     ONE single continuous unbroken motion / ONE unbroken take（一气呵成）。
  4) 抱团滚：Anna's arms WRAPPED around Lu Chen, ROLL TWO TO THREE full turns
     across the wet floor to bleed off the impact, 收势 Anna shielding him。
  5) 运动锁按 G24 二选一取「人景同速」：MOTION UNITY LOCK + INHERITING（G17），
     背景随人物滚动按同一速度后退。不写 v5 的 BACKGROUND LOCK / SAME screen
     coordinates —— 完整跳车＋滚地动作链与「背景绝对不动」在生成层互斥（v5 已证）。
  6) 保留未撤回口径：K 型加速锚点（G23）、车轮加速镜头、蓝隼正轴特写（G21）、
     DIRECTION LOCK 车头 AT 蓝隼胸口 / NEVER reverses / BEFORE contact（G14）、
     冷蓝灰日漫、3 图 0 音频。
  7) 不恢复踢／翻／爆炸（用户本轮未要求），仍列 BANNED。

闸门 EP06_6_1A_V6_CONFIRMED=1；提交与轮询拆开（G09），断连只续轮询同一
taskId，绝不二次提交。按 2026-11-15 新口径：不写复盘／开发说明文档，
验收结论只在对话里给，交付列表只放视频。

参考槽位（G05）：51=<Picture 1> 安娜 / 49=<Picture 2> 车库 / 50=<Picture 3> 蓝隼。
48/14/15 音频槽默认 None；本段 0 台词不绑音频（P02 先例、G13）。
素材沿用 `上传包_云端/` 三张已验收图；**宫格图不得喂进 <Picture N>**。

应用 2110357037929558018｜16:9 / 15s / 1.5MP / simple / 12 步 → 1664×928。
预估约 76–85 积分，实际以回执 usage.settleMode 为准（G12）。
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

PROMPT = SEG / "金鱼_H3纯提示词_EP06_6-1a_v6.txt"
REFS = [
    PACK / "ep06s01c_anna.png",           # 51 -> <Picture 1>
    PACK / "ep06s01c_garage.png",         # 49 -> <Picture 2>
    PACK / "ep06s01c_lansun_clean.png",   # 50 -> <Picture 3>
]
AUDIOS: list[Path] = []
IMAGE_NODES = ("51", "49", "50")
AUDIO_NODES: tuple[str, ...] = ()
TASKID_FILE = SEG / "_jinyu_v6.taskid"

HARD_LOCKS = (
    "SETTING FIRST", "MOTION UNITY LOCK", "INHERITING", "ONE motion system",
    "SPEED LOCK", "ACCELERATES HARD", "SPEED LINES", "GROWS LARGER",
    "SHRINKS FASTER", "radial streaks", "motion blur", "cuts get SHORTER",
    "DIRECTION LOCK", "AT Lan Sun", "FULL FRONT VIEW",
    "CAMERA ON HIS CENTRAL AXIS", "BOTH EARS VISIBLE", "lenses EQUAL width",
    "NEVER reverses", "NEVER passes him", "BEFORE contact",
    "WINDSHIELD INTERIOR POV", "GROUND-LEVEL WHEEL CLOSE-UP",
    "WIDE SINISTER SMIRK", "NEVER removed", "BLUE-BLACK", "ZERO dialogue",
    "DO NOT inherit its camera angle", "URGENT", "RISING in pitch",
    "LEFT FRONT seat", "RIGHT FRONT seat", "SAME front row",
    "GRABS", "CLAMPS", "PULLS", "EXIT TOGETHER", "SAME LEFT front door",
    "ONE single continuous unbroken motion", "ONE unbroken take",
    "WRAPPED", "ROLL TWO TO THREE", "bleed off the impact", "shielding him",
    "landing thud", "ROLLING friction",
)
# G16：v5 静态降级词物理清零 + v5 自相矛盾背景锁清零 + 旧踢/翻/爆炸 + A 型事故形态
BANNED = (
    "back seat", "rear seat", "STILL ON THE SEAT", "REMAINS INSIDE",
    "stay SEATED", "STATIC SHOT LOCK", "BACKGROUND LOCK",
    "SAME screen coordinates", "no background drift",
    "still tension", "Hold >=", "MOTIONLESS", "slow motion", "gentle",
    "steady", "quiet", "coasts", "rolls forward", "freeze frames",
    "no speed lines", "no motion blur", "cuts carry the timeline",
    "punch", "fist", "kick", "right boot lands", "spinning", "corkscrew",
    "EXPLODES", "explosion", "WHITE-hot flash", "BLUE-WHITE shockwave",
    "BLACK smoke", "bail", "leap", "jump", "tumble", "roll out",
    "piano", "musical instrument", "wooden", "energy thread",
    "negativePrompt", "SALE",
)


def main() -> int:
    if os.environ.get("EP06_6_1A_V6_CONFIRMED") != "1":
        raise SystemExit(
            "EP06 6-1a v6: 未获确认，拒绝提交视频生成（约 76-85 积分，POINT 结算）。"
            "用户已确认后请设 EP06_6_1A_V6_CONFIRMED=1 再运行。"
        )
    api_key = require_api_key(
        os.environ.get("RH_API_KEY") or os.environ.get("RUNNINGHUB_API_KEY")
    )

    # 提交前余额预检（2026-11-15 补）：付费积分耗尽时 submit 返回 821，但
    # _rh_call 的 sys.exit trap 会把原始错误文案丢成 "RH_API_EXIT code=1"，
    # 于是脚本按可重试错误处理、白等 6 分钟。这里直接查账户状态提前拦下。
    # 判据用 remainPoint + remainMoney 双零，不看 remainCoins（G12：金币 0
    # 时仍可能按 POINT 结算跑通，不能据此拒绝提交）。
    import json as _json
    import runninghub as _rh

    _resp = _rh.curl_post_json(
        _rh.ACCOUNT_STATUS_URL, {"apikey": api_key},
        {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        timeout=15,
    )
    try:
        _acc = _json.loads(_resp.stdout).get("data") or {}
    except Exception:  # noqa: BLE001
        _acc = {}
    _point = float(_acc.get("remainPoint") or 0)
    _money = float(_acc.get("remainMoney") or 0)
    print(f"account: remainPoint={_point} remainMoney={_money} "
          f"remainCoins={_acc.get('remainCoins')} "
          f"runningTasks={_acc.get('currentTaskCounts')}", flush=True)
    if _point <= 0 and _money <= 0:
        raise SystemExit(
            "EP06 6-1a v6: 付费积分与钱包余额均为 0，RunningHub 会返回 821 "
            "「付费积分余额不足，消费级 API 调用仅支持使用付费积分，"
            "免费积分不可用于 API 调用」。未提交任何任务、0 消耗。"
            "请充值后重新运行本脚本：https://www.runninghub.cn/vip-rights/4"
        )

    prompt = PROMPT.read_text(encoding="utf-8").strip()
    labels = [
        "subject_definitions:", "summary:", "retention_analysis:",
        "detailed_description:", "overall_soundscape:", "non_diegetic_music:",
    ]
    pos = [prompt.find(l) for l in labels]
    if any(i < 0 for i in pos) or pos != sorted(pos) or not prompt.startswith("subject_definitions:"):
        raise ValueError("EP06 6-1a v6: H3 gate failed (6 labels order)")
    nbytes = len(prompt.encode("utf-8"))
    if nbytes > 5000:
        raise ValueError(f"EP06 6-1a v6: prompt too long {nbytes} bytes")
    pics = set(re.findall(r"<Picture (\d+)>", prompt))
    if pics != {str(i + 1) for i in range(len(REFS))}:
        raise ValueError(f"EP06 6-1a v6: picture mismatch prompt={pics} bound={len(REFS)}")
    declared = len(set(re.findall(r"<Audio (\d+)>", prompt)))
    if declared != len(AUDIOS):
        raise ValueError(f"EP06 6-1a v6: audio mismatch prompt={declared} bound={len(AUDIOS)}")
    for stale in BANNED:
        if stale.lower() in prompt.lower():
            raise ValueError(f"EP06 6-1a v6: banned concept/word: {stale}")
    for hard in HARD_LOCKS:
        if hard not in prompt:
            raise ValueError(f"EP06 6-1a v6: missing hard lock: {hard}")
    if prompt.count("AT Lan Sun") < 2:
        raise ValueError("EP06 6-1a v6: direction anchor to person missing")
    if len(re.findall(r"\[Shot \d+\]", prompt)) != 6:
        raise ValueError("EP06 6-1a v6: expected 6 shots")
    for f in REFS + AUDIOS:
        if not f.exists():
            raise FileNotFoundError(f"EP06 6-1a v6: missing asset {f}")
    if TASKID_FILE.exists():
        raise SystemExit(
            f"EP06 6-1a v6: taskId 已存在 ({TASKID_FILE.read_text(encoding='utf-8').strip()})，"
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
        f"=== EP06 6-1a v6 完整跳车动作链 | 云端金鱼 {APP_ID} | "
        f"{nbytes} bytes | 15s | 1.5MP | 12 steps | 0 audio ===",
        flush=True,
    )
    for i, r in enumerate(REFS):
        print(f"  image{i+1} node {IMAGE_NODES[i]} -> {r.name}", flush=True)
    print("  SEAT: Lu Chen RIGHT FRONT passenger, SAME front row as Anna (not back seat)", flush=True)
    print("  EXIT: Anna CLAMPS his wrist, both EXIT TOGETHER through the SAME LEFT driver door", flush=True)
    print("  ROLL: WRAPPED together, ROLL TWO TO THREE turns to bleed off the impact", flush=True)
    print("  G16: v5 'stay seated / only open door' chain physically removed", flush=True)
    print("  G24: MOTION UNITY LOCK chosen (background recedes with the pair), no SAME-coords lock", flush=True)
    print("  G23: K-type acceleration anchors kept; G21 frontal axis; G14 AT Lan Sun", flush=True)
    print("  estimated ~76-85 POINT (usage receipt wins, G12)", flush=True)

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
                raise RuntimeError(f"EP06 6-1a v6: FATAL submit refused (no retry): {msg}") from exc
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
        raise RuntimeError("EP06 6-1a v6: submit returned no data")

    task_id = str(data["taskId"])
    TASKID_FILE.write_text(task_id, encoding="utf-8")
    print(f"taskId = {task_id}", flush=True)
    print(f"taskId saved to {TASKID_FILE}", flush=True)
    print("SUBMIT DONE — poll/download with resume_ep06_6-1a_jinyu_v6.py, NEVER resubmit", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
