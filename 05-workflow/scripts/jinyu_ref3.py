"""金鱼工作流：参考图收敛到 3 张（审讯场景只需 2 人物 + 1 场景）。

原则：**除参考图槽位外，不改工作流任何一个节点**。
金鱼原图有 9 个 ref_image 槽（图像1..图像9），本次只保留前 3 个：
    图像1 -> 陆沉_人设.png          （人物）
    图像2 -> 审讯员老韩_人设_单人.png （人物）
    图像3 -> 场景_ND审问室_日漫v3.png （场景）
其余 6 个槽连同其 LoadImage 节点一并断开/删除，
这样提示词里只需声明 <Subject 1> <Subject 2> <Subject 3> 三个参考。

不动的部分：SetNode/GetNode 转发层、SelfLiftH3Sampler、
所有 LoRA / 模型加载 / 采样参数 / Note 与 Reroute，全部原样保留。
"""
from __future__ import annotations

import json
from pathlib import Path

SRC = Path("F:/ComfyUI_V6.0/YZ金鱼-MiniMax H3 终极篇-文武双全.json")
OUT = Path("F:/h3tmp/jinyu_ref3.json")

KEEP_REF_SLOTS = 3          # 只保留 ref_image_0/1/2
DROP_LOADIMAGE = (235, 234, 233, 236, 237, 238)   # 图像7/8/9/6/5/4 的 LoadImage


def main() -> None:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    nodes = d["nodes"]
    links = d["links"]
    by_id = {n["id"]: n for n in nodes}

    h3 = next(n for n in nodes
              if n["type"] == "MiniMaxH3ReferenceToVideo")
    link_by_id = {l[0]: l for l in links}

    # ---- 1. 断开 ref_image_3..8 的连线 ----
    drop_links = set()
    drop_link_objs = []
    for sp in h3["inputs"]:
        name = sp.get("name", "")
        if not name.startswith("ref_images.ref_image_"):
            continue
        idx = int(name.rsplit("_", 1)[1])
        if idx >= KEEP_REF_SLOTS:
            lid = sp.get("link")
            if lid is not None:
                drop_links.add(lid)
                drop_link_objs.append(link_by_id[lid])
                sp["link"] = None
            print(f"  断开 {name}")

    links = [l for l in links if l[0] not in drop_links]

    # ---- 2. 删除对应的 LoadImage 节点 ----
    # 注意：这些 LoadImage 是经 SetNode/GetNode 转发接进 H3 的，
    # link 的 origin 是 GetNode 而非 LoadImage，所以要按 id 显式删。
    drop_nodes = {nid for nid in DROP_LOADIMAGE if nid in by_id}
    for l in drop_link_objs:
        src = l[1]
        if src in by_id and by_id[src]["type"] == "LoadImage":
            drop_nodes.add(src)
    nodes = [n for n in nodes if n["id"] not in drop_nodes]
    print(f"删除 LoadImage 节点 {sorted(drop_nodes)}")

    # ---- 3. 清理幸存节点的悬空端口 ----
    alive = {l[0] for l in links}
    fixed = 0
    for n in nodes:
        for sp in n.get("inputs") or []:
            if sp.get("link") is not None and sp["link"] not in alive:
                sp["link"] = None
                fixed += 1
        for op in n.get("outputs") or []:
            if op.get("links"):
                op["links"] = [x for x in op["links"] if x in alive]
    print(f"清理悬空端口 {fixed} 个")

    d["nodes"] = nodes
    d["links"] = links
    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已输出 {OUT}：{len(nodes)} 节点 / {len(links)} 连线")

    # ---- 4. 核对保留的 3 个参考图槽 ----
    by_id2 = {n["id"]: n for n in nodes}
    lk = {l[0]: l for l in links}
    h3 = next(n for n in nodes
              if n["type"] == "MiniMaxH3ReferenceToVideo")
    print("\n保留的参考图槽：")
    for sp in h3["inputs"]:
        name = sp.get("name", "")
        if name.startswith("ref_images.ref_image_"):
            lid = sp.get("link")
            if lid:
                src = lk[lid][1]
                print(f"  {name} <- LoadImage#{src} "
                      f"{by_id2[src].get('widgets_values')}")
            else:
                print(f"  {name} <- 未连接")
    types = {n["type"] for n in nodes}
    print(f"\nSetNode/GetNode 保留: "
          f"{'SetNode' in types}/{'GetNode' in types}  "
          f"SelfLiftH3Sampler: {'SelfLiftH3Sampler' in types}")


if __name__ == "__main__":
    main()
