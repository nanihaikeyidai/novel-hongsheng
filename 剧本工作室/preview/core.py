#!/usr/bin/env python3
"""《红绳》剧本工作室 · 核心层（唯一写入通道）

分层（详见 preview/CONTRACT.md）：
    episodes/epXX.md   ← 唯一真相源
        ↑ core.py       ← 解析 / 编辑 / 校验 / 备份 / 落盘，全在这里
        ↑                server.py（HTTP，给 Web）   cli.py（命令行，给 Agent）
                         两者只调本模块，不允许各自实现写入逻辑

设计上的几条硬规矩：
1. **行号一律 0 基绝对行号**，指向**原文**的 md。所有 op 一次性应用，
   互不基于上一次结果；行区间重叠直接报错。
2. **一切按 LF 思考，落盘时再还原 CRLF**。Windows 上仓库里这些 md 是 CRLF
   （git autocrlf=true），如果按 LF 写回，git 会把整个文件视作全改。
3. **附注块是「头行 + 每行以 "- " 开头的正文」**。头行 `【表演附注 X】` 不在
   text 里，replace 时由 core 按原文保留——所以删附注能删干净，改附注不会丢头。
4. **replace_block 的行数必须与原块一致**。新内容短了补空行，长了截断。
   这是为了保证后续所有行号不错位（详见 _render_block 的注释）。

历史踩过的坑（别再犯）：
- 曾经把「剧情梗概」里的 `- **起**：` 当成台词做完整性统计 → 场次正文边界
  必须收到下一个 `##` 二级标题为止。
- 曾经把附注正文整段丢失 → 附注块的 text 必须是「每行以 "- " 开头」的整段，
  缺前缀要补。
- 曾经「删除按钮把没点的行也判成删除」→ 删除必须由服务端显式 op 表达，
  这里不做任何 DOM 推断。
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import threading
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------- 路径常量 --
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EP_DIR = ROOT / "episodes"
INDEX = HERE / "index.html"
BACKUP_DIR = HERE / ".backups"

sys.path.insert(0, str(HERE))
import sync as sync_mod  # noqa: E402  复用同一份内嵌逻辑，避免两套实现漂移

EP_ID_RE = re.compile(r"^ep\d{2,3}$")
SAVE_LOCK = threading.Lock()

# 完整性校验用的三种「内容行」正则（与旧 server.py / index.html 保持一致，
# 改这里等于改闸门口径，必须三处同步）。
RE_DIALOGUE = re.compile(r"^[^：:\s　]{1,12}：", re.M)
RE_ACTION = re.compile(r"^△", re.M)
RE_NOTE = re.compile(r"^【表演附注", re.M)

# 场次标题：### 6-1a 地下车库 夜 内（同场分段用 a/b/c…）
RE_SCENE_HEAD = re.compile(r"^###\s+(\d+-\d+[a-z]?)\s*(.*)$")
RE_CHARACTERS = re.compile(r"^人物[：:]\s*(.+)$")
RE_NOTE_HEAD = re.compile(r"^【表演附注[^】]*】")
RE_DIALOGUE_LINE = re.compile(r"^([^：:\s　]{1,12})([：:])(.*)$")
RE_BULLET_DIALOGUE = re.compile(r"^-\s+([^：:\s]{1,12})([：:])(.*)$")
RE_HR = re.compile(r"^-{3,}\s*$")
RE_HEADING = re.compile(r"^#{1,6}\s")

# 这些词出现在「XX：」开头时是标签不是说话人（附注里的 - 节拍：… 等）
META_LABELS = {
    "节拍", "潜台词", "情绪线", "表演时机", "声音", "价值", "场景功能", "功能",
    "衔接备注", "id", "title", "status", "duration_target", "aspect", "updated",
    "premise", "open", "revision", "人物", "类型", "风格", "标签", "人设",
}

BLOCK_TYPES = ("action", "dialogue", "note", "beat")


# ------------------------------------------------------------ 基础文本工具 --
def detect_eol(text: str) -> str:
    """判断文本的换行风格：含 \\r\\n 就是 CRLF，否则 LF。"""
    return "\r\n" if "\r\n" in text else "\n"


def split_lines(text: str) -> list[str]:
    """按行切分并剥掉行尾的 \\r。

    Windows 下这些 md 是 CRLF，直接 text.split("\\n") 会在每行尾部留下 \\r，
    导致 `^△` 这类前缀判断失配（附注正文尤其明显）。
    """
    return [ln.rstrip("\r") for ln in re.split(r"\r\n|\n", text)]


def join_lines(lines: list[str], eol: str) -> str:
    return eol.join(lines)


def to_eol(text: str, eol: str) -> str:
    """把任意换行统一成 eol（用 lambda 避免 re.sub 把 \\r\\n 当转义序列）。"""
    return re.sub(r"\r\n|\n", lambda _m: eol, text)


def normalize(text: str) -> str:
    """统一成 LF，供解析 / 比较 / diff 使用。"""
    return text.replace("\r\n", "\n")


# --------------------------------------------------------------- frontmatter --
def parse_yaml(md: str) -> dict[str, str]:
    """解析 ```yaml 包裹的 frontmatter，返回 {键: 字符串值}。"""
    meta: dict[str, str] = {}
    m = re.search(r"```ya?ml[^\S\r\n]*\r?\n(.*?)```", md, re.S)
    if not m:
        return meta
    for raw in split_lines(m.group(1)):
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta


def _quote_like(old_value: str, new_value: str) -> str:
    """按原有引号风格给新值加引号；没有引号但值里含敏感字符时补双引号。"""
    old = old_value.strip()
    if old.startswith('"') and old.endswith('"') and len(old) >= 2:
        return '"' + new_value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if old.startswith("'") and old.endswith("'") and len(old) >= 2:
        return "'" + new_value.replace("'", "''") + "'"
    if new_value == "" or ":" in new_value or "#" in new_value:
        return '"' + new_value.replace('"', '\\"') + '"'
    return new_value


def set_yaml(md: str, key: str, value: str) -> str:
    """改 frontmatter 的某个键，保留原格式与换行风格。

    - 键存在 → 原地替换值（保留缩进、引号风格）
    - 键不存在 → 在 yaml 块末尾追加一行
    - 没有 yaml 块 → 报错（不静默新建，避免产出畸形文档）
    """
    if not re.search(r"```ya?ml[^\S\r\n]*\r?\n", md):
        raise ValueError("该文件没有 yaml frontmatter，无法写 meta")

    eol = detect_eol(md)
    m = re.search(r"(```ya?ml[^\S\r\n]*\r?\n)(.*?)(```)", md, re.S)
    assert m is not None
    head, body, tail = m.group(1), m.group(2), m.group(3)

    raw_lines = re.split(r"(\r\n|\n|\r)", body)
    # raw_lines 是 [内容, 分隔符, 内容, 分隔符, ...]
    contents = raw_lines[0::2]
    seps = raw_lines[1::2]

    target = -1
    for i, content in enumerate(contents):
        m2 = re.match(r"^(\s*)" + re.escape(key) + r"\s*:(.*)$", content)
        if m2:
            target = i
            break

    if target >= 0:
        old_value = re.match(r"^(\s*)" + re.escape(key) + r"\s*:(.*)$", contents[target]).group(2)  # type: ignore[union-attr]
        indent = re.match(r"^(\s*)", contents[target]).group(1)  # type: ignore[union-attr]
        sep = seps[target] if target < len(seps) else eol
        contents[target] = f"{indent}{key}: {_quote_like(old_value, value)}"
        new_body = "".join(c + (seps[i] if i < len(seps) else "") for i, c in enumerate(contents))
    else:
        sep = eol
        new_body = body
        if new_body and not new_body.endswith(("\n", "\r")):
            new_body += sep
        new_body += f"{key}: {_quote_like('', value)}" + sep

    return md[: m.start()] + head + new_body + tail + md[m.end():]


# ------------------------------------------------------------------ 读集数 --
def resolve_ep_path(ep_id: str) -> Path:
    """把集号解析成安全的文件路径，挡住路径穿越。"""
    if not isinstance(ep_id, str) or not EP_ID_RE.match(ep_id):
        raise ValueError(f"非法集号：{ep_id}")
    path = (EP_DIR / f"{ep_id}.md").resolve()
    if path.parent != EP_DIR.resolve():
        raise ValueError(f"越界路径：{ep_id}")
    return path


def list_episodes() -> list[dict]:
    """列出所有集：[{id, meta, markdown}]，按 id 排序。

    直接复用 sync.load_episodes()（与 index.html 内嵌快照同一份口径），
    只把 meta 补齐成契约要求的 id/title/status/updated。

    markdown 是 read_text 出来的 LF 版本——与内嵌快照一致，前端拿到
    /api/episodes 和拿到内嵌数据看到的行号完全相同。
    落盘时的 CRLF 由 save_episode 依据**磁盘原文件**判定，与这里无关。
    """
    items = sync_mod.load_episodes()
    out: list[dict] = []
    for it in items:
        ep_id = str(it.get("id") or "")
        meta = dict(it.get("meta") or {})
        meta["id"] = ep_id
        meta["title"] = str(meta.get("title") or ep_id)
        meta["status"] = str(meta.get("status") or "")
        meta["updated"] = str(meta.get("updated") or "")
        out.append({"id": ep_id, "meta": meta, "markdown": str(it.get("markdown") or "")})
    out.sort(key=lambda x: x["id"])
    return out


def read_episode(ep_id: str) -> str:
    """读一集的原始文本（保留 CRLF）。"""
    path = resolve_ep_path(ep_id)
    if not path.exists():
        raise ValueError(f"集不存在：{ep_id}")
    return path.read_bytes().decode("utf-8")


# -------------------------------------------------------------------- 解析 --
def _parse_scene_table(lines: list[str]) -> list[list[str]]:
    """抓「## 分场表」下的表格行。"""
    table: list[list[str]] = []
    start = None
    for i, ln in enumerate(lines):
        if re.match(r"^##\s*分场表", ln):
            start = i
            break
    if start is None:
        return table
    for ln in lines[start + 1:]:
        if not ln.strip():
            continue  # 表头与表格之间有空行，跳过
        if not ln.startswith("|"):
            break
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue  # 分隔行
        if cells and cells[0] in ("场次", "场次号"):
            continue  # 表头
        if len(cells) >= 2:
            table.append(cells)
    return table


def _classify_line(line: str) -> tuple[str, str, str, str] | None:
    """把一行分类成 (type, who, text, prefix)。不认识就当 beat（原文保留）。

    顺序很重要：先判 △ 动作行，再判台词行。
    因为 △ 允许正文里出现冒号（如「△特写：手」），先判台词会把动作行误认成台词。
    """
    if line.startswith("△") or line.startswith("◆△") or line.startswith("★△"):
        return ("action", "", re.sub(r"^[◆★]?△[^\S　]?", "", line), "")

    m = RE_DIALOGUE_LINE.match(line)
    if m:
        who, prefix, text = m.group(1), m.group(2), m.group(3)
        if who in META_LABELS:
            return ("beat", "", line, "")
        return ("dialogue", who, text.strip(), prefix)

    m = RE_BULLET_DIALOGUE.match(line)
    if m:
        who, prefix, text = m.group(1), m.group(2), m.group(3)
        if who not in META_LABELS:
            return ("dialogue", who, text.strip(), prefix)
        return ("beat", "", line, "")

    return ("beat", "", line, "")


def parse_episode(md: str) -> dict[str, Any]:
    """解析一集 markdown，返回带行号与块结构的 dict。

    返回结构见 CONTRACT.md 第 2 节。要点：
    - 场次正文边界收到下一个 `##` 二级标题为止（否则会把「剧情梗概」的
      `- **起**：` 误判成台词）。
    - 附注块 = `【表演附注 X】` 头行 + 连续 `- ` 开头的正文行。
    - blocks 的 lineStart/lineEnd 指向**原文**行号。
    """
    eol = detect_eol(md)
    lines = split_lines(md)
    meta = parse_yaml(md)

    # 先定位所有场次标题，再算每场的正文边界。
    heads: list[tuple[int, str, str]] = []
    for i, ln in enumerate(lines):
        m = RE_SCENE_HEAD.match(ln)
        if m:
            heads.append((i, m.group(1), m.group(2).strip()))

    scenes: list[dict[str, Any]] = []
    for h, (h_line, sid, title_line) in enumerate(heads):
        limit = heads[h + 1][0] if h + 1 < len(heads) else len(lines)
        # 正文遇到 `##` 二级标题就停（先到先算）
        end = limit
        for k in range(h_line + 1, limit):
            if lines[k].startswith("## "):
                end = k
                break
        # 去掉尾部空行与 `---` 分隔线，让 lineEnd 落在最后一条有效内容上
        while end > h_line + 1 and (not lines[end - 1].strip() or RE_HR.match(lines[end - 1])):
            end -= 1

        characters: list[str] = []
        blocks: list[dict[str, Any]] = []
        i = h_line + 1
        while i < end:
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            if RE_HR.match(line) or RE_HEADING.match(line):
                i += 1
                continue
            cm = RE_CHARACTERS.match(line)
            if cm:
                characters = [c.strip() for c in re.split(r"[、,，]", cm.group(1)) if c.strip()]
                i += 1
                continue
            if RE_NOTE_HEAD.match(line):
                header = line
                j = i + 1
                while j < end and lines[j].lstrip().startswith("-"):
                    j += 1
                body = lines[i + 1: j]
                blocks.append({
                    "type": "note",
                    "who": "",
                    "text": "\n".join(body),
                    "lineStart": i,
                    "lineEnd": (j - 1) if j - 1 > i else i,
                    "prefix": "",
                    "header": header,
                })
                i = j
                continue
            kind = _classify_line(line)
            if kind is None:
                i += 1
                continue
            btype, who, text, prefix = kind
            blocks.append({
                "type": btype,
                "who": who,
                "text": text,
                "lineStart": i,
                "lineEnd": i,
                "prefix": prefix,
            })
            i += 1

        scenes.append({
            "id": sid,
            "heading": f"{sid} {title_line}".strip(),
            "titleLine": title_line,
            "lineStart": h_line,
            "lineEnd": max(h_line, end - 1),
            "characters": characters,
            "blocks": blocks,
        })

    return {
        "meta": meta,
        "scenes": scenes,
        "sceneTable": _parse_scene_table(lines),
        "lines": lines,
        "eol": eol,
    }


def scene_by_id(parsed: dict[str, Any], scene_id: str) -> dict[str, Any] | None:
    """按场次号取场次对象，取不到返回 None。"""
    for sc in parsed.get("scenes", []):
        if sc.get("id") == scene_id:
            return sc
    return None


# ------------------------------------------------------------------ ops 解析 --
def _op_kind(op: dict[str, Any]) -> str:
    """取 op 的种类。

    规范字段是 `op`（CONTRACT 第 3 节的表头就是这么写的）；为了兼容前端
    的其它叫法，也接受 `opType` / `kind` / `name`。注意 `type` 在
    replace_block 里是**块类型**（action/dialogue/note/beat），不能当种类用。
    """
    for key in ("op", "opType", "kind", "name"):
        v = op.get(key)
        if isinstance(v, str) and v:
            return v
    # 兜底：没有 op 字段时按字段形状猜（只猜无歧义的情况）
    if isinstance(op.get("type"), str) and op.get("type") in BLOCK_TYPES and "lineStart" in op:
        return "replace_block"
    if "lineStart" in op and "lineEnd" in op:
        return "delete_block"
    return ""


def _require(op: dict[str, Any], key: str, idx: int) -> Any:
    if key not in op:
        raise ValueError(f"第 {idx + 1} 个 op 缺少字段 {key}")
    return op[key]


def _as_int(op: dict[str, Any], key: str, idx: int) -> int:
    v = _require(op, key, idx)
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"第 {idx + 1} 个 op 的 {key} 必须是整数，收到 {v!r}")
    return v


def _op_text(op: dict[str, Any], idx: int) -> str:
    v = op.get("text", "")
    if v is None:
        return ""
    if not isinstance(v, str):
        raise ValueError(f"第 {idx + 1} 个 op 的 text 必须是字符串")
    return v


def _parse_ops(ops: list[dict[str, Any]], n_lines: int) -> list[dict[str, Any]]:
    """把原始 ops 归一化成内部结构，并做基本合法性检查。"""
    if not isinstance(ops, list):
        raise ValueError("ops 必须是列表")
    parsed: list[dict[str, Any]] = []
    for idx, raw in enumerate(ops):
        if not isinstance(raw, dict):
            raise ValueError(f"第 {idx + 1} 个 op 不是对象")
        kind = _op_kind(raw)
        if kind == "replace_block":
            start = _as_int(raw, "lineStart", idx)
            end = _as_int(raw, "lineEnd", idx)
            btype = raw.get("type") or "beat"
            if btype not in BLOCK_TYPES:
                raise ValueError(f"第 {idx + 1} 个 op 的 type 非法：{btype}")
            parsed.append({
                "kind": kind, "idx": idx, "start": start, "end": end,
                "type": btype, "text": _op_text(raw, idx),
                "who": raw.get("who"), "prefix": raw.get("prefix"),
            })
        elif kind == "replace_line":
            line = _as_int(raw, "line", idx)
            parsed.append({"kind": kind, "idx": idx, "start": line, "end": line,
                           "text": _op_text(raw, idx)})
        elif kind == "delete_block":
            start = _as_int(raw, "lineStart", idx)
            end = _as_int(raw, "lineEnd", idx)
            parsed.append({"kind": kind, "idx": idx, "start": start, "end": end})
        elif kind == "insert_after":
            line = _as_int(raw, "line", idx)
            parsed.append({"kind": kind, "idx": idx, "start": line, "end": line,
                           "text": _op_text(raw, idx)})
        else:
            raise ValueError(f"第 {idx + 1} 个 op 种类无法识别：{kind or '（缺 op 字段）'}")

        p = parsed[-1]
        if p["start"] < 0 or p["end"] < p["start"]:
            raise ValueError(f"第 {idx + 1} 个 op 的行区间非法：{p['start']}:{p['end']}")
        if p["kind"] != "insert_after" and p["end"] >= n_lines:
            raise ValueError(
                f"第 {idx + 1} 个 op 的行区间 {p['start']}:{p['end']} 超出正文范围"
                f"（共 {n_lines} 行，0 基）"
            )
        if p["kind"] == "insert_after" and p["start"] >= n_lines:
            raise ValueError(f"第 {idx + 1} 个 op 的插入位置 {p['start']} 超出正文范围")
    return parsed


def _infer_who_prefix(orig: list[str]) -> tuple[str, str]:
    """从原块里推断说话人与分隔符（replace_block 的 dialogue 不带 who 字段时用）。"""
    for ln in orig:
        m = RE_DIALOGUE_LINE.match(ln)
        if m and m.group(1) not in META_LABELS:
            return m.group(1), m.group(2)
    return "", "："


def _render_block(orig: list[str], op: dict[str, Any]) -> list[str]:
    """把 replace_block 的 text 渲染成最终行列表。

    **行数必须与原块一致**：短的补空行，长的截断。
    原因：行号是全篇的坐标，一旦某块行数变了，后面所有块（以及用户手里的
    行号）全部错位，改一句台词就会连累后面几十行——历史上就是这么炸的。
    """
    btype = op["type"]
    text = op["text"]
    body_lines = [b for b in text.split("\n")] if text != "" else []

    if btype == "action":
        # △ 前缀由 core 补。但原文行首的 ◆ / ★（高光标记）要**保留**：
        # parse 时会把它们剥掉，如果不按原文补回来，往返一次就丢了。
        # （ep06/ep07 里 ◆/★ 出现在行尾，那是正文的一部分，本来就原样保留。）
        deco = ""
        if orig:
            m = re.match(r"^([◆★])", orig[0].strip())
            if m:
                deco = m.group(1)
        rendered: list[str] = []
        for k, bl in enumerate(body_lines):
            s = bl.strip()
            if k == 0:
                s = re.sub(r"^[◆★]?△", "", s)
                rendered.append(deco + "△" + s)
            else:
                rendered.append(s)
    elif btype == "dialogue":
        who = op.get("who")
        prefix = op.get("prefix")
        # 分隔符一律从**原文**取（除非调用方显式给了 prefix）。
        # 注意：who 给不给都要取——前端只传 who 不传 prefix，
        # 若这里只在 who 缺失时才推断，原文里的半角「:」会被悄悄改成全角「：」。
        orig_who, orig_prefix = _infer_who_prefix(orig)
        if not who:
            who = orig_who
        if not prefix:
            prefix = orig_prefix
        if not prefix:
            prefix = "："
        who = str(who)
        rendered = []
        for k, bl in enumerate(body_lines):
            s = bl.strip()
            if k == 0:
                head = who + prefix
                if s.startswith(head):
                    s = s[len(head):]
                rendered.append(head + s)
            else:
                rendered.append(s)
    elif btype == "note":
        # 附注块 = 头行（【表演附注 X】）+ 每行以 "- " 开头的正文。
        # 契约规定 note 的 text 是**正文**（不含头行），头行由 core 按原文保留——
        # 否则改一次附注就会把「【表演附注 6-1a】」吃掉，附注就再也对不上场次了。
        raw = [bl.rstrip() for bl in body_lines]
        head: str | None = None
        if raw and raw[0].lstrip().startswith("【表演附注"):
            head = raw[0].strip()  # 兼容调用方把头行也塞进 text 的情况
            raw = raw[1:]
        body: list[str] = []
        for s in raw:
            if not s.strip():
                body.append("")
            elif s.lstrip().startswith("- "):
                body.append(s.lstrip())
            else:
                body.append("- " + s.strip())
        if head is None and orig and RE_NOTE_HEAD.match(orig[0]):
            head = orig[0].rstrip()  # 头行按原文保留
        # 原块第一行不是头行时（调用方只圈了正文），不凭空造头行
        rendered = ([head] + body) if head is not None else list(body)
    else:  # beat：原文照抄
        rendered = [bl.rstrip() for bl in body_lines]

    target = len(orig)
    if len(rendered) < target:
        rendered = rendered + [""] * (target - len(rendered))
    else:
        rendered = rendered[:target]
    return rendered


def apply_ops(md: str, ops: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    """把一组 op 应用到 markdown，返回 (新 markdown, 变更摘要)。

    - 纯函数：同样的 md + ops → 同样的结果，不碰磁盘。
    - 所有 op 都基于**同一份原文**的行号，一次性应用。
    - 行区间重叠 → 抛 ValueError。
    """
    eol = detect_eol(md)
    lines = split_lines(md)
    parsed = _parse_ops(ops, len(lines))

    # --- 重叠检查：replace/delete/line 三类占用行区间，互不相交 -----------
    spans: list[tuple[int, int, int]] = []
    for p in parsed:
        if p["kind"] == "insert_after":
            continue
        spans.append((p["start"], p["end"], p["idx"]))
    spans.sort()
    for a, b in zip(spans, spans[1:]):
        if b[0] <= a[1]:
            raise ValueError(
                f"op 行区间重叠：第 {a[2] + 1} 个 op 的 {a[0]}:{a[1]} 与"
                f"第 {b[2] + 1} 个 op 的 {b[0]}:{b[1]} 冲突"
            )

    # --- insert_after 的锚点不能落在别的 op 的区间内部 ---------------------
    for p in parsed:
        if p["kind"] != "insert_after":
            continue
        for s, e, oi in spans:
            if s <= p["start"] < e:
                raise ValueError(
                    f"insert_after 第 {p['idx'] + 1} 个 op 的锚点 {p['start']} "
                    f"落在第 {oi + 1} 个 op 的区间 {s}:{e} 内"
                )

    range_by_start: dict[int, dict[str, Any]] = {}
    inserts: dict[int, list[list[str]]] = {}
    for p in parsed:
        if p["kind"] == "insert_after":
            ins = [ln for ln in p["text"].split("\n")]
            inserts.setdefault(p["start"], []).append(ins)
        else:
            range_by_start[p["start"]] = p

    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        op = range_by_start.get(i)
        if op is not None:
            orig = lines[op["start"]: op["end"] + 1]
            if op["kind"] == "delete_block":
                pass  # 整块删掉，不产出任何行
            elif op["kind"] == "replace_line":
                out.extend(op["text"].split("\n"))
            else:  # replace_block
                out.extend(_render_block(orig, op))
            # 插入锚点落在被替换区间的**末尾**时，插在替换结果之后
            for extra in inserts.get(op["end"], []):
                out.extend(extra)
            i = op["end"] + 1
            continue
        out.append(lines[i])
        for extra in inserts.get(i, []):
            out.extend(extra)
        i += 1

    deleted_lines = sum(
        (p["end"] - p["start"] + 1) for p in parsed if p["kind"] == "delete_block"
    )
    changed = len(parsed)
    note_bits: list[str] = []
    kinds = [p["kind"] for p in parsed]
    for k in ("replace_block", "replace_line", "delete_block", "insert_after"):
        c = kinds.count(k)
        if c:
            label = {
                "replace_block": "替换块",
                "replace_line": "替换行",
                "delete_block": "删除块",
                "insert_after": "插入行",
            }[k]
            note_bits.append(f"{label} {c}")
    summary = {
        "changed": changed,
        "deleted": deleted_lines,
        "note": ("、".join(note_bits) + "；" if note_bits else "") + f"共 {changed} 处改动，删除 {deleted_lines} 行",
    }
    return join_lines(out, eol), summary


# ------------------------------------------------------------------ 完整性 --
def _count(text: str, pattern: re.Pattern[str]) -> int:
    return len(pattern.findall(text))


def _is_dialogue(line: str) -> bool:
    return bool(RE_DIALOGUE.match(line))


def _is_action(line: str) -> bool:
    return bool(RE_ACTION.match(line))


def _is_note_head(line: str) -> bool:
    return bool(RE_NOTE.match(line))


def deleted_allowance(md: str, ranges: list[tuple[int, int]]) -> dict[str, int]:
    """按「用户明确圈住的行范围」算出放行量，返回契约里的 {"lines", "notes"}。

    闸门的核心思想：**只有被明确圈住的行，才允许变少**。
    - 圈住的行里有 N 个台词行 / M 个动作行 → 台词行与动作行共用 max(N, M) 的额度
      （契约规定两个检查共用一个 "lines" 额度）
    - 圈住的行里有 K 个附注段头 → 附注段放行 K 个

    圈定范围之外的内容如果变少 → 闸门拦下。这正是「附注整段丢失」「
    删除按钮把没点的行也删了」这类事故要拦的东西。
    """
    lines = split_lines(normalize(md))
    touched: set[int] = set()
    for s, e in ranges:
        touched.update(range(max(0, s), min(len(lines), e + 1)))
    dlg = sum(1 for i in touched if _is_dialogue(lines[i]))
    act = sum(1 for i in touched if _is_action(lines[i]))
    note = sum(1 for i in touched if _is_note_head(lines[i]))
    return {"lines": max(dlg, act), "notes": note}


def op_ranges(ops: list[dict[str, Any]]) -> list[tuple[int, int]]:
    """取出 ops 真正「动到」的行区间。

    - replace_block / replace_line / delete_block → 它覆盖的行区间
    - insert_after → 空区间（插入不会让内容变少）
    """
    ranges: list[tuple[int, int]] = []
    for op in ops or []:
        kind = _op_kind(op)
        if kind in ("replace_block", "replace_line", "delete_block"):
            s = int(op.get("lineStart", op.get("line", 0)))
            e = int(op.get("lineEnd", op.get("line", 0)))
            ranges.append((s, e))
    return ranges


def check_integrity(old: str, new: str, deleted: dict[str, Any] | None = None) -> list[str]:
    """写回前的完整性校验：新内容不得比原文少台词行/动作行/附注段。

    这是最后一道闸门——前端校验可能因各种原因失效，这里保证磁盘上永远不会
    出现「被截断的剧本」。刻意删除的行/附注段是合法编辑，按 deleted 放行。

    deleted = {"lines": int, "notes": int}：
        lines  —— 台词行与动作行**共用**的放行额度（本次主动删掉了几行内容）
        notes  —— 附注段的放行额度
    """
    deleted = deleted or {}
    del_lines = int(deleted.get("lines") or 0)
    del_notes = int(deleted.get("notes") or 0)
    o = normalize(old)
    n = normalize(new)
    problems: list[str] = []
    checks = (
        ("台词行", RE_DIALOGUE, del_lines),
        ("动作行", RE_ACTION, del_lines),
        ("表演附注段", RE_NOTE, del_notes),
    )
    for label, pat, allowance in checks:
        oc, nc = _count(o, pat), _count(n, pat)
        if nc < oc - allowance:
            problems.append(
                f"{label}少了 {oc - nc} 个（{oc} → {nc}），超出本次删除的 {allowance} 个"
            )
    return problems


# -------------------------------------------------------------------- diff --
def diff_lines(old: str, new: str) -> list[dict[str, Any]]:
    """逐行 diff，返回 [{op: same|del|add, old, new, line}]。

    line 字段：same/add 是**新文本**的行号，del 是**旧文本**的行号。
    """
    import difflib

    a = split_lines(old)
    b = split_lines(new)
    out: list[dict[str, Any]] = []
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                out.append({"op": "same", "old": a[i1 + k], "new": b[j1 + k], "line": j1 + k})
        elif tag == "delete":
            for k in range(i1, i2):
                out.append({"op": "del", "old": a[k], "new": None, "line": k})
        elif tag == "insert":
            for k in range(j1, j2):
                out.append({"op": "add", "old": None, "new": b[k], "line": k})
        else:  # replace
            for k in range(i1, i2):
                out.append({"op": "del", "old": a[k], "new": None, "line": k})
            for k in range(j1, j2):
                out.append({"op": "add", "old": None, "new": b[k], "line": j1 + k})
    return out


# ------------------------------------------------------------------ 落盘 --
def _backup_path(ep_id: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = BACKUP_DIR / f"{ep_id}.{stamp}.md"
    n = 1
    while path.exists():
        path = BACKUP_DIR / f"{ep_id}.{stamp}-{n}.md"
        n += 1
    return path


def save_episode(ep_id: str, markdown: str, deleted: dict[str, Any] | None = None) -> dict[str, str]:
    """落盘。内部顺序：校验 → 备份 → 保留原换行风格写入 → 刷新内嵌。

    校验不通过抛 ValueError，消息里含「拒绝写入」。
    """
    path = resolve_ep_path(ep_id)
    with SAVE_LOCK:
        exists = path.exists()
        old_bytes = path.read_bytes() if exists else b""
        old = old_bytes.decode("utf-8") if exists else ""
        eol = "\r\n" if b"\r\n" in old_bytes else "\n"

        if old:
            problems = check_integrity(old, markdown, deleted)
            if problems:
                raise ValueError("拒绝写入，完整性校验未通过：" + "；".join(problems))

        backup = ""
        if exists:
            bp = _backup_path(ep_id)
            shutil.copy2(path, bp)
            backup = str(bp)

        # 保留原文件换行风格：CRLF 文件继续用 CRLF，避免 git 视整个文件全改
        out_text = to_eol(markdown, eol)
        path.write_bytes(out_text.encode("utf-8"))

        # 内嵌数据跟着更新，file:// 方式打开也能看到最新内容。
        # sync.main() 会 print，CLI 的 --json 输出必须保持干净，所以把 stdout 挪到 stderr。
        with redirect_stdout(sys.stderr):
            sync_mod.main()

    return {"path": str(path), "id": ep_id, "backup": backup, "eol": "crlf" if eol == "\r\n" else "lf"}


# ------------------------------------------------------------------ git --
def git_head_text(ep_id: str) -> str | None:
    """取 git HEAD 里的那一集文本；取不到返回 None（调用方降级为与空串比）。"""
    try:
        proc = subprocess.run(
            ["git", "show", f"HEAD:./episodes/{ep_id}.md"],
            cwd=str(ROOT), capture_output=True,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    try:
        return proc.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None


def diff_against_head(ep_id: str) -> list[dict[str, Any]]:
    """与 git HEAD 比的逐行 diff。HEAD 取不到时降级为与空串比（全是 add）。"""
    head = git_head_text(ep_id)
    try:
        current = read_episode(ep_id)
    except ValueError:
        current = ""
    return diff_lines(head or "", current)


__all__ = [
    "ROOT", "EP_DIR", "INDEX", "BACKUP_DIR",
    "list_episodes", "read_episode", "resolve_ep_path",
    "parse_episode", "parse_yaml", "set_yaml", "scene_by_id",
    "apply_ops", "check_integrity", "save_episode", "diff_lines",
    "diff_against_head", "git_head_text",
    "detect_eol", "split_lines", "join_lines", "normalize", "to_eol",
]
