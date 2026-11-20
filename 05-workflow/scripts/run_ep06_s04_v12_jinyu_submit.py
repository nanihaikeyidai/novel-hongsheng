# -*- coding: utf-8 -*-
"""EP06 S04 v12｜云端金鱼 H3 提交（基于 v9b 成功版优化）。

触发：2026-11-19 用户「用云端金鱼重新生成一下，蓝隼应该闪身到安娜正面，面对面
而不是到安娜背后，蓝隼脸部特写的时候应该有阴影，是抬头45度向上看的状态，因为
安娜脸挡住光了，陆沉不要距离这么远跑过来，应该是出拳攻击的特写动画」+「安娜
应该双手抓住蓝隼的手臂缓解自己的压力」。

v9b（本地四图六镜）为成功版：加陆沉第4图 + 压镜数解决"同一男模覆盖全场"。
本版沿用其四图链路，把 4 项修改并入，改走云端金鱼（余额已恢复 2030 点）。

一次反馈＝一版＝一次生成：提交 1 次，失败不自动重试非可重试错误；提交与轮询拆开
（G09），断连只续轮询同一 taskId，绝不二次提交。按 2026-11-15 新口径：不写复盘／
开发说明文档，验收结论只在对话里给，交付列表只放视频。

提示词：金鱼_S04_v12_正面台词_两步出拳踢胸口.txt（4980 bytes，六标签，4 图 + 1 音频）。
参考槽位（G05/G25）：51=<Picture 1> 安娜凝刃 / 49=<Picture 2> 车库 /
50=<Picture 3> 蓝隼 / 43=<Picture 4> 陆沉白衬衫正面（G25 缺锚覆盖）。
音频槽 48=<Audio 1> 蓝隼音色（锁中文台词）。
应用 2110357037929558018｜16:9 / 15s / 1.5MP / simple / 12 步 → 1664×928。
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
SEG = ROOT / "05-workflow" / "ep06" / "全本批量_梅林"
PACK = ROOT / "05-workflow" / "ep06" / "6-1a_跳车掀车" / "上传包_云端"
VOICE = ROOT / "05-workflow" / "归档素材" / "人物参考音色"
ARCH = ROOT / "05-workflow" / "归档素材" / "人物"

PROMPT = SEG / "提示词" / "金鱼_S04_v12_正面台词_两步出拳踢胸口.txt"
REFS = [
    SEG / "安娜_凝刃战斗姿态_ref.png",        # 51 -> <Picture 1>
    PACK / "ep06s01c_garage.png",                 # 49 -> <Picture 2>
    PACK / "ep06s01c_lansun_clean.png",           # 50 -> <Picture 3>
    ARCH / "陆沉_人设.png",                       # 43 -> <Picture 4> (G25)
]
AUDIOS = [
    VOICE / "蓝隼.wav",                           # 48 -> <Audio 1>
]
IMAGE_NODES = ("51", "49", "50", "43")
AUDIO_NODES = ("48",)
TASKID_FILE = SEG / "_jinyu_s04_v12.taskid"

HARD_LOCKS = (
    "MOTION UNITY LOCK", "INHERITING", "ONE motion system",
    "SPEED LOCK", "MOUTH LOCK", "GRIP LOCK",
    "WHITE MASK", "COMPLETELY STILL", "blade-ready combat stance",
    "ELECTRIC-BLUE", "NEVER removed", "FACE-TO-FACE",
    "ZERO travel", "BOTH hands", "RELIEVE throat pressure",
    "FULL FRONT", "eye-level", "NO low angle", "NO tilt up", "sunglasses EQUAL width", "HARD SHADOW",
    "PUNCH CLOSE-UP", "NOT a long-distance run",
    "SIDE KICK", "NEVER releases Anna's throat",
    "SMASHES into a YELLOW-BLACK STRIPED CONCRETE PILLAR",
    "irises FLARE BRILLIANT RED", "CRACKLING BLUE-WHITE LIGHTNING",
    "TWO QUICK STEPS", "INSTANT PUNCH", "SURGING IN", "SNAPS ONE fast SIDE KICK", "CHEST",
    "HIGH DYNAMIC", "SPEED LINES", "REVERSES his momentum", "BLASTED flying",
    "<d>[Chinese]",
)


def main() -> int:
    if os.environ.get("S04_V12_JINYU_CONFIRMED") != "1":
        raise SystemExit(
            "S04 v12 金鱼: 未获确认，拒绝提交视频生成（约 76-95 积分，POINT 结算）。"
            "确认后请设 S04_V12_JINYU_CONFIRMED=1 再运行。"
        )
    api_key = require_api_key(
        os.environ.get("RH_API_KEY") or os.environ.get("RUNNINGHUB_API_KEY")
    )

    # 提交前余额预检：付费积分 < 单次预估下限(76) 即提前拦下，避免 821 白重试。
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
    ESTIMATE_MIN_POINT = 76.0
    if _point <= 0 and _money <= 0:
        raise SystemExit(
            "S04 v12 金鱼: 付费积分与钱包余额均为 0，RunningHub 会返回 821。未提交、0 消耗。"
            "请充值后重跑：https://www.runninghub.cn/vip-rights/4"
        )
    if 0 < _point < ESTIMATE_MIN_POINT:
        raise SystemExit(
            f"S04 v12 金鱼: 付费积分 {_point} < 单次预估下限 {ESTIMATE_MIN_POINT:.0f}，"
            "RunningHub 会返回 821「付费积分余额不足」。未提交、0 消耗、无 taskId。"
            f"当前差约 {ESTIMATE_MIN_POINT - _point:.0f} 点。请充值后重跑："
            "https://www.runninghub.cn/vip-rights/4"
        )

    prompt = PROMPT.read_text(encoding="utf-8").strip()
    labels = [
        "subject_definitions:", "summary:", "retention_analysis:",
        "detailed_description:", "overall_soundscape:", "non_diegetic_music:",
    ]
    pos = [prompt.find(l) for l in labels]
    if any(i < 0 for i in pos) or pos != sorted(pos) or not prompt.startswith("subject_definitions:"):
        raise ValueError("S04 v12: H3 gate failed (6 labels order)")
    nbytes = len(prompt.encode("utf-8"))
    if nbytes > 5000:
        raise ValueError(f"S04 v12: prompt too long {nbytes} bytes")
    pics = set(re.findall(r"<Picture (\d+)>", prompt))
    if pics != {str(i + 1) for i in range(len(REFS))}:
        raise ValueError(f"S04 v12: picture mismatch prompt={pics} bound={len(REFS)}")
    declared = len(set(re.findall(r"<Audio (\d+)>", prompt)))
    if declared != len(AUDIOS):
        raise ValueError(f"S04 v12: audio mismatch prompt={declared} bound={len(AUDIOS)}")
    for hard in HARD_LOCKS:
        if hard not in prompt:
            raise ValueError(f"S04 v12: missing hard lock: {hard}")
    for f in REFS + AUDIOS:
        if not f.exists():
            raise FileNotFoundError(f"S04 v12: missing asset {f}")
    if TASKID_FILE.exists():
        raise SystemExit(
            f"S04 v12: taskId 已存在 ({TASKID_FILE.read_text(encoding='utf-8').strip()})，"
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
        f"=== EP06 S04 v12 正面台词+两步出拳+踢胸口高动态 | 云端金鱼 {APP_ID} | "
        f"{nbytes} bytes | 15s | 1.5MP | 12 steps | 4 img 1 audio ===",
        flush=True,
    )
    for i, r in enumerate(REFS):
        print(f"  image{i+1} node {IMAGE_NODES[i]} -> {r.name}", flush=True)
    for i, a in enumerate(AUDIOS):
        print(f"  audio{i+1} node {AUDIO_NODES[i]} -> {a.name}", flush=True)
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
                "invalid_key", "unauthorized", "401", "403", "not enough", "821",
            ))
            if fatal:
                raise RuntimeError(f"S04 v12: FATAL submit refused (no retry): {msg}") from exc
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
        raise RuntimeError("S04 v12: submit returned no data")

    task_id = str(data["taskId"])
    TASKID_FILE.write_text(task_id, encoding="utf-8")
    print(f"taskId = {task_id}", flush=True)
    print(f"taskId saved to {TASKID_FILE}", flush=True)
    print("SUBMIT DONE — poll/download with resume script, NEVER resubmit", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
