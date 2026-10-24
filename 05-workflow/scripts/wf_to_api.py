# -*- coding: utf-8 -*-
"""把 ComfyUI 前端工作流 JSON 转成 API (prompt) 格式，并可直连本地 8188 提交。

用法：
    python wf_to_api.py <工作流.json> [-o out.json]      # 只转换
    python wf_to_api.py <工作流.json> --submit           # 转换后提交到本地 ComfyUI
    python wf_to_api.py <工作流.json> --submit --wait     # 提交并轮询到完成
"""
import argparse
import json
import time
import urllib.request
import urllib.error
from pathlib import Path


def to_api(wf: dict) -> dict:
    """前端格式 -> API 格式。

    前端节点 inputs 里只有 widget（控件）值；连线关系在 wf['links'] 里，
    link 形如 [link_id, origin_node, origin_slot, target_node, target_slot, type]。
    API 格式要把连线写成 inputs[input_name] = [origin_node_id, origin_slot]。
    """
    nodes = {str(n["id"]): n for n in wf["nodes"]}
    api: dict[str, dict] = {}

    for nid, n in nodes.items():
        inputs: dict = {}
        for slot in (n.get("inputs") or []):
            if isinstance(slot, dict) and slot.get("name"):
                inputs[slot["name"]] = slot.get("widget_values")
        wv = n.get("widget_values")
        if isinstance(wv, list) and not inputs:
            # 控件值按顺序对应 required 输入，逐个落到 widget_* 或按名字
            pass
        if isinstance(wv, dict):
            inputs.update(wv)
        api[nid] = {"class_type": n["type"], "inputs": inputs}

    # 处理连线
    for link in wf.get("links", []):
        if link and isinstance(link, (list, tuple)) and len(link) >= 6:
            _, origin, o_slot, target, t_slot, _ty = link[:6]
            target_name = _input_name(nodes[str(target)], t_slot)
            if target_name is None:
                continue
            api[str(target)]["inputs"][target_name] = [str(origin), o_slot]

    return api


def _input_name(node: dict, slot: int):
    """把连线插槽序号映射回输入名。"""
    ins = node.get("inputs") or []
    if slot < len(ins) and isinstance(ins[slot], dict):
        return ins[slot].get("name")
    return None


def _fill_widgets(api: dict, wf: dict, object_info: dict | None = None) -> list[str]:
    """把前端 widget_values 按 object_info 的 required 顺序回填到 API inputs。

    前端把控件值存在 node['widgets_values']，输入名要从 object_info 拿。
    本函数尽力而为：按 required 顺序依次对应，无法确定时报错而非静默写错。
    """
    warn = []
    for nid, n in {str(x["id"]): x for x in wf["nodes"]}.items():
        wv = n.get("widgets_values")
        if not isinstance(wv, list):
            continue
        if not object_info:
            warn.append(f"节点 {nid}({n['type']}) 有 {len(wv)} 个控件值但缺少 object_info，未回填")
            continue
        req = object_info.get(n["type"], {}).get("input", {}).get("required", {})
        names = list(req.keys())
        cur = api[nid]["inputs"]
        # 前端 widgets_values 只包含「有控件的输入」的值，且连线占用的输入不产生控件。
        # 判定：inputs 里已有的连线项（值形如 [node_id, slot]）要跳过，不消费控件值。
        linked = {k for k, v in cur.items()
                  if isinstance(v, (list, tuple)) and len(v) == 2
                  and isinstance(v[0], (str, int)) and isinstance(v[1], int)}
        wi = 0
        for nm in names:
            if nm in linked:
                continue          # 被连线占用，无控件值
            if wi < len(wv):
                cur[nm] = wv[wi]
                wi += 1
        if wi < len(wv):
            warn.append(f"节点 {nid}({n['type']}) 有多余控件值未回填：{wv[wi:]}")
    return warn


def post(path: str, payload: dict, host="127.0.0.1:8188"):
    req = urllib.request.Request(
        f"http://{host}{path}", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=300).read())
    except urllib.error.HTTPError as e:
        print("HTTP", e.code)
        print(e.read().decode()[:3000])
        raise SystemExit(1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--wait", action="store_true")
    args = ap.parse_args()

    wf = json.loads(Path(args.workflow).read_text(encoding="utf-8"))
    oi = None
    try:
        oi = json.loads(urllib.request.urlopen(
            "http://127.0.0.1:8188/object_info", timeout=90).read())
    except Exception:
        pass

    api = to_api(wf)
    for w in _fill_widgets(api, wf, oi):
        print("⚠", w)

    out = Path(args.out) if args.out else Path(args.workflow).with_name(
        Path(args.workflow).stem + "_api.json")
    out.write_text(json.dumps(api, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已转换 {len(api)} 个节点 -> {out}")

    if args.submit:
        cid = post("/prompt", {"prompt": api, "client_id": "wfconv"})["prompt_id"]
        print("prompt_id =", cid)
        if args.wait:
            t0 = time.time()
            while True:
                time.sleep(5)
                h = json.loads(urllib.request.urlopen(
                    f"http://127.0.0.1:8188/history/{cid}", timeout=60).read())
                if cid in h:
                    o = h[cid]
                    st = o.get("status", {})
                    print(f"耗时 {time.time() - t0:.0f}s  状态 {st.get('status_str')}")
                    for m in st.get("messages", []):
                        if m[0] == "execution_error":
                            print("错误:", json.dumps(m[1], ensure_ascii=False)[:2000])
                    for k, v in (o.get("outputs") or {}).items():
                        for key in ("gifs", "images", "audio"):
                            for it in v.get(key, []):
                                print(f"  节点{k} 产出 {key}: "
                                      f"{it.get('filename') or it.get('name')}")
                    break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
