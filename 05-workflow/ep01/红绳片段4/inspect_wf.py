# -*- coding: utf-8 -*-
"""分析 Work-Fisher MiniMax-H3 工作流 JSON：管线3依赖链"""
import json, os, sys

WF_PATH = r"F:\Work-Fisher纯净包2026.8.7\ComfyUI\user\default\workflows\【Work-Fisher】Minimax-H3 整合流程.json"
print("size:", os.path.getsize(WF_PATH))

with open(WF_PATH, encoding="utf-8") as f:
    wf = json.load(f)

print("keys:", list(wf.keys()))
nodes = wf["nodes"]
links = wf["links"]
print("num nodes:", len(nodes), "num links:", len(links))

# 建立 link_id -> (from_node, from_slot, to_node, to_slot, type)
link_map = {}
for lnk in links:
    link_map[lnk[0]] = {"from_node": lnk[1], "from_slot": lnk[2], "to_node": lnk[3], "to_slot": lnk[4], "type": lnk[5]}

# 节点索引
node_map = {n["id"]: n for n in nodes}

target_ids = [153, 154, 155, 156, 151, 150]
for nid in target_ids:
    n = node_map.get(nid)
    if n is None:
        print(f"\n=== NODE {nid} NOT FOUND ===")
        continue
    print(f"\n=== NODE {nid} ===")
    print("type:", n.get("type"))
    print("widgets_values:", json.dumps(n.get("widgets_values"), ensure_ascii=False)[:800])
    print("inputs:", json.dumps(n.get("inputs"), ensure_ascii=False)[:800])
    print("outputs:", json.dumps(n.get("outputs"), ensure_ascii=False)[:300])

# 从 node 153 开始 BFS 上游依赖
print("\n\n===== BFS UPSTREAM DEPENDENCIES OF NODE 153 =====")
queue = [153]
visited = set()
upstream = {}
while queue:
    nid = queue.pop(0)
    if nid in visited:
        continue
    visited.add(nid)
    n = node_map.get(nid)
    if n is None:
        continue
    for inp in n.get("inputs", []):
        lid = inp.get("link")
        if lid is not None and lid in link_map:
            src = link_map[lid]["from_node"]
            upstream.setdefault(nid, []).append((src, inp.get("name")))
            queue.append(src)

for nid in sorted(upstream, key=lambda x: (x not in (153,), x)):
    n = node_map.get(nid)
    print(f"node {nid}: {n.get('type') if n else '?'}")
    for src, iname in upstream[nid]:
        print(f"    <- input '{iname}' from node {src} ({node_map[src].get('type') if src in node_map else '?'})")

# 输出所有节点 id -> type 概览
print("\n\n===== ALL NODES (id: type) =====")
for n in sorted(nodes, key=lambda x: x["id"]):
    print(f"{n['id']}: {n.get('type')}")
