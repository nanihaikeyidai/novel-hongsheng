#!/usr/bin/env python3
"""《红绳》剧本工作室 · Agent 命令行（cli.py）

给 AI Agent / 脚本用的读写入口。所有写入都走 preview/core.py（唯一写入通道）：
完整性闸门 → 备份 → 保留 CRLF 落盘 → 刷新 index.html 内嵌。

════════════════════ 用法速查 ════════════════════
    python preview/cli.py list                        # 列出所有集
    python preview/cli.py show ep06                   # 打印整集
    python preview/cli.py show ep06 --scene 6-1a      # 只看某一场
    python preview/cli.py parse ep06                  # 结构化解析（行号 + 块）
    python preview/cli.py set ep06 --block 125:127 --type dialogue --text "我来帮你。"
    python preview/cli.py set ep06 --line 130 --text "△安娜头也不回。"
    python preview/cli.py del ep06 --block 125:127
    python preview/cli.py ins ep06 --after 125 --text "△新动作"
    python preview/cli.py replace ep06 --find "我来帮你。" --replace "我来帮你啊！"
    python preview/cli.py meta ep06 --set status=定稿
    python preview/cli.py diff ep06                   # 与 git HEAD 比
    python preview/cli.py check ep06                  # 完整性自检（不落盘）

所有子命令都支持 --json（可放在子命令前或后）。给 Agent 的调用范例：

    # 改一句台词，确认只有这一行变了
    python preview/cli.py set ep06 --block 125:127 --type dialogue \\
        --text "我来帮你啊！" --json
    # → {"ok": true, "id": "ep06", "changed": 1, "diff": [...]}

    # 批量管道：正文从 stdin 读（省掉 shell 引号地狱）
    echo "我来帮你啊！" | python preview/cli.py set ep06 --block 125:127 \\
        --type dialogue --json

    # 只读查询，绝不碰磁盘
    python preview/cli.py parse ep06 --json

约定（务必读）：
- 行号一律 **0 基绝对行号**，指向原文；--block A:B 是闭区间。
- --block 的 --text 是**正文**（不含 △、不含「说话人：」），由 core 按 type 补前缀。
- --line / --after 的 --text 是**整行原文**（要自带 △ 或「说话人：」）。
- --block 会先在区间里定位目标类型的行（台词行 / 动作行 / 附注段），
  只替换这些行，区间里的空行与其它内容保持原样。
- 退出码：0 成功；1 被完整性闸门拒绝或参数非法；2 命令行用法错误。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import core  # noqa: E402

EXIT_OK = 0
EXIT_FAIL = 1


# ------------------------------------------------------------------ 输出 --
def emit_json(obj: dict[str, Any]) -> None:
    """机器可读输出：只往 stdout 打一个 JSON 对象。"""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def fail(msg: str, as_json: bool, **extra: Any) -> int:
    if as_json:
        emit_json({"ok": False, "error": msg, **extra})
    else:
        print(f"❌ {msg}", file=sys.stderr)
    return EXIT_FAIL


def read_text_arg(value: str | None, what: str) -> str:
    """--text 缺省时从 stdin 读（Agent 管道友好）。"""
    if value is not None:
        return value
    if sys.stdin is None or sys.stdin.isatty():
        raise ValueError(f"缺少 --text，且当前是交互终端，无法从 stdin 读取{what}")
    data = sys.stdin.read().replace("\r\n", "\n")
    return data.rstrip("\n")


def changed_only(diff: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """只保留 del/add（same 行没有信息量，Agent 不用看）。"""
    return [d for d in diff if d.get("op") != "same"]


def count_changed(diff: list[dict[str, Any]]) -> int:
    """统计「变了几行」。

    diff 是逐行的 del/add 序列：改一行会给出 1 个 del + 1 个 add，
    直接数条目会算成 2。这里按连续变更块算，改一行 = 1。
    """
    import itertools

    n = 0
    for _op, group in itertools.groupby(
        diff, key=lambda d: 0 if d.get("op") != "same" else 1
    ):
        items = list(group)
        if items and items[0].get("op") != "same":
            n += max(sum(1 for d in items if d["op"] == "del"),
                     sum(1 for d in items if d["op"] == "add"))
    return n


# ------------------------------------------------------------------ 读集 --
def load_ep(ep_id: str) -> tuple[str, dict[str, Any]]:
    """读一集原文 + 解析结果。"""
    md = core.read_episode(ep_id)
    return md, core.parse_episode(md)


# ------------------------------------------------------- 目标行定位 --
def _line_type(lines: list[str], i: int) -> str:
    """判断某一行属于哪种块类型（用于 --block 定位目标行）。"""
    line = lines[i]
    if core.RE_NOTE_HEAD.match(line):
        return "note"
    if line.startswith("△") or line.startswith("◆△") or line.startswith("★△"):
        return "action"
    m = core.RE_DIALOGUE_LINE.match(line)
    if m and m.group(1) not in core.META_LABELS:
        return "dialogue"
    m = core.RE_BULLET_DIALOGUE.match(line)
    if m and m.group(1) not in core.META_LABELS:
        return "dialogue"
    return "beat"


def find_targets(lines: list[str], start: int, end: int, btype: str) -> list[tuple[int, int]]:
    """在闭区间 [start, end] 里找出该类型的行。

    返回 [(行号, 行号)]；附注返回整个附注段（头行 + 正文行）。
    """
    hits: list[tuple[int, int]] = []
    i = start
    while i <= end:
        t = _line_type(lines, i)
        if btype == "note":
            if t == "note":
                j = i + 1
                while j <= end and lines[j].lstrip().startswith("-"):
                    j += 1
                hits.append((i, j - 1))
                i = j
                continue
        elif t == btype:
            hits.append((i, i))
        i += 1
    return hits


def infer_type(lines: list[str], start: int, end: int) -> str:
    """--type 缺省时，从区间内第一个非空行推断块类型。"""
    for i in range(start, min(end, len(lines) - 1) + 1):
        if lines[i].strip():
            return _line_type(lines, i)
    return "beat"


# ------------------------------------------------------------- 写操作出口 --
def do_write(ep_id: str, new_md: str, deleted: dict[str, int], as_json: bool,
             action: str, **extra: Any) -> int:
    """统一写出口：闸门 → 备份 → 落盘 → 刷新内嵌 → 回报 diff。"""
    old_md = core.read_episode(ep_id)
    problems = core.check_integrity(old_md, new_md, deleted)
    if problems:
        return fail("拒绝写入，完整性校验未通过：" + "；".join(problems), as_json, **extra)
    try:
        info = core.save_episode(ep_id, new_md, deleted)
    except ValueError as exc:
        return fail(str(exc), as_json, **extra)
    diff = changed_only(core.diff_lines(old_md, new_md))
    changed = count_changed(core.diff_lines(old_md, new_md))
    if as_json:
        emit_json({
            "ok": True,
            "id": ep_id,
            "action": action,
            "changed": changed,
            "deleted": deleted.get("lines", 0),
            "path": info.get("path"),
            "backup": info.get("backup"),
            "diff": diff,
            **extra,
        })
    else:
        print(f"✅ 已写入 {ep_id}.md（{action}，{changed} 处变化）")
        for d in diff:
            if d.get("op") == "del":
                print(f"  - [{d['line']}] {d.get('old')}")
            else:
                print(f"  + [{d['line']}] {d.get('new')}")
    return EXIT_OK


# --------------------------------------------------------------- 子命令 --
def cmd_list(args: argparse.Namespace) -> int:
    eps = core.list_episodes()
    if args.json:
        emit_json({
            "ok": True,
            "episodes": [
                {
                    "id": e["id"],
                    "title": e["meta"].get("title", ""),
                    "status": e["meta"].get("status", ""),
                    "updated": e["meta"].get("updated", ""),
                    "meta": e["meta"],
                }
                for e in eps
            ],
        })
        return EXIT_OK
    if not eps:
        print("（没有找到任何集）")
        return EXIT_OK
    print(f"{'集号':<8}{'状态':<8}{'更新':<14}标题")
    for e in eps:
        m = e["meta"]
        print(f"{e['id']:<8}{m.get('status','') or '—':<8}{m.get('updated','') or '—':<14}{m.get('title','')}")
    return EXIT_OK


def cmd_show(args: argparse.Namespace) -> int:
    md, parsed = load_ep(args.id)
    if args.scene:
        sc = core.scene_by_id(parsed, args.scene)
        if sc is None:
            return fail(f"没有找到场次 {args.scene}（{args.id}）", args.json)
        lines = core.split_lines(md)
        text = "\n".join(lines[sc["lineStart"]: sc["lineEnd"] + 1])
        if args.json:
            emit_json({"ok": True, "id": args.id, "scene": sc, "markdown": text})
            return EXIT_OK
        print(f"# {sc['heading']}")
        print(f"人物：{'、'.join(sc['characters']) or '（未标注）'}")
        print(f"行号：{sc['lineStart']}–{sc['lineEnd']}")
        print()
        print(text)
        return EXIT_OK
    if args.json:
        emit_json({"ok": True, "id": args.id, "meta": parsed["meta"], "markdown": md})
        return EXIT_OK
    print(md)
    return EXIT_OK


def cmd_parse(args: argparse.Namespace) -> int:
    md, parsed = load_ep(args.id)
    if args.json:
        emit_json({"ok": True, "id": args.id, "meta": parsed["meta"], "parsed": parsed})
        return EXIT_OK
    print(f"== {args.id} ==")
    print(f"frontmatter：{parsed['meta']}")
    print(f"分场表 {len(parsed['sceneTable'])} 行，正文 {len(parsed['lines'])} 行，换行 {parsed['eol']!r}")
    for sc in parsed["scenes"]:
        print()
        print(f"### {sc['heading']}  [行 {sc['lineStart']}–{sc['lineEnd']}]")
        print(f"    人物：{'、'.join(sc['characters']) or '（未标注）'}")
        for b in sc["blocks"]:
            who = f"{b['who']}：" if b.get("who") else ""
            body = (b.get("text") or "").replace("\n", " ⏎ ")
            print(f"    {b['lineStart']:>4}-{b['lineEnd']:<4} {b['type']:<9}{who}{body}")
    return EXIT_OK


def cmd_set(args: argparse.Namespace) -> int:
    md, _parsed = load_ep(args.id)
    lines = core.split_lines(md)
    n = len(lines)

    if args.block:
        m = re.fullmatch(r"(\d+)\s*:\s*(\d+)", args.block.strip())
        if not m:
            return fail("--block 需要 '起始:结束' 形式（0 基闭区间）", args.json)
        start, end = int(m.group(1)), int(m.group(2))
    elif args.line is not None:
        start = end = args.line
    else:
        return fail("必须给 --block A:B 或 --line N", args.json)

    if start < 0 or end < start or end >= n:
        return fail(f"行区间 {start}:{end} 超出正文范围（共 {n} 行，0 基）", args.json)

    try:
        text = read_text_arg(args.text, "正文")
    except ValueError as exc:
        return fail(str(exc), args.json)

    if args.line is not None:
        op: dict[str, Any] = {"op": "replace_line", "line": start, "text": text}
        action = f"替换行 {start}"
    else:
        btype = args.type or infer_type(lines, start, end)
        if btype not in core.BLOCK_TYPES:
            return fail(f"--type 非法：{btype}（可选 {'/'.join(core.BLOCK_TYPES)}）", args.json)
        targets = find_targets(lines, start, end, btype)
        if not targets:
            return fail(f"区间 {start}:{end} 内没有 {btype} 类型的行", args.json)
        # 正文按目标切分：
        #   台词/动作/拍子——每个目标一行，正文按 \n 逐行分配（多退少补由 core 处理）
        #   附注——整段正文（可多行）给唯一的那个附注目标
        ops: list[dict[str, Any]] = []
        if btype == "note":
            if len(targets) > 1:
                return fail(f"区间 {start}:{end} 内有 {len(targets)} 段附注，请缩小范围", args.json)
            s, e = targets[0]
            ops.append({
                "op": "replace_block", "lineStart": s, "lineEnd": e,
                "type": "note", "text": text,
            })
        else:
            parts = text.split("\n") if text != "" else []
            if len(parts) < len(targets):
                parts = parts + [""] * (len(targets) - len(parts))
            elif len(parts) > len(targets):
                return fail(
                    f"正文有 {len(parts)} 行，但区间 {start}:{end} 内只有 {len(targets)} 处 {btype}；"
                    "请缩小范围或改成一次改一处",
                    args.json,
                )
            for k, (s, e) in enumerate(targets):
                op = {
                    "op": "replace_block", "lineStart": s, "lineEnd": e,
                    "type": btype, "text": parts[k],
                }
                if args.who and btype == "dialogue":
                    op["who"] = args.who
                ops.append(op)
        action = f"替换 {btype}（行 {start}:{end} 内 {len(targets)} 处）"

    try:
        new_md, _summary = core.apply_ops(md, [op] if args.line is not None else ops)
    except ValueError as exc:
        return fail(str(exc), args.json)
    # 放行量按「被圈住的行里有几行内容」算。
    # 这样「把一句台词改成动作行」这种合法编辑能过闸，
    # 但圈外的内容丢失仍然会被拦下。
    ranges = core.op_ranges([op] if args.line is not None else ops)
    deleted = core.deleted_allowance(md, ranges)
    return do_write(args.id, new_md, deleted, args.json, action)


def cmd_del(args: argparse.Namespace) -> int:
    md, _parsed = load_ep(args.id)
    lines = core.split_lines(md)
    m = re.fullmatch(r"(\d+)\s*:\s*(\d+)", (args.block or "").strip())
    if not m:
        return fail("--block 需要 '起始:结束' 形式（0 基闭区间）", args.json)
    start, end = int(m.group(1)), int(m.group(2))
    if start < 0 or end < start or end >= len(lines):
        return fail(f"行区间 {start}:{end} 超出正文范围（共 {len(lines)} 行，0 基）", args.json)

    op = {"op": "delete_block", "lineStart": start, "lineEnd": end}
    try:
        new_md, _summary = core.apply_ops(md, [op])
    except ValueError as exc:
        return fail(str(exc), args.json)
    # 放行量按「被删掉的行里有多少内容行」算，而不是区间长度——
    # 删掉 10 行空行不该顺带放行删掉别处的台词。
    deleted = core.deleted_allowance(md, [(start, end)])
    return do_write(args.id, new_md, deleted, args.json, f"删除块 {start}:{end}")


def cmd_ins(args: argparse.Namespace) -> int:
    md, _parsed = load_ep(args.id)
    lines = core.split_lines(md)
    if args.after < 0 or args.after >= len(lines):
        return fail(f"插入位置 {args.after} 超出正文范围（共 {len(lines)} 行，0 基）", args.json)
    try:
        text = read_text_arg(args.text, "整行原文")
    except ValueError as exc:
        return fail(str(exc), args.json)
    op = {"op": "insert_after", "line": args.after, "text": text}
    try:
        new_md, _summary = core.apply_ops(md, [op])
    except ValueError as exc:
        return fail(str(exc), args.json)
    return do_write(args.id, new_md, {"lines": 0, "notes": 0}, args.json,
                    f"在第 {args.after} 行后插入")


def cmd_replace(args: argparse.Namespace) -> int:
    """全文精确替换（可跨行），命中多处逐条列出（行号 + 前后文）。"""
    md, _parsed = load_ep(args.id)
    eol = core.detect_eol(md)
    norm = core.normalize(md)
    needle = args.find
    if needle == "":
        return fail("--find 不能为空", args.json)

    hits: list[dict[str, Any]] = []
    pos = 0
    while True:
        idx = norm.find(needle, pos)
        if idx < 0:
            break
        line_no = norm.count("\n", 0, idx)
        line_start = norm.rfind("\n", 0, idx) + 1
        line_end = norm.find("\n", idx)
        if line_end < 0:
            line_end = len(norm)
        hits.append({
            "index": len(hits) + 1,
            "line": line_no,
            "before": norm[line_start:idx],
            "match": norm[idx:idx + len(needle)],
            "after": norm[idx + len(needle):line_end],
        })
        pos = idx + len(needle)

    if not hits:
        return fail(f"没有找到「{needle}」", args.json)

    new_norm = norm.replace(needle, args.replace)
    new_md = core.to_eol(new_norm, eol)
    # 全文替换：被替换掉的整行算「主动删除」，按它算放行量。
    # 没被替换的同行改写不算删除。
    deleted = removed_stats(md, new_md)

    return do_write(args.id, new_md, deleted, args.json,
                    f"全文替换 {len(hits)} 处", hits=hits)


def removed_stats(old: str, new: str) -> dict[str, int]:
    """统计这次改动**净删掉**了多少台词行 / 动作行 / 附注段。

    只算「整行消失」，被改写的行算修改不算删除——否则任何一句改写都会被
    当成删除，完整性闸门就形同虚设了。
    """
    import difflib

    a = core.split_lines(old)
    b = core.split_lines(new)
    removed: list[str] = []
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "delete":
            removed.extend(a[i1:i2])
        elif tag == "replace":
            extra = (i2 - i1) - (j2 - j1)
            if extra > 0:
                removed.extend(a[i1 + (j2 - j1):i2])
    dlg = sum(1 for ln in removed if core.RE_DIALOGUE.match(ln))
    act = sum(1 for ln in removed if core.RE_ACTION.match(ln))
    note = sum(1 for ln in removed if core.RE_NOTE.match(ln))
    return {"lines": max(dlg, act), "notes": note}


def cmd_meta(args: argparse.Namespace) -> int:
    md, parsed = load_ep(args.id)
    if not args.set:
        if args.json:
            emit_json({"ok": True, "id": args.id, "meta": parsed["meta"]})
            return EXIT_OK
        for k, v in parsed["meta"].items():
            print(f"{k}: {v}")
        return EXIT_OK

    pairs: list[tuple[str, str]] = []
    for item in args.set:
        if "=" not in item:
            return fail(f"--set 需要 '键=值' 形式，收到：{item}", args.json)
        k, v = item.split("=", 1)
        k = k.strip()
        if not k:
            return fail(f"--set 的键不能为空：{item}", args.json)
        pairs.append((k, v))

    new_md = md
    try:
        for k, v in pairs:
            new_md = core.set_yaml(new_md, k, v)
    except ValueError as exc:
        return fail(str(exc), args.json)
    return do_write(args.id, new_md, {"lines": 0, "notes": 0}, args.json,
                    "改 frontmatter：" + "、".join(k for k, _ in pairs))


def cmd_diff(args: argparse.Namespace) -> int:
    diff = core.diff_against_head(args.id)
    changed = changed_only(diff)
    if args.json:
        emit_json({"ok": True, "id": args.id, "changed": len(changed), "diff": changed})
        return EXIT_OK
    if not changed:
        print(f"{args.id}：与 git HEAD 一致")
        return EXIT_OK
    print(f"{args.id}：与 git HEAD 有 {len(changed)} 处差异")
    for d in changed:
        if d.get("op") == "del":
            print(f"  - [{d['line']}] {d.get('old')}")
        else:
            print(f"  + [{d['line']}] {d.get('new')}")
    return EXIT_OK


def cmd_check(args: argparse.Namespace) -> int:
    """完整性自检：只读，不落盘。"""
    md, parsed = load_ep(args.id)
    problems: list[str] = []

    if not parsed["meta"]:
        problems.append("缺少 frontmatter（yaml 块）")
    for key in ("id", "title"):
        if key not in parsed["meta"]:
            problems.append(f"frontmatter 缺少 {key}")

    if not parsed["scenes"]:
        problems.append("没有解析到场次（### 6-1a 形式）")

    for sc in parsed["scenes"]:
        if not sc["blocks"]:
            problems.append(f"场次 {sc['id']} 没有任何内容块")
        if not sc["characters"]:
            problems.append(f"场次 {sc['id']} 缺少「人物：」行")
        for b in sc["blocks"]:
            if b["type"] == "note":
                for ln in (b.get("text") or "").split("\n"):
                    if ln.strip() and not ln.lstrip().startswith("-"):
                        problems.append(f"场次 {sc['id']} 附注行缺 '- ' 前缀：{ln[:30]}")
            if b["type"] == "dialogue":
                if not b.get("who"):
                    problems.append(f"场次 {sc['id']} 第 {b['lineStart']} 行台词缺说话人")
                if "*" in (b.get("who") or ""):
                    problems.append(
                        f"场次 {sc['id']} 第 {b['lineStart']} 行疑似把梗概行当台词：{b.get('text','')[:30]}"
                    )

    # 与 git HEAD 比：如果比 HEAD 少了内容，多半是被误删了
    head = core.git_head_text(args.id)
    if head:
        for label, pat in (("台词行", core.RE_DIALOGUE), ("动作行", core.RE_ACTION),
                           ("表演附注段", core.RE_NOTE)):
            o = len(pat.findall(core.normalize(head)))
            n = len(pat.findall(core.normalize(md)))
            if n < o:
                problems.append(f"比 git HEAD 少了 {o - n} 个{label}（{o} → {n}）")

    diff = changed_only(core.diff_against_head(args.id))
    counts = {
        "台词行": len(core.RE_DIALOGUE.findall(core.normalize(md))),
        "动作行": len(core.RE_ACTION.findall(core.normalize(md))),
        "附注段": len(core.RE_NOTE.findall(core.normalize(md))),
        "场次": len(parsed["scenes"]),
        "与HEAD差异": len(diff),
    }
    if args.json:
        emit_json({"ok": not problems, "id": args.id, "problems": problems, "counts": counts})
        return EXIT_OK if not problems else EXIT_FAIL
    if problems:
        print(f"❌ {args.id} 自检发现 {len(problems)} 个问题：")
        for p in problems:
            print(f"  - {p}")
    else:
        print(f"✅ {args.id} 自检通过")
    print("统计：" + "、".join(f"{k} {v}" for k, v in counts.items()))
    return EXIT_OK if not problems else EXIT_FAIL


# ------------------------------------------------------------------ 入口 --
def build_parser() -> argparse.ArgumentParser:
    # --json 同时允许放在子命令前后：父解析器与各子解析器都定义它，
    # 用 SUPPRESS 作默认值，子解析器不会把父级已经设好的 True 冲掉。
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                        help="机器可读输出（JSON）")

    ap = argparse.ArgumentParser(
        prog="preview/cli.py",
        description="《红绳》剧本工作室 · Agent 命令行（写入走 core.py 唯一通道）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n"
               "  python preview/cli.py list --json\n"
               "  python preview/cli.py set ep06 --block 125:127 --type dialogue --text \"我来帮你啊！\" --json\n"
               "  echo \"再来一刀\" | python preview/cli.py set ep06 --block 125:127 --type dialogue --json\n",
    )
    ap.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                    help="机器可读输出（JSON）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", parents=[common], help="列出所有集")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show", parents=[common], help="打印整集或某一场")
    p.add_argument("id")
    p.add_argument("--scene", help="只看某一场（场次号，如 6-1a）")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("parse", parents=[common], help="输出结构化解析结果（行号 + 块）")
    p.add_argument("id")
    p.set_defaults(func=cmd_parse)

    p = sub.add_parser("set", parents=[common], help="改一个块或一行")
    p.add_argument("id")
    p.add_argument("--block", help="0 基绝对行号闭区间，如 125:127")
    p.add_argument("--line", type=int, help="0 基绝对行号，单行")
    p.add_argument("--type", choices=list(core.BLOCK_TYPES), help="块类型（--block 用，缺省自动推断）")
    p.add_argument("--text", help="内容（缺省从 stdin 读）")
    p.add_argument("--who", help="说话人（仅 --block --type dialogue）")
    p.set_defaults(func=cmd_set)

    p = sub.add_parser("del", parents=[common], help="删一个块")
    p.add_argument("id")
    p.add_argument("--block", required=True, help="0 基绝对行号闭区间，如 125:127")
    p.set_defaults(func=cmd_del)

    p = sub.add_parser("ins", parents=[common], help="在某行之后插入一行")
    p.add_argument("id")
    p.add_argument("--after", type=int, required=True, help="0 基绝对行号")
    p.add_argument("--text", help="整行原文（缺省从 stdin 读）")
    p.set_defaults(func=cmd_ins)

    p = sub.add_parser("replace", parents=[common], help="全文精确替换")
    p.add_argument("id")
    p.add_argument("--find", required=True, help="要替换的原文")
    p.add_argument("--replace", required=True, help="替换成什么")
    p.set_defaults(func=cmd_replace)

    p = sub.add_parser("meta", parents=[common], help="查看 / 修改 frontmatter")
    p.add_argument("id")
    p.add_argument("--set", action="append", metavar="K=V", help="设置键值（可多次）")
    p.set_defaults(func=cmd_meta)

    p = sub.add_parser("diff", parents=[common], help="与 git HEAD 比")
    p.add_argument("id")
    p.set_defaults(func=cmd_diff)

    p = sub.add_parser("check", parents=[common], help="完整性自检（不落盘）")
    p.add_argument("id")
    p.set_defaults(func=cmd_check)

    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    as_json = bool(getattr(args, "json", False))
    args.json = as_json
    try:
        return int(args.func(args))
    except ValueError as exc:
        return fail(str(exc), as_json)
    except FileNotFoundError as exc:
        return fail(f"文件不存在：{exc}", as_json)


if __name__ == "__main__":
    sys.exit(main())
