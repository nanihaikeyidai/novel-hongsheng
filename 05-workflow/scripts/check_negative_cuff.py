"""确认 26 段提示词里已无手铐类数量否定（含 negative 区）。"""
from pathlib import Path

EP04 = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep04")
BAD_EN = ("multiple pairs of handcuffs", "second pair of handcuffs",
          "multiple handcuffs", "extra handcuffs", "handcuffs")
BAD_CN = ("第二副手铐", "出现第二副", "除此之外没有任何手铐", "多副手铐")

hit = 0
for p in sorted(EP04.glob("红绳片段*/动作流_H3纯提示词.txt")):
    t = p.read_text(encoding="utf-8")
    neg = t[t.find("negativePrompt:"):]
    for b in BAD_CN:
        if b in t:
            print(f"[CN] {p.parent.name}: {b}")
            hit += 1
    for b in BAD_EN:
        if b in neg:
            print(f"[EN-negative] {p.parent.name}: {b}")
            hit += 1
    # 正向约束：只在描述了手铐的段里要求（无铐段如空镜不该出现）
    if ("手铐" in t or "铐" in t) and "唯一存在的那副手铐" not in t:
        print(f"[缺正向约束] {p.parent.name}")
        hit += 1
print(f"\n共 {hit} 处问题" +("" if hit else "（全部干净）"))
