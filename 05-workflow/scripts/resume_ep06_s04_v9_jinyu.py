# -*- coding: utf-8 -*-
"""接续 EP06 S04 v9 云端金鱼已提交任务：只轮询/下载/写回执，**不重新提交**。

G09：提交与轮询拆开。taskId 默认从 _jinyu_s04_v9.taskid 读取，也可命令行传入。
本地进程断连／超时 ≠ 生成失败，只续轮询同一个 taskId，绝不二次提交。

用法：python resume_ep06_s04_v9_jinyu.py [taskId]
"""
from __future__ import annotations

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
SEG = ROOT / "05-workflow" / "ep06" / "全本批量_梅林"
OUT = SEG / "视频草稿" / "EP06_S04_v9_金鱼_电光瞬移_POV踢飞撞柱.mp4"
RECEIPT = SEG / "RH任务回执_金鱼_S04_v9.json"
TASKID_FILE = SEG / "_jinyu_s04_v9.taskid"
PROMPT = SEG / "提示词" / "金鱼_S04_v9_电光瞬移_POV踢飞撞柱.txt"


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
        raise RuntimeError("S04 v9 resume: task done but no files")

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
        "unit": "EP06_S04_v9_jinyu",
        "versionNote": (
            "2026-11-19 用户『蓝不要闪到背后，有个闪电电光瞬移特效，正面抓起安娜，"
            "后半不要消音，给男主红眼开眼特写动画，然后镜头为男主第一人称视角，"
            "看着蓝隼后背，抓住安娜的画面保持一致性，跑向蓝隼，然后被蓝侧身一脚踢开，"
            "手上还抓住安娜状态，男主被踢飞，撞上停车场柱子』。"
            "7 镜：电光瞬移正面抓安娜(/GRIP LOCK 跨镜继承) → 蓝隼正面台词特写 → "
            "陆沉红眼开眼特写 → 陆沉第一人称 POV 看蓝隼后背 → POV 冲刺 → "
            "蓝隼侧身踢(手不松安娜) → 陆沉撞黄黑条纹柱。"
            "4691 bytes、六标签、3 图 + 1 音频(蓝隼音色锁中文台词)、无 negativePrompt。"
            "一版反馈=一次生成；按 2026-11-15 新口径不写复盘/开发说明文档，交付只放视频。"
        ),
        "workflow": "金鱼云端",
        "appId": "2110357037929558018",
        "taskId": task_id,
        "status": final.get("status"),
        "usage": usage,
        "promptBytes": nbytes,
        "params": "16:9 / 15s / 1.5MP / simple / 12",
        "refs": [str(SEG / "安娜_凝刃战斗姿态_ref.png")],
        "audios": [str(ROOT / "05-workflow" / "归档素材" / "人物参考音色" / "蓝隼.wav")],
        "saved": [str(p) for p in saved],
    }
    RECEIPT.write_text(
        __import__("json").dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"receipt: {RECEIPT}", flush=True)
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
