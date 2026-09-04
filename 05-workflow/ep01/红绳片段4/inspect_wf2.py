# -*- coding: utf-8 -*-
"""从输出节点 VHS_VideoCombine(149) 向上游 BFS，打印管线3完整子图的节点详情"""
import json, os

WF_PATH = r"F:\Work-Fisher纯净包2026.8.7\ComfyUI\user\default\workflows\【Work-Fisher】Minimax-H3 整合流程.json"

with open(WF_PATH, encoding="utf-8") as f:
    wf = json.load(f)

nodes = wf["nodes"]
links = wf["links"]
node_map = {n["id"]: n for n in nodes}
link_map = {}
for lnk in links:
    link_map[lnk[0]] = {"from_node": lnk[1], "from_slot": lnk[2], "to_node": lnk[3], "to_slot": lnk[4], "type": lnk[5]}

# 从 149 上游 BFS（用后进先出，先打印靠近输出端的链）
START = 149
queue = [START]
visited = set()
order = []
while queue:
    nid = queue.pop()
    if nid in visited:
        continue
    visited.add(nid)
    order.append(nid)
    n = node_map.get(nid)
    if n is None:
        continue
    for inp in n.get("inputs", []):
        lid = inp.get("link")
        if lid is not None and lid in link_map:
            queue.append(link_map[lid]["from_node"])

# 按 BFS 发现顺序打印（149 最先，最后到模型加载）
for nid in reversed(order):
    n = node_map.get(nid)
    print(f"\n=== NODE {nid}: {n.get('type')} ===")
    print("widgets_values:", json.dumps(n.get("widgets_values"), ensure_ascii=False)[:600])
    for inp in n.get("inputs", []):
        lid = inp.get("link")
        if lid is not None and lid in link_map:
            src = link_map[lid]["from_node"]
            src_node = node_map[src]
            print(f"  input '{inp['name']}' <- [{src}] {src_node.get('type')} slot{link_map[lid]['from_slot']}")
        else:
            print(f"  input '{inp['name']}' (widget, no link)")
    for out in n.get("outputs", []):
        if out.get("links"):
            for ol in out["links"]:
                if ol in link_map:
                    tgt = link_map[ol]["to_node"]
                    tgt_node = node_map.get(tgt)
                    print(f"  output '{out['name']}' -> [{tgt}] {tgt_node.get('type') if tgt_node else '?'} input '{link_map[ol]['to_slot'] if False else ''}'")
