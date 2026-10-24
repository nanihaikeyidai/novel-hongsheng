"""解析金鱼工作流 JSON：节点类型清单、缺失节点、模型依赖。"""
import json
from collections import Counter
from pathlib import Path

SRC = Path(r"F:\ComfyUI_V6.0\YZ金鱼-MiniMax H3 终极篇-文武双全.json")
d = json.loads(SRC.read_text(encoding="utf-8"))
nodes = d["nodes"]

print("=" * 70)
print("节点类型分布（共 %d 个节点）" % len(nodes))
print("=" * 70)
cnt = Counter(n["type"] for n in nodes)
for t, c in sorted(cnt.items(), key=lambda kv: -kv[1]):
    print(f"  {c:2d}x  {t}")

print()
print("=" * 70)
print("按 id 列出（type / title）")
print("=" * 70)
for n in sorted(nodes, key=lambda x: x["id"]):
    title = n.get("title") or ""
    print(f"  #{n['id']:3d}  {n['type']:42s} {title[:40]}")

print()
print("=" * 70)
print("连线")
print("=" * 70)
for l in d["links"]:
    print(f"  {l[0]:3d}: node {l[1]} out{l[2]} -> node {l[3]} in{l[4]}")
