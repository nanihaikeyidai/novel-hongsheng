#!/usr/bin/env python3
"""《红绳》剧本工作室 · 可编辑预览服务（本地）

用法：
    python preview/server.py                 # 默认 http://127.0.0.1:8765
    python preview/server.py --port 9000
    python preview/server.py --no-open       # 不自动开浏览器

为什么需要它：
    preview/index.html 是静态页，用 file:// 打开时浏览器没有写文件的能力。
    本服务提供 HTTP 接口，让页面里的编辑真正落回 episodes/*.md。

**本文件只做 HTTP 转发，不含任何写入逻辑**：
    解析 → core.parse_episode()
    编辑 → core.apply_ops()      （前端发结构化 ops，Python 侧唯一写入通道）
    校验 → core.check_integrity()
    落盘 → core.save_episode()    （内部：备份 → 保留 CRLF → sync 刷新内嵌）

接口（见 preview/CONTRACT.md）：
    GET  /api/episodes           列出所有集
    GET  /api/parse?id=ep06      结构化解析结果（行号 + 块）
    GET  /api/raw?id=ep06        某集原文
    GET  /api/diff?id=ep06       与 git HEAD 的差异
    POST /api/save               {id, ops, deleted} → 写回

只监听 127.0.0.1，不对外暴露。
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EP_DIR = ROOT / "episodes"
INDEX = HERE / "index.html"
BACKUP_DIR = HERE / ".backups"

sys.path.insert(0, str(HERE))
import core  # noqa: E402  唯一写入通道：所有落盘逻辑都在 core 里


def _log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


class Handler(BaseHTTPRequestHandler):
    server_version = "HongshengPreview/2.0"

    def log_message(self, fmt: str, *args) -> None:  # 静音默认访问日志
        pass

    # ---------- helpers ----------
    def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError):
            pass

    def _json(self, obj: object, code: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send(code, body, "application/json; charset=utf-8")

    def _ep_id(self, query: str) -> str | None:
        """从 query 里取出集号，非法直接返回 None。"""
        qs = parse_qs(query)
        ep_id = (qs.get("id") or [""])[0]
        if not ep_id:
            return None
        try:
            core.resolve_ep_path(ep_id)
        except ValueError:
            return None
        return ep_id

    # ---------- routes ----------
    def do_GET(self) -> None:
        route = urlparse(self.path)

        if route.path in ("/", "/index.html"):
            try:
                body = INDEX.read_bytes()
            except OSError:
                self._json({"error": "index.html 不可读"}, 500)
                return
            self._send(200, body, "text/html; charset=utf-8")
            return

        if route.path == "/api/episodes":
            self._json({"episodes": core.list_episodes()})
            return

        if route.path == "/api/parse":
            ep_id = self._ep_id(route.query)
            if not ep_id:
                self._json({"error": "缺少或非法的 id 参数"}, 400)
                return
            try:
                md = core.read_episode(ep_id)
            except (ValueError, OSError) as exc:
                self._json({"error": str(exc)}, 404)
                return
            parsed = core.parse_episode(md)
            self._json({"id": ep_id, "meta": parsed["meta"], "parsed": parsed})
            return

        if route.path == "/api/raw":
            ep_id = self._ep_id(route.query)
            if not ep_id:
                self._json({"error": "缺少或非法的 id 参数"}, 400)
                return
            try:
                self._json({"id": ep_id, "markdown": core.read_episode(ep_id)})
            except (ValueError, OSError) as exc:
                self._json({"error": str(exc)}, 404)
            return

        if route.path == "/api/diff":
            ep_id = self._ep_id(route.query)
            if not ep_id:
                self._json({"error": "缺少或非法的 id 参数"}, 400)
                return
            diff = core.diff_against_head(ep_id)
            self._json({"id": ep_id, "diff": diff})
            return

        self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        route = urlparse(self.path)
        if route.path != "/api/save":
            self._json({"error": "not found"}, 404)
            return

        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > 4 * 1024 * 1024:
            self._json({"error": "请求体为空或过大"}, 400)
            return

        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._json({"error": f"JSON 解析失败：{exc}"}, 400)
            return

        if not isinstance(payload, dict):
            self._json({"error": "请求体必须是 JSON 对象"}, 400)
            return

        ep_id = str(payload.get("id") or "")
        ops = payload.get("ops")
        deleted = payload.get("deleted") or {}
        if not isinstance(ops, list):
            self._json({"error": "缺少 ops 字段（应为操作列表）"}, 400)
            return
        if not isinstance(deleted, dict):
            deleted = {}

        try:
            old = core.read_episode(ep_id)
        except (ValueError, OSError) as exc:
            self._json({"error": str(exc)}, 400)
            return

        # 解析 ops → 校验 → 落盘，全部委托 core
        try:
            new_md, summary = core.apply_ops(old, ops)
        except ValueError as exc:
            self._json({"error": str(exc)}, 400)
            return

        # deleted 是前端声明的「本次主动删除量」。
        # 取「前端声明」与「ops 圈定的行里实际有多少内容行」的**较大者**：
        #   - 前端声明得更准（主动删了很多行）→ 采信前端
        #   - 前端没声明或声明为 0，但 ops 里确实是 delete_block → 采信 ops
        #   - 圈外的意外丢失 → 两边都不放行，闸门拦下
        computed = core.deleted_allowance(old, core.op_ranges(ops))
        deleted = {
            "lines": max(int(deleted.get("lines") or 0), computed["lines"]),
            "notes": max(int(deleted.get("notes") or 0), computed["notes"]),
        }

        problems = core.check_integrity(old, new_md, deleted)
        if problems:
            self._json({"error": "拒绝写入，完整性校验未通过：" + "；".join(problems)}, 400)
            return

        try:
            core.save_episode(ep_id, new_md, deleted)
        except ValueError as exc:
            self._json({"error": str(exc)}, 400)
            return
        except OSError as exc:
            self._json({"error": f"写入失败：{exc}"}, 500)
            return

        _log(f"已保存 {ep_id}.md（{summary.get('changed', 0)} 处改动）")
        self._json({
            "ok": True,
            "id": ep_id,
            "episodes": core.list_episodes(),
            "diff": core.diff_lines(old, new_md),
            "summary": summary,
        })


def main() -> None:
    ap = argparse.ArgumentParser(description="《红绳》剧本工作室 · 可编辑预览服务")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-open", action="store_true", help="不自动打开浏览器")
    args = ap.parse_args()

    if not EP_DIR.exists():
        raise SystemExit(f"找不到 episodes 目录：{EP_DIR}")

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}/"
    _log(f"《红绳》剧本工作室 · 可编辑预览 → {url}")
    _log(f"episodes 目录：{EP_DIR}")
    _log("编辑后点「保存到文档」即可写回 .md；Ctrl+C 退出")

    if not args.no_open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        _log("已停止")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
