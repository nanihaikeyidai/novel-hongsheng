# -*- coding: utf-8 -*-
"""按源码行锚定替换 <d>[Chinese]…</d> 台词块。

用法：JOBS 中给 (文件名, 定位前缀, 新台词)。定位前缀只需在该片段的台词首行里唯一出现。
替换范围：从含前缀的那一行起，向后延伸到第一行含 '</d>' 的行为止，整段替换为单行。
"""
import re
from pathlib import Path

HERE = Path(__file__).parent

JOBS = [
    # ---- 10c：攻守易位 ----
    ("ep04_s10_prompts.py", "你说你们找了他十二年",
     "你们找了他十二年。官方记录是因公殉职——还说他带走了你们的东西。"),
    ("ep04_s10_prompts.py", "陆沉，有些事我现在不能跟你说太细",
     "你父亲不是普通人，他做的事也不是普通事。"),
    # ---- 11a ----
    ("ep04_s11_prompts.py", "说说你自己。最近有没有觉得身体不一样",
     "说说你自己。最近身体有没有不一样？"),
    ("ep04_s11_prompts.py", "你别紧张。你父亲当年也有类似的特质",
     "你别紧张。这可能是遗传的。"),
    # ---- 11b ----
    ("ep04_s11_prompts.py", "如果你有和别人不一样的地方",
     "你有和别人不一样的地方，不用藏。这不是病，是可以控制的。"),
    ("ep04_s11_prompts.py", "我们这儿有设备、有经验",
     "学会了控制，你就能回去正常上学。"),
    # ---- 11c ----
    ("ep04_s11_prompts.py", "今天在校门口，你明明可以跟我们走",
     "今天在校门口，你可以跟我们走，你偏要跑。"),
    ("ep04_s11_prompts.py", "我不是要拿你做实验。我是想帮你。",
     "跑到巷子口，两头都堵死了。我不是想拿你做实验，是想帮你。"),
    # ---- 12d ----
    ("ep04_s12_prompts.py", "你母亲是个很优秀的研究员。",
     "你母亲是个很优秀的研究员。她发现了一些东西，一些有人不希望她查下去的东西。"),
    # ---- 12f ----
    ("ep04_s12_prompts.py", "你父亲在哪里。那天在学校",
     "你父亲在哪里。那天在你身上，发生了什么。"),
    # ---- 13b ----
    ("ep04_s13_15_prompts.py", "陆沉，我再提醒你一次。",
     "陆沉，我再提醒你一次。我能跟你好好说话，是因为这案子还在我手里。"),
    # ---- 15a ----
    ("ep04_s13_15_prompts.py", "目标防备心强，逻辑清晰",
     "目标防备心强，逻辑清晰。有一个软肋。"),
    ("ep04_s13_15_prompts.py", "提到这个话题时，情绪完全失控",
     "他母亲陈玥的死因。提到这个话题，他情绪完全失控。"),
    # ---- 15b ----
    ("ep04_s13_15_prompts.py", "不用。明天继续从母亲入手。",
     "不用。明天继续从母亲入手。他越想知道真相，就越容易被引导。"),
    ("ep04_s13_15_prompts.py", "另外，今天带队的是赵凯和小月",
     "他知道了我们叫ND。查是谁提前漏过口风。"),
]


def main():
    cache = {}
    ok = fail = 0
    for fname, prefix, new_text in JOBS:
        if fname not in cache:
            cache[fname] = (HERE / fname).read_text(encoding="utf-8").split("\n")
        lines = cache[fname]
        hits = [i for i, ln in enumerate(lines) if prefix in ln]
        if not hits:
            print(f"[FAIL] 未找到: {fname} :: {prefix}")
            fail += 1
            continue
        if len(hits) > 1:
            print(f"[WARN] {len(hits)} 处命中，取最后一处: {fname} :: {prefix}")
        start = hits[-1]
        end = next((j for j in range(start, min(start + 12, len(lines)))
                    if "</d>" in lines[j]), None)
        if end is None:
            print(f"[FAIL] 未找到 </d> 收尾: {fname} :: {prefix}")
            fail += 1
            continue
        indent = re.match(r"[ \t]*", lines[start]).group(0)
        body = new_text.replace("\\", "\\\\").replace('"', '\\"')
        new_line = f'{indent}"<Subject PLACEHOLDER>'
        # 保留原行中 <d>[Chinese] 之前的说话人标签
        pre = lines[start].split("<d>[Chinese]")[0]
        pre = pre[pre.index('"') + 1:]          # 去掉行首缩进与开引号
        tail = ""
        if "</d>" in lines[end]:
            tail = lines[end].split("</d>", 1)[1].rstrip()
        repl = f'{indent}"{pre}<d>[Chinese]{body}</d>{tail}"'
        lines[start:end + 1] = [repl]
        cache[fname] = lines
        ok += 1
        print(f"[ok] {fname} L{start+1} :: {prefix[:24]} -> {len(new_text)} 字")

    for fname, lines in cache.items():
        (HERE / fname).write_text("\n".join(lines), encoding="utf-8")
    print(f"\n成功 {ok} / 失败 {fail}")


if __name__ == "__main__":
    main()
