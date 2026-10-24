"""把金鱼工作流里的 EasyUse SetNode/GetNode 重定向层解析成直连。

背景：SetNode / GetNode 是 EasyUse 提供的「给节点起别名 + 跨区域连线」辅助层。
SetNode 本质是「我不做任何计算，只把某个输入转发到某个输出」，
GetNode 本质是「我不做任何计算，只把另一个 SetNode 的值引进来」。

ComfyUI 前端会把这些节点画在界面上，但真正执行时数据流是穿透的——
所以本地只要没有 EasyUse 插件，就会报 missing_node_type。

本脚本的做法：
  1. 读出每个 SetNode 的 widgets_values，形如["别名", ...转发关系...]
     实测金鱼里它是 "input_name, value_name, ..." 形式，直接从节点 inputs 里已回填的
     连线关系取「输入端口 → 输出端口」的对应。
  2. 建立 GetNode(别名) -> SetNode(同名) 的映射，把 GetNode 所在位置的连线
     改接到 SetNode 的真实来源。
  3. 删除全部 SetNode / GetNode 节点。

如果某些 SetNode 的转发关系无法从 widgets 推断（例如它是「定义一个常量」），
就把它降级为一个 Text / PrimitiveFloat 等具体节点——因为金鱼里这些节点
实际只是把 CLIP / VAE / 模型 / 提示词 起个名字再引到推理节点。
"""
import json
from pathlib import Path

SRC = Path("F:/h3tmp/jinyu_local_ready.json")
OUT = Path("F:/h3tmp/jinyu_resolved.json")


def main() -> None:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    nodes = d["nodes"]
    by_id = {n["id"]: n for n in nodes}

    # link 结构: [id, origin_id, origin_slot, target_id, target_slot, type]
    links = d["links"]
    by_link_id = {l[0]: l for l in links}

    # ComfyUI 前端节点用 inputs[].link 指向 link_id，比遍历 links 更可靠
    incoming: dict[int, list] = {}
    for n in nodes:
        for slot, sp in enumerate(n.get("inputs") or []):
            lid = sp.get("link")
            if lid is None:
                continue
            l = by_link_id.get(lid)
            if l:
                incoming.setdefault(n["id"], []).append(l)   # 按 target 索引

    print("=== SetNode / GetNode 现状 ===")
    outgoing: dict[int, list] = {}
    for l in links:
        outgoing.setdefault(l[1], []).append(l)
    for n in nodes:
        if n["type"] in ("SetNode", "GetNode"):
            outs = outgoing.get(n["id"], [])
            ins = incoming.get(n["id"], [])
            wv = n.get("widgets_values")
            print(f"  #{n['id']} {n['type']:8s} widgets={wv}")
            print(f"      in<- {[(l[1], l[2]) for l in ins]}")
            print(f"      out-> {[(l[3], l[4]) for l in outs]}")

    # ---- 建 GetNode -> SetNode 的别名映射 ----
    # 关键坑：别名不在 widgets_values 里，而在 properties.previousName。
    # SetNode#5 的 widgets_values=["图像1"]，但真正被 GetNode 引用的是
    # properties.previousName，两者内容一致；用哪个都行，但不能只看 widgets。
    setter_by_alias: dict[str, int] = {}
    for n in nodes:
        if n["type"] == "SetNode":
            props = n.get("properties") or {}
            wv = n.get("widgets_values") or []
            for cand in (props.get("previousName"), wv[0] if wv else None):
                if isinstance(cand, str) and cand:
                    setter_by_alias[cand] = n["id"]
    print(f"\nSetNode 别名表({len(setter_by_alias)}): {setter_by_alias}")

    getter_ref: dict[int, str] = {}
    for n in nodes:
        if n["type"] == "GetNode":
            props = n.get("properties") or {}
            wv = n.get("widgets_values") or []
            for cand in (wv[0] if wv else None, props.get("previousName")):
                if isinstance(cand, str) and cand:
                    getter_ref[n["id"]] = cand
                    break
    print(f"GetNode 引用({len(getter_ref)}): {getter_ref}")

    # 自检：随机抽一条链路验证映射可用
    for probe in list(getter_ref)[:3]:
        alias = getter_ref[probe]
        sid = setter_by_alias.get(alias)
        ups = incoming.get(sid, []) if sid else []
        print(f"  自检 GetNode#{probe} 别名「{alias}」-> SetNode#{sid} "
              f"上游={[l[1] for l in ups]}")

    # ---- 解析：某条 link 的 origin 若是 GetNode/SetNode，一路回溯到真实来源 ----
    # 上一版这里有 bug：递归走到真实节点时 return None，导致全部 unresolved。
    def real_source(link: list, depth: int = 0) -> tuple[int, int] | None:
        """link 是一条从某节点出发的连线；返回它真正的 (origin_id, origin_slot)。

        沿着 GetNode -> SetNode(同名) -> SetNode 的输入 -> ... 一直往上，
        直到 origin 是普通节点为止。
        """
        if depth > 16:
            return None
        oid = link[1]
        n = by_id.get(oid)
        if n is None:
            return None
        t = n["type"]
        if t == "GetNode":
            alias = getter_ref.get(oid)
            sid = setter_by_alias.get(alias) if alias else None
            if sid is None:
                if depth == 0:
                    print(f"    [调试] GetNode#{oid} 别名「{alias}」"
                          f"在 SetNode 别名表中找不到"
                          f"（表里共 {len(setter_by_alias)} 项）")
                return None
            ups = incoming.get(sid, [])
            if not ups:
                if depth == 0:
                    print(f"    [调试] SetNode#{sid}（别名「{alias}」）没有上游连线")
                return None
            return real_source(ups[0], depth + 1)
        if t == "SetNode":
            ups = incoming.get(oid, [])
            if not ups:
                if depth == 0:
                    print(f"    [调试] SetNode#{oid} 没有上游连线")
                return None
            return real_source(ups[0], depth + 1)
        # 到达真实节点，返回它和它的输出槽
        return (oid, link[2])

    relay = set(getter_ref) | set(setter_by_alias.values())
    new_links = []
    patched = 0
    unresolved: list[int] = []
    for l in links:
        lid, oid, oslot, tid, tslot, ltype = l
        if oid in relay:
            src = real_source(l)
            if src:
                new_links.append([lid, src[0], src[1], tid, tslot, ltype])
                patched += 1
                continue
            unresolved.append(oid)
        new_links.append(l)
    if unresolved:
        print(f"未能解析的 origin 节点：{sorted(set(unresolved))}")

    drop = set(getter_ref) | set(setter_by_alias.values())
    # relay 节点的出边已全部改接，剩下的入边都是死线，一并清掉
    new_links = [l for l in new_links if l[3] not in drop]
    still_used = {l[1] for l in new_links} | {l[3] for l in new_links}
    drop = {i for i in drop if i not in still_used}
    print(f"\n改接连线 {patched} 条；可删除节点 {len(drop)} 个")

    d["links"] = new_links
    d["nodes"] = [n for n in nodes if n["id"] not in drop]
    # 清掉幸存节点 inputs 里指向已删节点的悬空 link
    alive_links = {l[0] for l in new_links}
    dangling = 0
    for n in d["nodes"]:
        for sp in n.get("inputs") or []:
            if sp.get("link") is not None and sp["link"] not in alive_links:
                sp["link"] = None
                dangling += 1
    print(f"清理悬空输入端口 {dangling} 个")
    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已输出 {OUT}：{len(d['nodes'])} 节点 / {len(d['links'])} 连线")
    left = [n for n in d["nodes"] if n["type"] in ("SetNode", "GetNode")]
    print(f"剩余 SetNode/GetNode：{[(n['id'], n['type']) for n in left]}")


if __name__ == "__main__":
    main()
