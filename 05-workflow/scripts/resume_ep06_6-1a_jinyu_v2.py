# -*- coding: utf-8 -*-
"""接续 EP06 6-1a 云端金鱼 v2 已提交任务：只轮询/下载/写回执，**不重新提交**。

G09：提交与轮询拆开。taskId 默认从 _jinyu_v2.taskid 读取，也可命令行传入。
本地进程断连／超时 ≠ 生成失败，只续轮询同一个 taskId，绝不二次提交。

用法：python resume_ep06_6-1a_jinyu_v2.py [taskId]
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
OUT = SEG / "视频草稿" / "EP06_6-1a_金鱼_v2.mp4"
RECEIPT = SEG / "RH任务回执_金鱼_EP06_6-1a_v2.json"
TASKID_FILE = SEG / "_jinyu_v2.taskid"
PROMPT = SEG / "金鱼_H3纯提示词_EP06_6-1a_v2.txt"


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
        raise RuntimeError("EP06 6-1a v2 resume: task done but no files")

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
        "unit": "EP06_6-1a_v2_jinyu",
        "versionNote": (
            "v2 修正 v1 不合格：方向锁改锚在蓝隼身上（NOSE/headlights AT Lan Sun、"
            "headlight cone、bumper→boots gap SHRINKS、每镜 LOW three-quarter FRONT-SIDE 同框），"
            "不再用『画面深处/坡道』相机坐标；按避坑手册 K 型约束块 9 补满 ACCELERATES HARD / "
            "SPEED LINES / motion blur / GROWS LARGER / cuts get SHORTER 并删净 coasts/rolls/"
            "MOTIONLESS/fixed/Hold；掀翻改为 ONE SINGLE PUNCH → ENTIRE car LAUNCHED / "
            "all four wheels leaving / half-turn in mid-air。4987 bytes，6 标签，"
            "3 图 0 音频，无 negativePrompt 段与事故形态负向词。一次反馈=一次生成，未迭代第三版"
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
    print(json.dumps({"done": "EP06_6-1a_v2", "taskId": task_id,
                      "saved": [str(s) for s in saved]}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
