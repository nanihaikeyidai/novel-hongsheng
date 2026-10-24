"""把金鱼工作流按 ComfyUI 前端的规则展开 SetNode/GetNode，产出可直接提交的 API 图。

**这不是修改工作流**，而是复现 ComfyUI 前端在「提交到后端之前」必做的一步。

背景：
  金鱼工作流用了 KJNodes 的 SetNode / GetNode 来隐藏长连线。
  KJNodes 1.5.2 起把这两个节点重写为**纯前端虚拟节点**
  （custom_nodes/ComfyUI-KJNodes/web/js/setgetnodes.js），
  它们不在 NODE_CLASS_MAPPINGS 里注册，后端 object_info 查不到。
  前端在提交前会把 GetNode 展开成「同名 SetNode 的真实来源」的直连，
  所以从界面点「运行」不会有问题；但用 API 脚本直接提交就必然报
  missing_node_type: SetNode。

本脚本严格照搬前端 setgetnodes.js 的配对规则：
  findSetterByName(): 在当前图里找 widgets[0].value === name 的 SetNode
  SetNode.inputs[0]   : 就是该别名的真实来源

用法：
  python expand_setget.py <工作流.json> -o <展开后.json>
输出的是 API 格式（可直接 POST /prompt）。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_api(wf: dict) -> dict:
    """前端格式 + Set/Get 展开 -> API 格式。"""
    nodes = {n["id"]: n for n in wf["nodes"]}
    links = wf["links"]
    by_link = {l[0]: l for l in links}

    # 反查每个节点的入边（从 inputs[].link 反查，比遍历 links 的 target 可靠）
    # ---- Reroute 直通改接（必须最先做：它会改写 links，
    #      而后面的 incoming 索引与 Set/Get 回溯都依赖 links）----
    # Reroute 是「一对多/多对一」连线工具，后端 object_info 查不到，
    # 必须删；但直接删会把数据流断成悬空，表现为节点被 ComfyUI 判为
    # 「无需执行」——20 秒空跑、history.outputs 为空、磁盘无产出。
    # 所以先把经过 Reroute 的连线压成直连，再删 Reroute。
    rr = {n["id"] for n in wf["nodes"] if n["type"] == "Reroute"}
    if rr:
        for _ in range(8):        # 链可能有多级，反复压平直到收敛
            ups_of: dict[int, list] = {}
            for l in links:
                ups_of.setdefault(l[3], []).append(l)
            changed = False
            out = []
            for l in links:
                if l[1] in rr:
                    ups = ups_of.get(l[1]) or []
                    if not ups:
                        continue    # 无上游的 Reroute 是孤立节点，直接丢
                    u = ups[0]
                    out.append([l[0], u[1], u[2], l[3], l[4], l[5]])
                    changed = True
                else:
                    out.append(l)
            links = out
            if not changed:
                break
        print(f"  Reroute 直通改接完成（{len(rr)} 个已压平并删除）")

    incoming: dict[int, list] = {}
    for n in wf["nodes"]:
        for sp in n.get("inputs") or []:
            lid = sp.get("link")
            if lid is not None and lid in by_link:
                incoming.setdefault(n["id"], []).append(by_link[lid])

    # ---- 配对表：别名 -> SetNode id ----
    setter_by_name: dict[str, int] = {}
    for n in wf["nodes"]:
        if n["type"] == "SetNode":
            wv = n.get("widgets_values") or []
            if wv and isinstance(wv[0], str) and wv[0]:
                setter_by_name[wv[0]] = n["id"]

    def real_source(link: list, depth: int = 0):
        """link 是从某节点出发的连线；返回它真正的 (origin_id, origin_slot)。

        沿 GetNode -> SetNode(同名) -> SetNode 的入边 -> ... 一直往上，
        直到 origin 是普通节点为止。
        注意：终点必须返回 (节点, 槽)，返回 None 会让整条链解析失败
        （这是第一版只改接 0 条的原因）。
        """
        if depth > 16:
            return None
        oid = link[1]
        n = nodes.get(oid)
        if n is None:
            return None
        t = n["type"]
        if t == "GetNode":
            wv = n.get("widgets_values") or []
            name = wv[0] if wv else None
            sid = setter_by_name.get(name)
            if sid is None:
                return None
            ups = incoming.get(sid) or []
            if not ups:
                return None
            return real_source(ups[0], depth + 1)
        if t == "SetNode":
            ups = incoming.get(oid) or []
            if not ups:
                return None
            return real_source(ups[0], depth + 1)
        return (oid, link[2])        # 到达真实节点

    relay = {n["id"] for n in wf["nodes"] if n["type"] in ("SetNode", "GetNode")}
    new_links: list[list] = []
    patched = 0
    unresolved: list[int] = []
    for l in links:
        lid, oid, oslot, tid, tslot, ltype = l
        if oid in relay:
            src = real_source(l)
            if src is not None:
                l = [lid, src[0], src[1], tid, tslot, ltype]
                patched += 1
            else:
                unresolved.append(oid)
        new_links.append(l)

    if unresolved:
        print(f"  ⚠ 未解析的 relay origin：{sorted(set(unresolved))}")
    print(f"  Set/Get 展开：改接 {patched} 条连线")

    # 指向 relay 的连线在展开后全是死线
    new_links = [l for l in new_links if l[3] not in relay]
    drop = {i for i in relay
            if i not in {l[1] for l in new_links} | {l[3] for l in new_links}}
    print(f"  删除 relay 节点 {len(drop)} 个（Set+Get 全部移除）")

    # ---- 剔除纯前端装饰节点 ----
    # Note / MarkdownNote 是纯备注，没有任何数据流，删掉不影响执行。
    # Reroute 已在函数开头完成直通改接，这里只负责删掉壳。
    # 「忽略多组孤海」是 RunningHub 的分组标注节点，本身就是 OUTPUT_NODE，
    # 留着会让 ComfyUI 只执行这几个孤立标注、整张主链被判不可达
    # （表现为 20 秒空跑、history.outputs 为空）。
    DECOR = {"Note", "MarkdownNote", "Reroute", "忽略多组孤海"}
    kept = [n for n in wf["nodes"] if n["id"] not in drop
            and n["type"] not in DECOR]
    decor = sorted({n["type"] for n in wf["nodes"] if n["type"] in DECOR})
    if decor:
        print(f"  删除纯前端/标注节点（{decor}）")

    # ---- 前端格式 -> API 格式 ----
    # 注意：不要把 widgets_values 原样塞进 API 图。
    # API 格式只认 class_type + inputs，多余键会让 ComfyUI 的
    # 图验证把整张图判为不可达（表现为只跑孤立标注节点、20 秒空跑）。
    api: dict[str, dict] = {}
    for n in kept:
        inputs: dict = {}
        for sp in n.get("inputs") or []:
            lid = sp.get("link")
            if lid is None:
                continue
            l = next((x for x in new_links if x[0] == lid), None)
            if l is None:
                continue
            name = sp.get("name")
            if name:
                inputs[name] = [str(l[1]), l[2]]
        api[str(n["id"])] = {"class_type": n["type"], "inputs": inputs}
    return api


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()
    wf = json.loads(Path(args.workflow).read_text(encoding="utf-8"))
    print(f"输入 {len(wf['nodes'])} 节点 / {len(wf['links'])} 连线")
    api = build_api(wf)
    Path(args.out).write_text(
        json.dumps(api, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"输出 {args.out}：{len(api)} 节点")


if __name__ == "__main__":
    main()
