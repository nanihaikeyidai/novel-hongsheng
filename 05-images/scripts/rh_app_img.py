#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《红绳》生图通道适配层 — RunningHub AI 应用版（2026-10-12 新增）

背景（第 12 轮实测）
-------------------
- 65535.space：Key 依旧 `401 invalid_api_key`，旧端点 `img-cn` 仍 502 → 不可用。
- RunningHub **标准模型** 文生图：33/33 全部被拦（30×`40310` CN 合规下线、6×`1014` 需企业级 Key）
  → 不可用（apiType=NORMAL）。
- RunningHub **AI 应用**（webapp，走 `/task/openapi/ai-app/run`，消耗 coins）：
  ✅ **可用**。这是本项目唯一未枯竭的生图通道。

本模块把 AI 应用封装成"给提示词 → 出图"的简单接口，
与 `img_api.py`（65535.space 适配层）保持同样的调用手感。

已核实的文生图应用（`rh app info` 实测节点）
--------------------------------------------
| webappId            | 标题                             | 节点 | 关键字段 |
|---------------------|----------------------------------|------|----------|
| 2097866022547181570 | 全能图片G-image-2.5文生图高品质版 | `1`  | prompt / quality / resolution / aspectRatio / background / outputFormat |

关键字段取值（实测 fieldData 默认值）
    quality      high
    resolution   2k
    aspectRatio  16:9        ← 符合《红绳》强制 16:9 横屏
    outputFormat png

环境变量
--------
    RH_API_KEY     必填（本机已有）。也接受 RUNNINGHUB_API_KEY。
    RH_IMG_WEBAPP  可选。默认 2097866022547181570

用法
----
    python scripts/rh_app_img.py --check              # 只读自检，不花钱
    python scripts/rh_app_img.py --prompt-file p.txt  # 跑一条提示词并下载
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

API_HOST = "https://www.runninghub.cn"
SUBMIT_URL = f"{API_HOST}/task/openapi/ai-app/run"
NODE_INFO_URL = f"{API_HOST}/api/webapp/apiCallDemo"
POLL_URL = f"{API_HOST}/openapi/v2/query"
ACCOUNT_URL = f"{API_HOST}/uc/openapi/accountStatus"

DEFAULT_WEBAPP = "2097866022547181570"   # 全能图片G-image-2.5文生图高品质版
PROMPT_NODE = "1"

POLL_INTERVAL = 3
MAX_POLL_SECONDS = 1200

# 账本：所有提交的 taskId 立即落盘，避免超时丢号（第 12 轮踩过这个坑）
LEDGER = Path(__file__).resolve().parent.parent.parent / "03-intermediate" / "api_probe" / "r12" / "rh_img_tasks.jsonl"


class RhImgError(RuntimeError):
    pass


def api_key() -> str:
    for name in ("RH_API_KEY", "RUNNINGHUB_API_KEY"):
        v = os.environ.get(name)
        if v:
            return v.strip()
    raise RhImgError("未找到 RH_API_KEY / RUNNINGHUB_API_KEY 环境变量。")


def _headers(key):
    # RunningHub 鉴权实测：轮询/查询走 Authorization: Bearer，
    # 提交走 body 里的 apiKey。二者混用会 401（第 12 轮踩过）。
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _post(url, payload, key, timeout=60, bearer=True):
    body = dict(payload)
    r = requests.post(url, json=body, headers=_headers(key) if bearer else None, timeout=timeout)
    if r.status_code != 200:
        raise RhImgError(f"HTTP {r.status_code} @ {url}: {r.text[:200]}")
    return r.json()


def _ledger(task_id, webapp, note=""):
    try:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                                 "taskId": task_id, "webappId": webapp, "note": note},
                                ensure_ascii=False) + "\n")
    except Exception:
        pass


def account_status(key=None):
    key = key or api_key()
    r = requests.post(ACCOUNT_URL, json={"apikey": key}, timeout=30)
    r.raise_for_status()
    return r.json().get("data", {})


def node_info(webapp=DEFAULT_WEBAPP, key=None):
    key = key or api_key()
    r = requests.get(NODE_INFO_URL, params={"apiKey": key, "webappId": webapp},
                     headers={"Authorization": f"Bearer {key}"}, timeout=30)
    r.raise_for_status()
    j = r.json()
    if j.get("code") != 0:
        raise RhImgError(f"获取节点失败: {j.get('msg')}")
    nodes = j.get("data", {}).get("nodeInfoList", [])
    if not nodes:
        raise RhImgError("该应用未返回可修改节点（需先在网页端成功运行一次）。")
    return nodes


def build_node_list(webapp, prompt, aspect="16:9", resolution="2k",
                    quality="high", fmt="png", background="auto", key=None):
    """按应用当前线上节点重建 nodeInfoList —— 不硬编码，逐字段对齐实测 fieldName。"""
    nodes = node_info(webapp, key=key)
    wanted = {
        "prompt": prompt,
        "aspectRatio": aspect,
        "resolution": resolution,
        "quality": quality,
        "outputFormat": fmt,
        "background": background,
    }
    out = []
    seen = set()
    for n in nodes:
        fn = n.get("fieldName")
        if fn in wanted and fn not in seen:
            out.append({
                "nodeId": str(n.get("nodeId")),
                "fieldName": fn,
                "fieldValue": wanted[fn],
            })
            seen.add(fn)
        else:
            out.append({
                "nodeId": str(n.get("nodeId")),
                "fieldName": fn,
                "fieldValue": n.get("fieldValue"),
            })
    missing = [k for k in ("prompt", "aspectRatio") if k not in seen]
    if missing:
        raise RhImgError(f"应用节点表缺少必需字段 {missing}；实际字段：{[n.get('fieldName') for n in nodes]}")
    return out


def submit(webapp, node_list, key=None):
    # 与 rh_cli/app/client.py 一致：提交时 apiKey 放 body，不带 Bearer 头
    k = key or api_key()
    j = _post(SUBMIT_URL, {"apiKey": k, "webappId": int(webapp), "nodeInfoList": node_list}, k)
    if j.get("code") != 0:
        raise RhImgError(f"提交失败 code={j.get('code')} msg={j.get('msg')} detail={str(j)[:300]}")
    data = j.get("data", {})
    tid = data.get("taskId")
    if not tid:
        raise RhImgError(f"提交成功但无 taskId: {str(j)[:300]}")
    _ledger(str(tid), webapp, note="submitted")
    return str(tid), data


def poll(task_id, key=None, on_tick=None):
    key = key or api_key()
    elapsed = 0
    while elapsed < MAX_POLL_SECONDS:
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        try:
            j = _post(POLL_URL, {"taskId": task_id}, key)   # Bearer 头
        except RhImgError as e:
            if on_tick:
                on_tick(elapsed, f"RETRY {e}")
            continue
        status = j.get("status", "UNKNOWN")
        if on_tick:
            on_tick(elapsed, status)
        if status in ("SUCCESS", "SUCCEED", "DONE"):
            return j
        if status in ("FAILED", "ERROR"):
            raise RhImgError(f"任务失败: {str(j)[:300]}")
    raise RhImgError(f"轮询超时（{MAX_POLL_SECONDS}s）")


def result_urls(final):
    urls = []
    for item in (final.get("results") or []):
        u = item.get("url") or item.get("outputUrl")
        if u:
            urls.append((str(u), str(item.get("outputType") or "png")))
    return urls


def download(url, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def generate(prompt, dest: Path, webapp=DEFAULT_WEBAPP, aspect="16:9",
             resolution="2k", quality="high", fmt="png", key=None):
    """一条提示词 → 一张图 → 落盘。返回 (ok, info)。"""
    k = key or api_key()
    nodes = build_node_list(webapp, prompt, aspect, resolution, quality, fmt, key=k)
    tid, data = submit(webapp, nodes, key=k)
    final = poll(tid, key=k)
    urls = result_urls(final)
    if not urls:
        raise RhImgError(f"任务完成但无结果 URL: {str(final)[:300]}")
    download(urls[0][0], dest)
    usage = final.get("usage") or {}
    return dest, {"taskId": tid, "url": urls[0][0], "usage": usage}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只读自检，不花钱")
    ap.add_argument("--webapp", default=DEFAULT_WEBAPP)
    ap.add_argument("--prompt-file")
    ap.add_argument("--out", default="05-images/storyboard/_rh_test.png")
    ap.add_argument("--aspect", default="16:9")
    ap.add_argument("--resolution", default="2k")
    args = ap.parse_args()

    if args.check:
        k = api_key()
        print(f"🔑 Key: {k[:10]}…{k[-6:]}（长度 {len(k)}）")
        print(f"💰 账户: {account_status(k)}")
        nodes = node_info(args.webapp, key=k)
        print(f"🧩 应用 {args.webapp} 节点 {len(nodes)} 个：")
        for n in nodes:
            print(f"   {n.get('nodeId')} | {n.get('fieldName')} | {n.get('fieldType')} | {str(n.get('fieldValue'))[:40]}")
        print("✅ AI 应用通道自检通过（未产生费用）")
        return 0

    if not args.prompt_file:
        print("需要 --prompt-file 或 --check", file=sys.stderr)
        return 2
    prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    print(f"提交 {args.webapp} … 提示词 {len(prompt)} 字")
    t0 = time.time()
    dest, info = generate(prompt, Path(args.out), webapp=args.webapp,
                          aspect=args.aspect, resolution=args.resolution)
    print(f"✅ {dest}  ({dest.stat().st_size//1024} KB, {time.time()-t0:.1f}s)")
    print(f"info: {info}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
