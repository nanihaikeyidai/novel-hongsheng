#!/usr/bin/env python3
"""剧本工作室 preview 工具的测试套件。

跑法：
    python preview/tests.py            # 全部
    python preview/tests.py core       # 只跑某一组

设计原则：
- 用临时目录里的**副本**做写入测试，绝不碰仓库里的真实 episodes/*.md
- 每个用例结束后校验：真实文件未被改动
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

PASS, FAIL = [], []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASS if cond else FAIL).append(name)
    print(f"  {'✅' if cond else '❌'} {name}" + (f"  → {detail}" if detail and not cond else ""))


def section(title: str) -> None:
    print(f"\n=== {title} ===")


# ---------------------------------------------------------------- fixtures
def make_sandbox() -> Path:
    """复制整个剧本工作室到临时目录，用作写入测试沙箱。"""
    tmp = Path(tempfile.mkdtemp(prefix="hs_preview_test_"))
    dst = tmp / "剧本工作室"
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".backups", "__pycache__", "*.pyc"))
    return dst


def git_show(path: Path, ref: str = "HEAD") -> str | None:
    r = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True,
                       cwd=path.parents[2] if len(path.parents) > 2 else None)
    return r.stdout if r.returncode == 0 else None


# ---------------------------------------------------------------- core tests
def test_core(sandbox: Path) -> None:
    import core

    section("core：解析")
    # 用 newline="" 保留原始换行符，否则 read_text 会把 CRLF 统一转成 LF，
    # 导致「CRLF 是否被保留」这类断言失真
    md = (sandbox / "episodes" / "ep06.md").read_text(encoding="utf-8", newline="")
    parsed = core.parse_episode(md)

    check("ep06 解析出 5 场", len(parsed["scenes"]) == 5, f"实际 {len(parsed['scenes'])}")
    check("场次号带字母后缀", parsed["scenes"][0]["id"] == "6-1a", parsed["scenes"][0]["id"])
    check("场次数与标题一致",
          all(s["id"] and s["titleLine"] for s in parsed["scenes"]))
    check("meta 含 status", parsed["meta"].get("status") == "定稿", str(parsed["meta"].get("status")))

    # 最后一场不得吞掉「剧情梗概」
    last = parsed["scenes"][-1]
    tail = "\n".join(parsed["lines"][last["lineStart"]: last["lineEnd"] + 1])
    check("最后一场不越界到 ## 二级标题", "## 剧情梗概" not in tail)

    # 每个块的行号必须真的指向对应类型的原文
    bad = []
    for sc in parsed["scenes"]:
        for b in sc["blocks"]:
            first = parsed["lines"][b["lineStart"]]
            ok = {
                "action": first.startswith("△"),
                "dialogue": ":" in first[:14] or "：" in first[:14],
                "note": first.startswith("【表演附注"),
                "beat": first.startswith("-") or first.startswith("**"),
            }.get(b["type"], True)
            if not ok:
                bad.append((sc["id"], b["type"], b["lineStart"], first[:30]))
    check("所有块的行号指向正确类型", not bad, str(bad[:3]))

    # 附注块：内容行数与行区间吻合
    note_bad = []
    for sc in parsed["scenes"]:
        for b in sc["blocks"]:
            if b["type"] != "note":
                continue
            seg = parsed["lines"][b["lineStart"]: b["lineEnd"] + 1]
            if not seg[0].startswith("【表演附注"):
                note_bad.append((sc["id"], "标题行不对"))
            body = [x for x in seg[1:] if x.strip()]
            if any(not x.startswith("- ") for x in body):
                note_bad.append((sc["id"], "内容行缺 '- ' 前缀"))
            if len(b["text"].split("\n")) != len(body):
                note_bad.append((sc["id"], f"text 行数 {len(b['text'].split(chr(10)))} != 原文 {len(body)}"))
    check("附注块结构正确（标题 + '- ' 内容行）", not note_bad, str(note_bad[:3]))

    section("core：apply_ops")
    # 改一句台词
    tgt = None
    for sc in parsed["scenes"]:
        for b in sc["blocks"]:
            if b["type"] == "dialogue" and b["text"] == "我来帮你。":
                tgt = (sc, b)
    check("找到目标台词「我来帮你。」", tgt is not None)
    if tgt:
        sc, b = tgt
        ops = [{"op": "replace_block", "lineStart": b["lineStart"], "lineEnd": b["lineEnd"],
                "type": "dialogue", "who": b["who"], "text": "我来帮你啊！"}]
        new_md, _ = core.apply_ops(md, ops)
        lines = new_md.split("\n")
        # 比对时剥掉行尾 \r（测试用 newline="" 读入，保留原始 CRLF）
        check("台词改写生效", lines[b["lineStart"]].rstrip("\r") == "陆沉：我来帮你啊！",
              repr(lines[b["lineStart"]]))
        check("改一行不动其他行",
              sum(1 for x, y in zip(md.split("\n"), lines) if x != y) == 1)
        check("总行数不变", len(new_md.split("\n")) == len(md.split("\n")))

        # 改动作行
        act = next(b2 for sc2 in parsed["scenes"] for b2 in sc2["blocks"]
                   if b2["type"] == "action" and "安娜撑地站起" in b2["text"])
        ops2 = [{"op": "replace_block", "lineStart": act["lineStart"], "lineEnd": act["lineEnd"],
                 "type": "action", "text": act["text"] + "（测）"}]
        md2, _ = core.apply_ops(md, ops2)
        check("动作行改写生效", "（测）" in md2.split("\n")[act["lineStart"]])

        # 改附注
        note = next(b2 for sc2 in parsed["scenes"] for b2 in sc2["blocks"] if b2["type"] == "note")
        ops3 = [{"op": "replace_block", "lineStart": note["lineStart"], "lineEnd": note["lineEnd"],
                 "type": "note", "text": note["text"].replace("节拍", "节拍（测）", 1)}]
        md3, _ = core.apply_ops(md, ops3)
        seg = md3.split("\n")[note["lineStart"]: note["lineEnd"] + 1]
        check("附注改写生效且行数不变",
              "节拍（测）" in seg[1] and len(seg) == note["lineEnd"] - note["lineStart"] + 1)

        # 删块
        ops4 = [{"op": "delete_block", "lineStart": b["lineStart"], "lineEnd": b["lineEnd"]}]
        md4, _ = core.apply_ops(md, ops4)
        check("删除块后行数减少", len(md4.split("\n")) == len(md.split("\n")) - 1)
        check("删除后该行不再是台词", "我来帮你。" not in md4)

        # 插入行
        ops5 = [{"op": "insert_after", "line": b["lineStart"], "text": "△新插入的动作"}]
        md5, _ = core.apply_ops(md, ops5)
        check("插入行生效", "△新插入的动作" in md5.split("\n")[b["lineStart"] + 1])
        check("插入后总行数 +1", len(md5.split("\n")) == len(md.split("\n")) + 1)

        # 重叠 ops 必须报错
        try:
            core.apply_ops(md, [
                {"op": "replace_block", "lineStart": b["lineStart"], "lineEnd": b["lineEnd"],
                 "type": "dialogue", "who": "陆沉", "text": "x"},
                {"op": "replace_block", "lineStart": b["lineStart"], "lineEnd": b["lineEnd"],
                 "type": "dialogue", "who": "陆沉", "text": "y"},
            ])
            check("重叠 ops 被拒绝", False, "未抛异常")
        except Exception:
            check("重叠 ops 被拒绝", True)

    section("core：完整性闸门")
    problems = core.check_integrity(md, "# 只剩一行\n")
    check("截断内容被判定有问题", len(problems) > 0, str(problems))
    check("问题信息含具体数字", any("少了" in p for p in problems), str(problems))
    problems2 = core.check_integrity(md, md, {"lines": 0, "notes": 0})
    check("原样内容通过校验", not problems2, str(problems2))

    section("core：frontmatter")
    m2 = core.set_yaml(md, "status", "草稿")
    check("set_yaml 改 status 生效", "status: 草稿" in m2)
    check("set_yaml 不动其他行",
          sum(1 for x, y in zip(md.split("\n"), m2.split("\n")) if x != y) == 1)
    check("set_yaml 保留 CRLF", "\r\n" in m2 and m2.count("\r\n") == md.count("\r\n"))

    section("core：往返幂等与前缀保真")
    # 往返幂等：用解析出的原样 text 重建，文件应逐字不变。
    # 这条能抓住「分隔符吞空格」「★/◆ 行首标记丢失」这类静默丢字符的 bug。
    for ep_file in ("ep06.md", "ep07.md"):
        raw = (sandbox / "episodes" / ep_file).read_text(encoding="utf-8", newline="")
        pp = core.parse_episode(raw)
        ops = []
        for sc in pp["scenes"]:
            for b in sc["blocks"]:
                if b["type"] == "dialogue":
                    ops.append({"op": "replace_block", "lineStart": b["lineStart"], "lineEnd": b["lineEnd"],
                                "type": "dialogue", "who": b["who"], "text": b["text"]})
                elif b["type"] == "action":
                    ops.append({"op": "replace_block", "lineStart": b["lineStart"], "lineEnd": b["lineEnd"],
                                "type": "action", "text": b["text"]})
        rebuilt, _ = core.apply_ops(raw, ops)
        o = raw.split("\r\n"); n = rebuilt.split("\r\n")
        d = sum(1 for i in range(min(len(o), len(n))) if o[i] != n[i])
        check(f"{ep_file} 往返重建逐字不变", d == 0 and len(o) == len(n), f"{d} 行差异")

    # 分隔符的尾随空白必须保留（半角冒号 + 空格）
    for raw_line, want in [("Anna: run now", "Anna: run now"),
                           ("Anna:run", "Anna:run"),
                           ("安娜：快跑", "安娜：快跑"),
                           ("安娜：  两空格", "安娜：  两空格")]:
        mini = "### 1-1 S 夜 内\n\n人物：Anna\n\n" + raw_line + "\n"
        mp = core.parse_episode(mini)
        mb = next(b for b in mp["scenes"][0]["blocks"] if b["type"] == "dialogue")
        mops = [{"op": "replace_block", "lineStart": mb["lineStart"], "lineEnd": mb["lineEnd"],
                 "type": "dialogue", "who": mb["who"], "text": mb["text"]}]
        mn, _ = core.apply_ops(mini, mops)
        got = mn.split("\n")[mb["lineStart"]]
        check(f"分隔符保真 {raw_line!r}", got == want, f"得到 {got!r}")

    # 行首 ★/◆ 高光标记必须保留
    mini2 = "### 1-1 S 夜 内\n\n人物：A\n\n★△带星号的动作\n"
    mp2 = core.parse_episode(mini2)
    mb2 = next(b for b in mp2["scenes"][0]["blocks"] if b["type"] == "action")
    mn2, _ = core.apply_ops(mini2, [{"op": "replace_block", "lineStart": mb2["lineStart"],
                                     "lineEnd": mb2["lineEnd"], "type": "action", "text": "新动作"}])
    got2 = mn2.split("\n")[mb2["lineStart"]]
    check("行首 ★ 标记保留", got2.startswith("★"), f"得到 {got2!r}")

    section("core：diff_lines")
    d = core.diff_lines(md, md2)
    check("diff 能报出改动行", any(x["op"] != "same" for x in d))
    check("diff 标注行号", all("line" in x for x in d))


# ---------------------------------------------------------------- cli tests
def test_cli(sandbox: Path) -> None:
    section("cli：命令可用")
    ep = sandbox / "episodes" / "ep06.md"
    before = ep.read_bytes()

    def cli(*args, expect_ok=True):
        r = subprocess.run([sys.executable, str(sandbox / "preview" / "cli.py"), *args],
                           capture_output=True, text=True, cwd=sandbox)
        return r

    r = cli("list", "--json")
    check("cli list 返回 JSON", r.returncode == 0 and "ep06" in r.stdout, r.stderr[:200])

    r = cli("parse", "ep06", "--json")
    check("cli parse 返回结构化结果", r.returncode == 0 and '"scenes"' in r.stdout, r.stderr[:200])

    r = cli("show", "ep06", "--json")
    check("cli show 返回内容", r.returncode == 0 and len(r.stdout) > 100, r.stderr[:200])

    # 找一行台词来改
    parsed_json = json.loads(cli("parse", "ep06", "--json").stdout)
    # parse --json 的结构：{"ok":true,"id":...,"meta":{...},"parsed":{"scenes":[...]}}
    root = parsed_json.get("parsed", parsed_json)
    scene = next(s for s in root["scenes"] if s["id"] == "6-1b")
    dlg = next(b for b in scene["blocks"] if b["type"] == "dialogue" and b["text"] == "我来帮你。")

    r = cli("set", "ep06", "--block", f"{dlg['lineStart']}:{dlg['lineEnd']}",
            "--type", "dialogue", "--text", "我来帮你啊！", "--json")
    check("cli set 成功", r.returncode == 0, (r.stdout + r.stderr)[:200])

    after = ep.read_text(encoding="utf-8", newline="")
    lines = after.split("\n")
    check("cli 写入生效", lines[dlg["lineStart"]].rstrip("\r") == "陆沉：我来帮你啊！",
          repr(lines[dlg["lineStart"]]))
    # 比对必须用同样的换行处理：before 是原始字节，after 用 newline="" 保留 CRLF
    before_text = before.decode("utf-8")
    diff_count = sum(1 for x, y in zip(before_text.split("\n"), lines) if x != y)
    check("cli 改一行只动一行", diff_count == 1, f"动了 {diff_count} 行")

    # 备份应生成
    baks = list((sandbox / "preview" / ".backups").glob("ep06.*.md")) if (sandbox / "preview" / ".backups").exists() else []
    check("cli 保存生成备份", len(baks) > 0, f"{len(baks)} 个")

    # 完整性闸门：截断内容必须被拒
    r = subprocess.run([sys.executable, "-c", f"""
import sys; sys.path.insert(0, {str(sandbox / 'preview')!r})
import core
try:
    core.save_episode('ep06', '# 截断\\n')
    print('NOT_BLOCKED')
except ValueError as e:
    print('BLOCKED', e)
"""], capture_output=True, text=True)
    check("core 拒绝截断内容", "BLOCKED" in r.stdout and "拒绝写入" in r.stdout, r.stdout[:200])
    check("被拒后文件未变", ep.read_bytes() == after.encode("utf-8"),
          "闸门拒绝后文件仍被改动")

    # 还原沙箱：cli 组改过的文件必须恢复，否则会污染后续 web 组
    ep.write_bytes(before)
    check("cli 组已还原沙箱", ep.read_bytes() == before)


# ---------------------------------------------------------------- web tests
def test_web(sandbox: Path) -> None:
    section("web：端到端")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  ⚠️ 未装 playwright，跳过 web 端到端")
        return

    port = 8899
    proc = subprocess.Popen(
        [sys.executable, str(sandbox / "preview" / "server.py"), "--port", str(port), "--no-open"],
        cwd=sandbox, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        import time
        time.sleep(2.5)
        ep = sandbox / "episodes" / "ep06.md"
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.goto(f"http://127.0.0.1:{port}/", wait_until="networkidle")

            heads = pg.eval_on_selector_all(".scene-head", "els=>els.map(e=>e.textContent.trim())")
            check("页面渲染出 5 场", len(heads) == 5, str(heads))
            check("场次号含字母后缀", any("6-1a" in h for h in heads), str(heads))

            pg.click("#btnEdit")
            pg.wait_for_timeout(500)
            check("进入编辑态", "editing" in pg.eval_on_selector("body", "e=>e.className"))

            # ---- 新增能力：撤销（需要有未保存改动）----
            pg.evaluate("""() => {
              const e = [...document.querySelectorAll("[data-part='text']")]
                .find(x => x.textContent.trim() === '我来帮你。');
              e.focus();
              const t = e.firstChild;
              const r = document.createRange();
              r.setStart(t, t.textContent.length); r.collapse(true);
              const s = getSelection(); s.removeAllRanges(); s.addRange(r);
              document.execCommand('insertText', false, 'X');
            }""")
            pg.wait_for_timeout(400)
            undo_ok = not pg.eval_on_selector("#btnUndo", "e=>e.disabled")
            check("撤销按钮可用", undo_ok)
            if undo_ok:
                pg.click("#btnUndo"); pg.wait_for_timeout(600)
                check("撤销后脏标记清空", pg.eval_on_selector("#dirtyFlag", "e=>e.textContent").strip() == "")
                check("撤销后内容还原", pg.evaluate(
                    "()=>[...document.querySelectorAll(\"[data-part='text']\")].some(x=>x.textContent.trim()==='我来帮你。')"))

            # 改一句台词
            # 前端用 data-part 标记可编辑部分（who / text），行号存在编辑模型里
            idx = pg.evaluate("""() => {
              const els=[...document.querySelectorAll("[data-part='text']")];
              return els.findIndex(e=>e.textContent.trim()==='我来帮你。');
            }""")
            check("找到可编辑台词", idx >= 0, str(idx))
            if idx >= 0:
                el = pg.query_selector_all("[data-part='text']")[idx]
                # 把光标精确放到文本末尾再输入。
                # 不能用 End 键：光标会落在句号之后，插成「我来帮你。啊」。
                pg.evaluate("""(el) => {
                  const t = el.firstChild;
                  const r = document.createRange();
                  r.setStart(t, t.textContent.length);
                  r.collapse(true);
                  const s = getSelection();
                  s.removeAllRanges();
                  s.addRange(r);
                  el.focus();
                }""", el)
                # 用 ASCII 字符测试：Playwright 逐字符 type 中文时会走 IME 合成路径，
                # 字符可能被插到标点之后（如「我来帮你。啊」），那是测试工具的问题，不是被测代码的问题。
                pg.keyboard.type("X")
                pg.wait_for_timeout(300)
                check("改动被标记为脏", "●" in pg.eval_on_selector("#dirtyFlag", "e=>e.textContent"))

                # 新流程：点保存 → 弹「保存前预览」模态框 → 确认写回
                pg.click("#btnSave")
                pg.wait_for_timeout(600)
                modal_on = pg.evaluate("()=>document.getElementById('diffModal').classList.contains('on')")
                check("保存前弹出 diff 预览", modal_on)
                note = pg.eval_on_selector("#diffNote", "e=>e.textContent")
                check("预览显示改动数", "1" in note, note)

                pg.click("#btnDiffOk")
                pg.wait_for_timeout(2500)
                result = pg.eval_on_selector("#diffNote", "e=>e.textContent")
                check("写回后展示结果", "新增" in result or "没有变化" in result, result)

                content = ep.read_text(encoding="utf-8", newline="")
                check("web 写入生效", "我来帮你。X" in content,
                      f"沙箱文件里是: {[l for l in content.split(chr(10)) if '我来帮你' in l][:2]}")
                check("web 只改目标行", content.count("我来帮你。X") == 1)

            # ---- 新增能力：frontmatter 编辑 ----
            pg.click("#btnDiffCancel"); pg.wait_for_timeout(500)
            opts = pg.eval_on_selector_all("#fStatus option", "els=>els.map(e=>e.value)")
            check("frontmatter status 是下拉框", "定稿" in opts, str(opts))
            pg.select_option("#fStatus", "定稿候选")
            pg.wait_for_timeout(300)
            check("改 frontmatter 后标脏", "●" in pg.eval_on_selector("#dirtyFlag", "e=>e.textContent"))
            pg.click("#btnSave"); pg.wait_for_timeout(700)
            pg.click("#btnDiffOk"); pg.wait_for_timeout(2200)
            c2 = ep.read_text(encoding="utf-8", newline="")
            check("frontmatter 写回生效", "status: 定稿候选" in c2)
            pg.click("#btnDiffCancel"); pg.wait_for_timeout(500)

            # ---- 新增能力：插入新动作行 ----
            add = pg.query_selector("[data-add='action']")
            check("有「＋动作」插入按钮", add is not None)
            if add:
                add.click(); pg.wait_for_timeout(500)
                inp = pg.query_selector("[data-ins] .ins-input")
                check("插入输入框出现", inp is not None)
                if inp:
                    inp.click()
                    pg.keyboard.type("△NEWACTION")
                    pg.wait_for_timeout(300)
                    pg.click("#btnSave"); pg.wait_for_timeout(700)
                    pg.click("#btnDiffOk"); pg.wait_for_timeout(2200)
                    c3 = ep.read_text(encoding="utf-8", newline="")
                    check("插入行写回生效", "△NEWACTION" in c3)
                    pg.click("#btnDiffCancel"); pg.wait_for_timeout(500)

            check("全程无页面错误", not errs, str(errs[:3]))
            b.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


# ---------------------------------------------------------------- main
def main() -> int:
    groups = sys.argv[1:] or ["core", "cli", "web"]
    sandbox = make_sandbox()
    print(f"沙箱：{sandbox}")
    real = ROOT / "episodes" / "ep06.md"
    real_before = real.read_bytes()

    try:
        if "core" in groups:
            test_core(sandbox)
        if "cli" in groups:
            test_cli(sandbox)
        if "web" in groups:
            test_web(sandbox)
    finally:
        check("真实 episodes/ep06.md 未被测试改动", real.read_bytes() == real_before)
        shutil.rmtree(sandbox.parent, ignore_errors=True)

    print(f"\n{'=' * 50}")
    print(f"通过 {len(PASS)} 项，失败 {len(FAIL)} 项")
    if FAIL:
        print("失败项：")
        for f in FAIL:
            print("  -", f)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
