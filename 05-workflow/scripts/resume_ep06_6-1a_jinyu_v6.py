# -*- coding: utf-8 -*-
"""接续 EP06 6-1a 云端金鱼 v6 已提交任务：只轮询/下载/写回执，**不重新提交**。

G09：提交与轮询拆开。taskId 默认从 _jinyu_v6.taskid 读取，也可命令行传入。
本地进程断连／超时 ≠ 生成失败，只续轮询同一个 taskId，绝不二次提交。

用法：python resume_ep06_6-1a_jinyu_v6.py [taskId]
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
OUT = SEG / "视频草稿" / "EP06_6-1a_金鱼_v6.mp4"
RECEIPT = SEG / "RH任务回执_金鱼_EP06_6-1a_v6.json"
TASKID_FILE = SEG / "_jinyu_v6.taskid"
PROMPT = SEG / "金鱼_H3纯提示词_EP06_6-1a_v6.txt"


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
        raise RuntimeError("EP06 6-1a v6 resume: task done but no files")

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
        "unit": "EP06_6-1a_v6_jinyu",
        "versionNote": (
            "2026-11-15 用户『修改，陆沉不是在后座在副驾，开门跳车动作一气呵成，"
            "安娜拉着陆沉和陆沉从主驾跳出，然后抱着地上滚了几圈缓解冲击力』。"
            "撤回 v4/v5 的静态降级，恢复完整跳车动作链：陆沉写死 RIGHT FRONT 副驾"
            "（与安娜同排、正向位置锚，不写否定句），安娜 CLAMPS 手腕把他拉过中控，"
            "两人 EXIT TOGETHER through the SAME LEFT driver door，ONE unbroken take；"
            "落地 WRAPPED 抱团 ROLL TWO TO THREE 圈卸力，收势安娜护住他。"
            "G16 把 v5「STILL ON THE SEAT / REMAINS INSIDE / 只开门准备」物理清零；"
            "按 G24 二选一取人景同速（MOTION UNITY LOCK + INHERITING，背景随人物后退），"
            "不写 v5 与动作链互斥的 BACKGROUND LOCK / SAME screen coordinates；"
            "保留 K 型加速（G23）、车轮镜头、蓝隼正轴特写（G21）、AT Lan Sun（G14）。"
            "4951 bytes、6 标签、6 镜、3 图 0 音频、无 negativePrompt。一版反馈=一次生成。"
            "按 2026-11-15 新口径不写复盘/开发说明文档，交付列表只放视频。"
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
    print(json.dumps({"done": "EP06_6-1a_v6", "taskId": task_id,
                      "saved": [str(s) for s in saved]}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
