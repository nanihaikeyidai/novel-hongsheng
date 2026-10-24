"""R2T2 反推台词 QC 门禁（EP04 审讯线）。

从「一次性诊断报告」升级为可复用的门禁：退出码非 0 即代表台词不合格，
可直接接入每集渲染后的自动化检查链。

实测阈值来源（2026-10-18，Confucius4-R2T2 反推 EP04 终版 60 秒音轨）：
  · 整段台词 ≤ 30 字：15 秒里 H3 塞不下 34 字，会拖长/复读来填时长
  · 单句台词 ≤ 16 字：超过就容易出现同音错字（「适适」←「到底」）

门禁项：
  1. 台词密度    —— 每段总字数超阈值
  2. 单句长度    —— 逗号分句后任一句超阈值
  3. 创作说明泄漏 —— detailed_description 的导演指令被当台词念出来
  4. 复读        —— 同一句在音轨里出现多次
  5. 台词缺失    —— 提示词里 <d> 写的句子在音轨中找不到
  6. 提示词外内容 —— 念出了不在任何 <d> 标签里的话

用法：
  python r2t2_verify_dialogue.py --dir F:/h3tmp/r2t2_ep04            # 默认阈值
  python r2t2_verify_dialogue.py --seg-total 24 --seg-sentence 12    # 收紧
  python r2t2_verify_dialogue.py --check-only                       # 只跑门禁不出报告
退出码：0 = 通过，1 = 有门禁项未过，2 = 输入文件缺失
"""
import argparse
import json
import re
import sys
from pathlib import Path

# ---- 实测阈值 ----
SEG_TOTAL_MAX = 30       # 整段台词总字数上限（15 秒）
SENTENCE_MAX = 16        # 单个分句字数上限

# ---- 导演指令泄漏特征词 ----
# H3 会把 detailed_description 里的创作说明当台词念出来。
# 这些词只该出现在给模型的指令里，绝不该出现在 <d> 台词标签里。
LEAK_PATTERNS = [
    (r"而不是被台词带", "创作说明原文串入"),
    (r"情绪转折", "导演指令术语"),
    (r"渲染风格", "导演指令术语"),
    (r"日漫|动漫风格|画风", "画风指令术语"),
    (r"锁定(画面|构图|角色)", "约束指令术语"),
    (r"不允许|不要出现|避免出现", "否定约束术语"),
    (r"镜头(语言|运动)|景别|运镜", "摄影指令术语"),
]
LEAK_RE = [(re.compile(p), d) for p, d in LEAK_PATTERNS]

PUNCT = "，。、——？！…·「」"


def norm(x: str) -> str:
    for ch in PUNCT:
        x = x.replace(ch, "")
    return x.replace(" ", "")


def split_sentences(text: str) -> list[str]:
    """按中文分句符切开，标点本身不计入字数。"""
    parts = re.split(r"[，。、——？！…]+", text)
    return [p for p in (norm(p) for p in parts) if p]


def load(work: Path) -> tuple[list, list]:
    tr_path, exp_path = work / "transcript.json", work / "expected_dialogue.json"
    for p in (tr_path, exp_path):
        if not p.exists():
            print(f"[缺文件] {p}")
            sys.exit(2)
    tr = json.loads(tr_path.read_text(encoding="utf-8"))
    exp = json.loads(exp_path.read_text(encoding="utf-8"))
    return tr.get("segments", []), exp


def gate_static(exp: list, seg_total_max: int, sentence_max: int) -> list[str]:
    """门禁 1/2：纯静态检查，不用等 ASR 结果，写完提示词就能跑。"""
    bad = []
    # expected_dialogue.json 的每条记录是一次 <d> 台词；按 seg 聚合总字数
    by_seg: dict[str, list] = {}
    for e in exp:
        by_seg.setdefault(e["seg"], []).append(e)
    for seg, items in sorted(by_seg.items()):
        joined = "".join(i["text"] for i in items)
        total = len(norm(joined))
        if total > seg_total_max:
            bad.append(f"[台词密度] {seg} 整段 {total} 字 > {seg_total_max} 字"
                       f"——{15}s 内 H3 塞不下会拖长/复读（实测 34 字必翻车）")
        for i in items:
            for s in split_sentences(i["text"]):
                if len(s) > sentence_max:
                    bad.append(f"[单句超长] {seg}「{s}」{len(s)} 字 > {sentence_max} 字"
                               f"——易触发同音错字")
    return bad


def gate_static_from_prompt(prompt_file: Path, seg_total_max: int,
                            sentence_max: int) -> list[str]:
    """直接读提示词 txt 跑静态门禁：除了字数，还要查导演指令泄漏。"""
    if not prompt_file.exists():
        print(f"[缺文件] {prompt_file}")
        sys.exit(2)
    txt = prompt_file.read_text(encoding="utf-8")
    bad = []
    # 提取每段的台词标签
    for m in re.finditer(r"<d>\[Chinese\](.*?)</d>", txt, re.S):
        body = m.group(1).strip()
        if not body:
            continue
        n = len(norm(body))
        if n > sentence_max:
            bad.append(f"[单句超长] <d>{body}</d> {n} 字 > {sentence_max} 字")
    # 导演指令泄漏：台词标签内不得出现这些术语
    for m in re.finditer(r"<d>\[Chinese\](.*?)</d>", txt, re.S):
        for rx, desc in LEAK_RE:
            if rx.search(m.group(1)):
                bad.append(f"[指令泄漏] 台词标签里出现{desc}：「{rx.search(m.group(1)).group(0)}」"
                           f"——H3 会把它当台词念出来")
    return bad


def gate_audio(segs: list, exp: list) -> list[str]:
    """门禁 3-6：需要 ASR 结果。"""
    bad = []
    all_asr = " ".join(s.get("text", "") for s in segs)

    for rx, desc in LEAK_RE:
        hit = rx.search(all_asr)
        if hit:
            bad.append(f"[指令泄漏] 音轨念出{desc}：「{hit.group(0)}」")

    seen: dict[str, int] = {}
    for s in segs:
        t = norm(s.get("text", ""))
        if len(t) >= 6:
            seen[t] = seen.get(t, 0) + 1
    for t, c in seen.items():
        if c > 1:
            bad.append(f"[复读] 「{t}」连续 {c} 次——时长不够时的填时长行为")

    asr_norm = norm(all_asr)
    for e in exp:
        parts = split_sentences(e["text"])
        miss = [p for p in parts if len(p) >= 4 and p not in asr_norm]
        if miss:
            bad.append(f"[台词缺失] {e['seg']} 「{'/'.join(miss)}」音轨中找不到")

    exp_all = norm(" ".join(e["text"] for e in exp))
    for s in segs:
        t = norm(s.get("text", ""))
        if len(t) >= 4 and t not in exp_all:
            bad.append(f"[提示词外] {s['start_sample']/16000:.2f}s 念出「{t}」"
                       f"——不在任何 <d> 标签里")
    return bad


def report(segs: list, exp: list) -> None:
    print("=" * 70)
    print("R2T2 反推台词（来自终版成片音轨）")
    print("=" * 70)
    for s in segs:
        t = s.get("text", "").strip()
        if t:
            print(f"  {s['start_sample']/16000:6.2f}s  {t}")
    print()
    print("=" * 70)
    print("提示词写的台词")
    print("=" * 70)
    for e in exp:
        if e["text"] != "...":
            print(f"  {e['seg']}  {e['text']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="F:/h3tmp/r2t2_ep04",
                    help="含 transcript.json / expected_dialogue.json 的目录")
    ap.add_argument("--seg-total", type=int, default=SEG_TOTAL_MAX,
                    help=f"整段台词总字数上限（默认 {SEG_TOTAL_MAX}）")
    ap.add_argument("--seg-sentence", type=int, default=SENTENCE_MAX,
                    help=f"单句字数上限（默认 {SENTENCE_MAX}）")
    ap.add_argument("--prompt", default="",
                    help="提示词 txt 路径；给了就额外跑静态门禁（含指令泄漏）")
    ap.add_argument("--check-only", action="store_true",
                    help="只输出门禁结果，不打印逐句对照报告")
    args = ap.parse_args()

    work = Path(args.dir)
    all_bad: list[str] = []

    # 静态门禁：即使没有 ASR 结果也能跑
    if args.prompt:
        all_bad += gate_static_from_prompt(Path(args.prompt), args.seg_total,
                                           args.seg_sentence)
        print(f"[静态门禁] 已检查 {args.prompt}")
    else:
        segs, exp = load(work)
        all_bad += gate_static(exp, args.seg_total, args.seg_sentence)
        print(f"[静态门禁] 阈值 整段≤{args.seg_total}字 / 单句≤{args.seg_sentence}字")

    if not args.check_only:
        segs, exp = load(work)
        report(segs, exp)
        all_bad += gate_audio(segs, exp)

    print()
    print("=" * 70)
    print(f"门禁结果：{len(all_bad)} 项未过")
    print("=" * 70)
    for i, b in enumerate(all_bad, 1):
        print(f"  {i}. {b}")
    if not all_bad:
        print("  ✓ 全部通过")
    sys.exit(1 if all_bad else 0)


if __name__ == "__main__":
    main()
