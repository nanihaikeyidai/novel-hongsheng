#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《红绳》生图通道适配层 — 65535.space 迁移后版本（2026-09-20）

背景（09-20 实测结论）
----------------------
65535.space **平台已迁移**。旧网关主机全部 502 停用，不再恢复：

    img-cn.65535.space / api.65535.space / api-cn.65535.space   → 502

新平台官方端点（公开文档 `https://my.65535.space/api/endpoints` 实测返回）：

    对话-国际端点   https://api2.65535.space
    对话-大陆优化   https://api2-cn.65535.space
    任务-国际端点   https://task-api-1.65535.space
    任务-大陆优化   https://task-api-1-cn.65535.space   ← 图片/视频任务默认走这里
    任务-分发专用   https://sub-proxy-us.65535.space

生图属于「任务 API」，因此本模块默认指向 `task-api-1-cn.65535.space`。

两条调用路线
------------
native（默认，官方推荐「新接入请用原生接口」）:
    POST /v1/tasks          → 202 {"id": "img_xxx", "status": "pending"}
    GET  /v1/tasks/{id}     → 轮询至 status == "done"，读 result_urls / result.data[].b64_json

legacy（旧客户端同步兼容，迁移期保留）:
    POST /65535-old/v1/images/generations   → 直接返回图片

环境变量
--------
    IMG_API_KEY     必填。新平台 Key（在 https://my.65535.space 生成/转移）
    IMG_BASE_URL    可选。默认 https://task-api-1-cn.65535.space
    IMG_API_STYLE   可选。native（默认）| legacy
    IMG_POLL_S      可选。轮询间隔秒，默认 3
    IMG_TASK_TIMEOUT 可选。单任务总超时秒，默认 600

注意：`/v1/models` 与 `/v1/pricing` **不需要 Key 也返回 200**（公开），
因此不能用它们判断 Key 是否有效——必须用 `/v1/tasks`、`/v1/usage` 这类
需要鉴权的接口，或直接看是否返回 401 invalid_api_key。
"""

import base64
import os
import time
from typing import Optional, Tuple

import requests

# ── 平台常量 ─────────────────────────────────────────────────────────
DEFAULT_BASE_URL = "https://task-api-1-cn.65535.space"
INTL_BASE_URL = "https://task-api-1.65535.space"
DEAD_HOSTS = ("img-cn.65535.space", "api.65535.space", "api-cn.65535.space")

DEFAULT_MODEL = "gpt-image-2"


class ImgApiError(RuntimeError):
    """带 HTTP 状态码的通道异常，便于上层如实登记失败原因。"""

    def __init__(self, status: int, message: str, body: str = ""):
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.message = message
        self.body = (body or "")[:400]


def api_key() -> str:
    return os.environ.get("IMG_API_KEY", "").strip()


def base_url() -> str:
    return (os.environ.get("IMG_BASE_URL", "").strip().rstrip("/")
            or DEFAULT_BASE_URL)


def api_style() -> str:
    return os.environ.get("IMG_API_STYLE", "native").strip().lower() or "native"


def _poll_seconds() -> float:
    try:
        return float(os.environ.get("IMG_POLL_S", "3"))
    except ValueError:
        return 3.0


def _task_timeout() -> float:
    try:
        return float(os.environ.get("IMG_TASK_TIMEOUT", "600"))
    except ValueError:
        return 600.0


def _headers(key: str) -> dict:
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _require_key() -> str:
    key = api_key()
    if not key:
        raise ImgApiError(0, "IMG_API_KEY 未设置")
    return key


def _fetch_bytes(url: str, timeout: float = 300) -> bytes:
    r = requests.get(url, timeout=timeout)
    if r.status_code != 200:
        raise ImgApiError(r.status_code, f"下载结果图失败 {url[:120]}", r.text)
    return r.content


def _decode_b64(s: str) -> bytes:
    if s.startswith("data:"):
        s = s.split(",", 1)[-1]
    return base64.b64decode(s)


def _extract_from_openai_shape(doc: dict, timeout: float) -> Optional[bytes]:
    """兼容 OpenAI 形状：{"data":[{"b64_json":...}|{"url":...}]}"""
    items = doc.get("data") or []
    if not isinstance(items, list) or not items:
        return None
    entry = items[0]
    if not isinstance(entry, dict):
        return None
    if entry.get("b64_json"):
        return _decode_b64(entry["b64_json"])
    if entry.get("url"):
        return _fetch_bytes(entry["url"], timeout)
    return None


def _extract_from_task_doc(doc: dict, timeout: float) -> Optional[bytes]:
    """原生任务完成响应：优先 result_urls，其次 result.data[].b64_json。"""
    urls = doc.get("result_urls") or []
    if urls:
        return _fetch_bytes(urls[0], timeout)
    result = doc.get("result") or {}
    got = _extract_from_openai_shape(result, timeout)
    if got:
        return got
    if result.get("b64_json"):
        return _decode_b64(result["b64_json"])
    return None


def _native_generate(prompt: str, model: str, size: Optional[str],
                     resolution: Optional[str], timeout: float) -> Tuple[bytes, dict]:
    """POST /v1/tasks → 轮询 GET /v1/tasks/{id}。"""
    key = _require_key()
    base = base_url()
    if any(h in base for h in DEAD_HOSTS):
        raise ImgApiError(0, f"IMG_BASE_URL 指向已停用的旧主机：{base}")

    inp = {"prompt": prompt, "n": 1}
    if size:
        inp["size"] = size
    if resolution:
        inp["resolution"] = resolution
    payload = {"kind": "image", "model": model, "input": inp}

    r = requests.post(f"{base}/v1/tasks", json=payload,
                      headers=_headers(key), timeout=timeout)
    if r.status_code not in (200, 202):
        raise ImgApiError(r.status_code, "创建图像任务失败", r.text)

    doc = r.json()
    task_id = doc.get("id")
    if not task_id:
        raise ImgApiError(r.status_code, f"创建响应无任务 id：{str(doc)[:200]}", r.text)

    deadline = time.time() + _task_timeout()
    interval = _poll_seconds()
    last = doc
    while time.time() < deadline:
        rr = requests.get(f"{base}/v1/tasks/{task_id}",
                          headers=_headers(key), timeout=timeout)
        if rr.status_code != 200:
            raise ImgApiError(rr.status_code, f"查询任务 {task_id} 失败", rr.text)
        last = rr.json()
        status = str(last.get("status", "")).lower()
        if status == "done":
            raw = _extract_from_task_doc(last, timeout)
            if not raw:
                raise ImgApiError(200, f"任务 {task_id} 完成但无图片数据", str(last)[:200])
            return raw, last
        if status == "failed":
            raise ImgApiError(
                200,
                f"任务失败 {last.get('error_code','')}: {last.get('error_message','')}",
                str(last)[:200])
        time.sleep(interval)
    raise ImgApiError(0, f"任务 {task_id} 超时（>{_task_timeout():.0f}s），最后状态 "
                         f"{last.get('status')}")


def _legacy_generate(prompt: str, model: str, size: Optional[str],
                     timeout: float) -> Tuple[bytes, dict]:
    """POST /65535-old/v1/images/generations（同步返回图片）。"""
    key = _require_key()
    base = base_url()
    payload = {"model": model, "prompt": prompt, "n": 1,
               "response_format": "b64_json"}
    if size:
        payload["size"] = size
    r = requests.post(f"{base}/65535-old/v1/images/generations", json=payload,
                      headers=_headers(key), timeout=timeout)
    if r.status_code != 200:
        raise ImgApiError(r.status_code, "旧兼容出图失败", r.text)
    doc = r.json()
    raw = _extract_from_openai_shape(doc, timeout)
    if not raw:
        raise ImgApiError(200, "旧兼容返回无图片数据", str(doc)[:200])
    return raw, doc


def generate_image(prompt: str,
                   size: Optional[str] = "16:9",
                   resolution: Optional[str] = "2k",
                   model: str = DEFAULT_MODEL,
                   timeout: float = 300,
                   style: Optional[str] = None) -> Tuple[bytes, dict]:
    """生成一张图。

    返回 (image_bytes, 原始响应 dict)。
    失败抛 ImgApiError（含 HTTP 状态码），由调用方如实登记，不伪造图片。
    """
    st = (style or api_style()).lower()
    if st == "legacy":
        return _legacy_generate(prompt, model, size, timeout)
    return _native_generate(prompt, model, size, resolution, timeout)


def preflight() -> Tuple[bool, str]:
    """只读自检：Key 是否存在 + 通道是否可达 + Key 是否被受理。

    不做任何生成，不产生费用。返回 (ok, 说明)。
    """
    key = api_key()
    if not key:
        return False, "IMG_API_KEY 未设置"
    base = base_url()
    try:
        # 公开接口：只能证明主机可达，不能证明 Key 有效
        r = requests.get(f"{base}/v1/pricing", timeout=20)
        reachable = f"HTTP {r.status_code}"
    except Exception as e:  # noqa: BLE001
        return False, f"通道不可达：{type(e).__name__} {e}"
    try:
        # 鉴权接口：这是判定 Key 有效性的唯一可靠方式
        r2 = requests.get(f"{base}/v1/usage", headers=_headers(key), timeout=20)
        if r2.status_code == 401:
            return False, (f"主机可达（/v1/pricing {reachable}），"
                           f"但 Key 被拒绝：HTTP 401 {r2.text[:120]}")
        if r2.status_code == 200:
            return True, f"Key 有效，通道就绪（base={base}）"
        return False, f"/v1/usage 返回 HTTP {r2.status_code}: {r2.text[:120]}"
    except Exception as e:  # noqa: BLE001
        return False, f"鉴权自检异常：{type(e).__name__} {e}"


if __name__ == "__main__":
    ok, msg = preflight()
    print(("✅ " if ok else "❌ ") + msg)
    print(f"   base_url   = {base_url()}")
    print(f"   api_style  = {api_style()}")
    raise SystemExit(0 if ok else 1)
