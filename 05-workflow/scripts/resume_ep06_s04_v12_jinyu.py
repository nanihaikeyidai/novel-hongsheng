# -*- coding: utf-8 -*-
"""接续 EP06 S04 v12 云端金鱼已提交任务：只轮询/下载/写回执，**不重新提交**。

G09：提交与轮询拆开。taskId 默认从 _jinyu_s04_v12.taskid 读取，也可命令行传入。
本地进程断连／超时 ≠ 生成失败，只续轮询同一个 taskId，绝不二次提交。

用法：python resume_ep06_s04_v12_jinyu.py [taskId]
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
OUT = SEG / "视频草稿" / "EP06_S04_v12_金鱼_正面台词两步出拳踢胸口.mp4"
RECEIPT = SEG / "RH任务回执_金鱼_S04_v12.json"
TASKID_FILE = SEG / "_jinyu_s04_v12.taskid"
PROMPT = SEG / "提示词" / "金鱼_S04_v12_正面台词_两步出拳踢胸口.txt"


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
        raise RuntimeError("S04 v12 resume: task done but no files")

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
        "unit": "EP06_S04_v12_jinyu",
        "versionNote": (
            "2026-11-20 用户在 v11 基础上追加：『蓝隼说话时正面特写，不要仰拍；"
            "踢陆沉时手不要放开安娜，只是快速出脚侧踢到陆沉胸口，踢飞出去，动态高；"
            "陆沉跑两步马上出拳进攻特写，然后被踢飞』。"
            "相对 v11：说话特写从仰拍翻回 FULL FRONT 正面平视(eye-level/NO low angle/"
            "NO tilt up/双耳同框)，保留安娜挡光的 HARD SHADOW；出拳改 TWO QUICK STEPS "
            "短冲即出拳(非长距离跑)；踢击改 SNAPS fast SIDE KICK 至 CHEST、HIGH DYNAMIC/"
            "SPEED LINES、手全程不松安娜。"
            "5 镜：电光瞬移正面抓安娜 → 蓝隼正面平视+阴影台词 → 陆沉两步出拳(红眼) "
            "→ 冲峰值被快速侧踢胸口动量反转(手不松安娜) → 翻滚撞黄黑条纹柱。"
            "4812 bytes、六标签、4 图(含陆沉 G25) + 1 音频(蓝隼音色锁中文台词)、"
            "无 negativePrompt。一次反馈=一次生成；按 2026-11-15 新口径不写复盘/"
            "开发说明文档，交付只放视频。"
        ),
        "workflow": "金鱼云端",
        "appId": "2110357037929558018",
        "taskId": task_id,
        "status": final.get("status"),
        "usage": usage,
        "promptBytes": nbytes,
        "params": "16:9 / 15s / 1.5MP / simple / 12",
        "refs": [
            str(SEG / "安娜_凝刃战斗姿态_ref.png"),
            str(ROOT / "05-workflow" / "ep06" / "6-1a_跳车掀车" / "上传包_云端" / "ep06s01c_garage.png"),
            str(ROOT / "05-workflow" / "ep06" / "6-1a_跳车掀车" / "上传包_云端" / "ep06s01c_lansun_clean.png"),
            str(ROOT / "05-workflow" / "归档素材" / "人物" / "陆沉_人设.png"),
        ],
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
