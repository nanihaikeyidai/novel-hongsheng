# -*- coding: utf-8 -*-
"""接续 EP06 6-1a 云端金鱼 v4 已提交任务：只轮询/下载/写回执，**不重新提交**。

G09：提交与轮询拆开。taskId 默认从 _jinyu_v4.taskid 读取，也可命令行传入。
本地进程断连／超时 ≠ 生成失败，只续轮询同一个 taskId，绝不二次提交。

用法：python resume_ep06_6-1a_jinyu_v4.py [taskId]
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
OUT = SEG / "视频草稿" / "EP06_6-1a_金鱼_v4.mp4"
RECEIPT = SEG / "RH任务回执_金鱼_EP06_6-1a_v4.json"
TASKID_FILE = SEG / "_jinyu_v4.taskid"
PROMPT = SEG / "金鱼_H3纯提示词_EP06_6-1a_v4.txt"


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
        raise RuntimeError("EP06 6-1a v4 resume: task done but no files")

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
        "unit": "EP06_6-1a_v4_jinyu",
        "versionNote": (
            "2026-11-14 用户判 v3『不行，还是控制不住』→ 先出 6 宫格确认镜头理解 → "
            "用户『可以，生视频』＝该次已确认。v4 按 G19 静态降级：删除跳车/脚踢/空中旋转/"
            "落地爆炸整条动作链（G16 物理清零，连否定句都不写），全片只剩两扇前门打开、"
            "蓝隼邪恶笑容特写、车迎面逼近三类可静止状态；STATIC SHOT LOCK 每镜 FIXED 机位、"
            "柱子灯管停车线逐帧同屏幕坐标（用户『背景不用动』，与 G17 互斥，K 型加速词清零）；"
            "FRONT-FACING LOCK 蓝隼每镜 FULL FRONT VIEW 正对来车；安娜主驾 LEFT、陆沉副驾 RIGHT，"
            "二人 hips STILL ON THE SEAT / REMAINS INSIDE，只开门不跳车。"
            "4937 bytes、6 标签、5 镜、3 图 0 音频、无 negativePrompt。一版反馈=一次生成。"
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
    print(json.dumps({"done": "EP06_6-1a_v4", "taskId": task_id,
                      "saved": [str(s) for s in saved]}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
