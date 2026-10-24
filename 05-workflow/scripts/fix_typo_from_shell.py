"""修正上一轮 shell 转义事故造成的同音错字。

背景：上一条 Bash 内联Python 里用了 \\uXXXX 转义，但反斜杠被 shell 吃掉，
导致写入的是「陆沈」「铰环」「锁芯」等同音错字（正确应为「陆沉」「铐环」「锁舌」）。
这里按文件精确修正，并做全量排查。
"""
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow")
SCRIPTS = ROOT / "scripts"
EP04 = ROOT / "ep04"

WRONG = ["陆沈", "铰环", "锁芯", "铰链"]
RIGHT = ["陆沉", "铐环", "锁舌", "铐链"]


def fix(p: Path) -> int:
    t = p.read_text(encoding="utf-8")
    orig = t
    for w, r in zip(WRONG, RIGHT):
        t = t.replace(w, r)
    if t != orig:
        p.write_text(t, encoding="utf-8")
        n = sum(orig.count(w) for w in WRONG)
        print(f"  修正 {n} 处 <- {p.name}")
        return n
    return 0


def scan(p: Path) -> None:
    t = p.read_text(encoding="utf-8")
    hit = [w for w in WRONG if w in t]
    if hit:
        print(f"  !! 仍存在错字 {hit} <- {p}")


def main() -> None:
    total = 0
    print("修正模块脚本：")
    for p in SCRIPTS.glob("ep04_*.py"):
        total += fix(p)
    print("修正已导出的片段提示词：")
    for p in EP04.glob("红绳片段*/动作流_H3纯提示词.txt"):
        total += fix(p)
    print(f"共修正 {total} 处\n")

    print("全量复查（应无输出）：")
    for p in list(SCRIPTS.glob("ep04_*.py")) + list(EP04.glob("红绳片段*/动作流_H3纯提示词.txt")):
        scan(p)
    print("复查结束")


if __name__ == "__main__":
    main()
