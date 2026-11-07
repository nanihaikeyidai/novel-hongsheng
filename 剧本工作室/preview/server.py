#!/usr/bin/env python3
"""《红绳》剧本工作室 · 可编辑预览服务（本地）

用法：
    python preview/server.py                 # 默认 http://127.0.0.1:8765
    python preview/server.py --port 9000
    python preview/server.py --no-open       # 不自动开浏览器

为什么需要它：
    preview/index.html 是静态页，用 file:// 打开时浏览器没有写文件的能力。
    本服务提供两个接口，让页面里的编辑真正落回 episodes/*.md：
        GET  /api/episodes      从磁盘重新读 episodes/*.md（不走内嵌快照）
        POST /api/save          写回 episodes/epXX.md，并自动重跑 sync.py
    写回前会把旧版备份到 preview/.backups/，不碰 episodes/ 目录以外的任何文件。

只监听 127.0.0.1，不对外暴露。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
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
import sync as sync_mod  # noqa: E402  复用同一份内嵌逻辑，避免两套实现漂移

EP_ID_RE = re.compile(r"^ep\d{2,3}$")
SAVE_LOCK = threading.Lock()


def _log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def list_episodes() -> list[dict]:
    """从磁盘重新读取 episodes/*.md。"""
    return sync_mod.load_episodes()


def resolve_ep_path(ep_id: str) -> Path:
    """把集号解析成安全的文件路径，挡住路径穿越。"""
    if not EP_ID_RE.match(ep_id):
        raise ValueError(f"非法集号：{ep_id}")
    path = (EP_DIR / f"{ep_id}.md").resolve()
    if path.parent != EP_DIR.resolve():
        raise ValueError(f"越界路径：{ep_id}")
    return path


def _count(md: str, pattern: str) -> int:
    return len(re.findall(pattern, md, re.M))


def check_integrity(old: str, new: str, deleted: dict | None = None) -> list[str]:
    """写回前的完整性校验：新内容不得比原文少台词行/动作行/附注段。

    这是最后一道闸门——网页端的校验可能因各种原因失效，
    这里保证磁盘上永远不会出现「被截断的剧本」。

    刻意删除的行/附注段是合法编辑，因此按 deleted 放行对应减少量。
    """
    deleted = deleted or {}
    del_lines = int(deleted.get("lines") or 0)
    del_notes = int(deleted.get("notes") or 0)
    problems: list[str] = []
    checks = (
        ("台词行", r"^[^：:\s　]{1,12}：", del_lines),
        ("动作行", r"^△", del_lines),
        ("表演附注段", r"^【表演附注", del_notes),
    )
    for label, pat, allowance in checks:
        o, n = _count(old, pat), _count(new, pat)
        if n < o - allowance:
            problems.append(f"{label}少了 {o - n} 个（{o} → {n}），超出本次删除的 {allowance} 个")
    return problems


def save_episode(ep_id: str, markdown: str, deleted: dict | None = None) -> Path:
    """写回 episodes/epXX.md，备份旧版，然后刷新内嵌数据。"""
    path = resolve_ep_path(ep_id)
    with SAVE_LOCK:
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        problems = check_integrity(old, markdown, deleted) if old else []
        if problems:
            raise ValueError("拒绝写入，完整性校验未通过：" + "；".join(problems))
        if path.exists():
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            shutil.copy2(path, BACKUP_DIR / f"{ep_id}.{stamp}.md")
            # 沿用原文件的换行风格，避免 git 把整个文件视为全改
            old_bytes = path.read_bytes()
            if b"\r\n" in old_bytes and "\r\n" not in markdown:
                markdown = markdown.replace("\n", "\r\n")
        path.write_text(markdown, encoding="utf-8", newline="")
        # 内嵌数据跟着更新，file:// 方式打开也能看到最新内容
        sync_mod.main()
    return path


class Handler(BaseHTTPRequestHandler):
    server_version = "HongshengPreview/1.0"

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

    def _json(self, obj, code: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send(code, body, "application/json; charset=utf-8")

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
            self._json({"episodes": list_episodes()})
            return

        if route.path == "/api/raw":
            qs = parse_qs(route.query)
            ep_id = (qs.get("id") or [""])[0]
            try:
                path = resolve_ep_path(ep_id)
            except ValueError as exc:
                self._json({"error": str(exc)}, 400)
                return
            try:
                self._json({"id": ep_id, "markdown": path.read_text(encoding="utf-8")})
            except OSError as exc:
                self._json({"error": str(exc)}, 404)
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

        ep_id = str(payload.get("id") or "")
        markdown = payload.get("markdown")
        deleted = payload.get("deletedLines") or {}
        if not isinstance(markdown, str):
            self._json({"error": "缺少 markdown 字段"}, 400)
            return

        try:
            path = save_episode(ep_id, markdown, deleted if isinstance(deleted, dict) else None)
        except ValueError as exc:
            self._json({"error": str(exc)}, 400)
            return
        except OSError as exc:
            self._json({"error": f"写入失败：{exc}"}, 500)
            return

        _log(f"已保存 {path.name}（{len(markdown)} 字符）")
        self._json({"ok": True, "id": ep_id, "episodes": list_episodes()})


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
