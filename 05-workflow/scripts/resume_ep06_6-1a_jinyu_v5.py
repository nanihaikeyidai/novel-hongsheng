# -*- coding: utf-8 -*-
"""接续 EP06 6-1a 云端金鱼 v5 已提交任务：只轮询/下载/写回执，**不重新提交**。

G09：提交与轮询拆开。taskId 默认从 _jinyu_v5.taskid 读取，也可命令行传入。
本地进程断连／超时 ≠ 生成失败，只续轮询同一个 taskId，绝不二次提交。

用法：python resume_ep06_6-1a_jinyu_v5.py [taskId]
"""
from __future__ import annotations

import json
import os
import subprocess as _sp
import sys
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

from runninghub import download_file, fix_mov_to_mp4, poll_task, require_api_key  # noqa: E402

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳")
SEG = ROOT / "05-workflow" / "ep06" / "6-1a_跳车掀车"
OUT = SEG / "视频草稿" / "EP06_6-1a_金鱼_v5.mp4"
RECEIPT = SEG / "RH任务回执_金鱼_EP06_6-1a_v5.json"
TASKID_FILE = SEG / "_jinyu_v5.taskid"
PROMPT = SEG / "金鱼_H3纯提示词_EP06_6-1a_v5.txt"


def main() -> int:
    if len(sys.argv) > 1:
        task_id = sys.argv[1]
    elif TASKID_FILE.exists():
        task_id = TASKID_FILE.read_text(encoding="utf-8").strip()
    else:
        raise SystemExit("no taskId: pass it as argv[1] or run submit script first")
    if not task_id:
        raise SystemExit("empty taskId")

    api_key = require_api_key(
        os.environ.get("RH_API_KEY") or os.environ.get("RUNNINGHUB_API_KEY")
    )
    nbytes = len(PROMPT.read_text(encoding="utf-8").strip().encode("utf-8"))
    print(f"=== RESUME ONLY (no resubmit) taskId={task_id} ===", flush=True)

    final = poll_task(api_key, task_id)
    results = final.get("results") or []
    if not results:
        raise RuntimeError("EP06 6-1a v5 resume: task done but no files")

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
        "unit": "EP06_6-1a_v5_jinyu",
        "versionNote": (
            "2026-11-14 用户判 v4『动作太慢了，动作要快，车速也要快，加速撞的感觉，"
            "要夸张点增加速度赶，给一个车轮加速的镜头，现在是慢吞吞开过去』。"
            "按 G20 本应先出加速版 6 宫格，用户主动取消出图并选择『直接生成 v5 视频』"
            "＝该次已确认；本轮 G20 由用户豁免，留痕在复盘。"
            "v5 是口径反转：恢复 K 型全部加速锚点（ACCELERATES HARD / SPEED LINES / "
            "motion blur / GROWS LARGER / SHRINKS FASTER / cuts get SHORTER / radial streaks），"
            "但 BACKGROUND LOCK 仍锁柱子灯管停车线逐帧同屏幕坐标（用户『背景不用动』未撤回），"
            "速度线只贴车身/轮拱/地面反光带，不写 9b 的 MOTION UNITY LOCK；"
            "新增 [Shot 5] 贴地车轮加速特写，末镜内 3 个短拍切回同机位；"
            "动作链仍按 G19 降级（不跳车/不踢/不翻/不爆炸，G16 物理清零），门 SNAP open IN ONE BEAT；"
            "G21 蓝隼特写补机位层正轴锁、参考图声明不继承 3/4 侧角度；"
            "G14 车头双灯 AT 蓝隼胸口，NEVER reverses / NEVER passes him。"
            "4983 bytes、6 标签、6 镜、3 图 0 音频、无 negativePrompt。一版反馈=一次生成。"
        ),
        "workflow": "金鱼云端",
        "appId": "2110357037929558018",
        "taskId": task_id,
        "status": final.get("status"),
        "usage": usage,
        "promptBytes": nbytes,
        "params": "16:9 / 15s / 1.5MP / simple / 12",
        "refs": [
            str(SEG / "上传包_云端" / "ep06s01c_anna.png"),
            str(SEG / "上传包_云端" / "ep06s01c_garage.png"),
            str(SEG / "上传包_云端" / "ep06s01c_lansun_clean.png"),
        ],
        "audios": [],
        "nodes": {"prompt": "263", "images": ["51", "49", "50"], "audios": []},
        "saved": [str(s) for s in saved],
        "tlsFix": "curl --ssl-no-revoke (Schannel CRYPT_E_REVOCATION_OFFLINE)",
        "resumed": True,
    }
    RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"done": "EP06_6-1a_v5", "taskId": task_id,
                      "saved": [str(s) for s in saved]}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
