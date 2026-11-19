# -*- coding: utf-8 -*-
"""接续 EP06 6-1a 云端金鱼 v1 已提交任务：只轮询/下载/写回执，**不重新提交**。

背景：2026-11-12 23:5x 首次提交脚本已成功提交并上传三张图，
      taskId = 2120912562534178818；本地轮询进程被命令超时 SIGTERM 杀掉，
      服务端任务仍在 RUNNING。按「一次反馈=一次生成」硬规则，
      绝不二次提交，只接续同一个 taskId。

用法：python resume_ep06_6-1a_jinyu_v1.py [taskId]
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
OUT = SEG / "视频草稿" / "EP06_6-1a_金鱼_v1.mp4"
RECEIPT = SEG / "RH任务回执_金鱼_EP06_6-1a_v1.json"
DEFAULT_TASK_ID = "2120912562534178818"


def main() -> int:
    task_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TASK_ID
    api_key = require_api_key(
        os.environ.get("RH_API_KEY") or os.environ.get("RUNNINGHUB_API_KEY")
    )
    print(f"=== RESUME ONLY (no resubmit) taskId={task_id} ===", flush=True)

    final = poll_task(api_key, task_id)
    results = final.get("results") or []
    if not results:
        raise RuntimeError("EP06 6-1a resume: task done but no files")

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
            "不含 negativePrompt 段与任何事故形态负向词。一次反馈=一次生成，未迭代第二版。"
            "首次提交脚本本地轮询被超时中断，本回执由 resume 脚本接续同一 taskId 补齐，未二次提交"
        ),
        "workflow": "金鱼云端",
        "appId": "2110357037929558018",
        "taskId": task_id,
        "status": final.get("status"),
        "usage": usage,
        "promptBytes": 4957,
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
    print(json.dumps({"done": "EP06_6-1a_v1", "taskId": task_id,
                      "saved": [str(s) for s in saved]}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
