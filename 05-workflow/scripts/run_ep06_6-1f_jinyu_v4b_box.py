# -*- coding: utf-8 -*-
"""EP06 6-1f「泼酒成刃」v4b｜云端金鱼 H3 Ref2VA（box 版，个人 RH 币）。

一次反馈＝一版＝一次提交：taskId 文件存在即拒绝二次提交，只续轮询。
key 取 RUNNINGHUB_API_KEY 前 32 位 hex，不打印、不落盘。
槽位：51=<Picture 1> 帕斯卡人设 / 49=<Picture 2> 车库（去红灯） / 50=<Picture 3> 蓝隼正侧身裁切；48=<Audio 1> 蓝隼音色。
"""
import json, os, re, sys, time
from pathlib import Path
import requests

API = "https://www.runninghub.cn"
APP = "2110357037929558018"
REPO = Path("/workspace/novel-hongsheng")
SEG = REPO / "05-workflow/ep06/6-1f_泼酒成刃"
PROMPT = SEG / "金鱼_H3纯提示词_EP06_6-1f_v4b.txt"
UP = Path("/workspace/ep05-preview/jinyu/EP06_6-1f_v1_upload")
OUTDIR = Path("/workspace/ep05-preview/jinyu/EP06_6-1f_v4b_review")
TASKID = SEG / "_jinyu_v4b.taskid"
RECEIPT = SEG / "RH任务回执_金鱼_EP06_6-1f_v4b.json"
IMAGES = [("51", UP / "pascal.png"), ("49", UP / "garage_clean.png"), ("50", UP / "lansun_front_side.png")]
AUDIOS = [("48", UP / "lansun.wav")]

m = re.match(r"^[0-9a-fA-F]{32}", os.environ.get("RUNNINGHUB_API_KEY", ""))
if not m:
    sys.exit("RUNNINGHUB_API_KEY missing/invalid")
KEY = m.group(0)


def post(ep, body, timeout=60):
    r = requests.post(API + ep, json={**body, "apiKey": KEY},
                      headers={"Authorization": f"Bearer {KEY}"}, timeout=(15, timeout))
    return r.json()


def upload(p):
    with open(p, "rb") as f:
        r = requests.post(API + "/task/openapi/upload", data={"apiKey": KEY},
                          files={"file": (p.name, f)}, timeout=180).json()
    if r.get("code") != 0:
        raise RuntimeError(f"upload fail {p.name}: {r.get('msg')}")
    return r["data"]["fileName"]


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    prompt = PROMPT.read_text(encoding="utf-8").strip()
    labels = ["subject_definitions:", "summary:", "retention_analysis:", "detailed_description:",
              "overall_soundscape:", "non_diegetic_music:"]
    pos = [prompt.find(l) for l in labels]
    assert all(i >= 0 for i in pos) and pos == sorted(pos) and prompt.startswith(labels[0])
    nbytes = len(prompt.encode())
    assert nbytes <= 5000, nbytes
    assert set(re.findall(r"<Picture (\d+)>", prompt)) == {"1", "2", "3"}
    assert set(re.findall(r"<Audio (\d+)>", prompt)) == {"1"}
    for w in ("FORBIDDEN", "demonic", "upside", "backwards", "backward"):
        assert w.lower() not in prompt.lower(), w

    acc0 = post("/uc/openapi/accountStatus", {}).get("data") or {}
    print("account before:", {k: acc0.get(k) for k in ("remainCoins", "remainPoint", "remainMoney", "currentTaskCounts")}, flush=True)

    if TASKID.exists():
        task_id = TASKID.read_text().strip()
        print("resume taskId", task_id, flush=True)
        submit = None
    else:
        nodes = [
            {"nodeId": "252", "fieldName": "aspect_ratio", "fieldValue": "16:9 (Widescreen)"},
            {"nodeId": "252", "fieldName": "megapixels", "fieldValue": "1.5"},
            {"nodeId": "259", "fieldName": "value", "fieldValue": "15"},
            {"nodeId": "261", "fieldName": "scheduler", "fieldValue": "simple"},
            {"nodeId": "261", "fieldName": "steps", "fieldValue": "12"},
        ]
        for nid, p in IMAGES:
            nodes.append({"nodeId": nid, "fieldName": "image", "fieldValue": upload(p)})
        for nid, p in AUDIOS:
            nodes.append({"nodeId": nid, "fieldName": "audio", "fieldValue": upload(p)})
        nodes.append({"nodeId": "263", "fieldName": "text", "fieldValue": prompt})
        for i in range(12):
            submit = post("/task/openapi/ai-app/run", {"webappId": APP, "instanceType": "plus", "nodeInfoList": nodes})
            print("submit try", i, submit.get("code"), submit.get("msg"), flush=True)
            if submit.get("code") == 0 and (submit.get("data") or {}).get("taskId"):
                break
            msg = str(submit.get("msg", ""))
            if "QUEUE" in msg.upper() or submit.get("code") in (421, 415, 805):
                time.sleep(30); continue
            sys.exit(f"submit refused: {submit.get('code')} {msg}")
        task_id = str(submit["data"]["taskId"])
        TASKID.write_text(task_id)
        print("taskId", task_id, flush=True)

    t0 = time.time()
    while True:
        try:
            st = post("/task/openapi/status", {"taskId": task_id}).get("data")
        except Exception as e:  # network hiccup: keep polling same taskId
            print("poll error", type(e).__name__, flush=True); st = None
        print(f"[{int(time.time()-t0)}s] {st}", flush=True)
        if st in ("SUCCESS", "FAILED"):
            break
        time.sleep(20)
    out = post("/task/openapi/outputs", {"taskId": task_id})
    (OUTDIR / "outputs.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    acc1 = post("/uc/openapi/accountStatus", {}).get("data") or {}
    print("account after:", {k: acc1.get(k) for k in ("remainCoins", "remainPoint", "remainMoney")}, flush=True)
    data = out.get("data") or []
    url = None
    usage = None
    if isinstance(data, list):
        for o in data:
            u = o.get("fileUrl") or ""
            usage = usage or {k: o.get(k) for k in ("consumeCoins", "consumeMoney", "taskCostTime", "thirdPartyConsumeMoney", "settleMode", "chargedPoint")}
            if u.endswith(".mp4"):
                url = u
    saved = None
    if st == "SUCCESS" and url:
        saved = Path("/workspace/ep05-preview/jinyu/EP06_6-1f_v4b_金鱼草稿.mp4")
        saved.write_bytes(requests.get(url, timeout=600).content)
    def num(x):
        try: return float(x)
        except Exception: return None
    coins_delta = None
    if num(acc0.get("remainCoins")) is not None and num(acc1.get("remainCoins")) is not None:
        coins_delta = num(acc0.get("remainCoins")) - num(acc1.get("remainCoins"))
    rec = {
        "unit": "EP06_6-1f_v4b_jinyu", "workflow": "金鱼云端(box)", "appId": APP, "taskId": task_id,
        "status": st, "billing": "personal_RH_coins", "usage": usage,
        "coins_before": acc0.get("remainCoins"), "coins_after": acc1.get("remainCoins"), "coins_delta": coins_delta,
        "promptBytes": nbytes, "params": "16:9 / 15s / 1.5MP / simple / 12 / plus",
        "prompt_path": str(PROMPT.relative_to(REPO)),
        "refs": {nid: p.name for nid, p in IMAGES}, "audios": {nid: p.name for nid, p in AUDIOS},
        "upload_dir": str(UP), "download_url": url, "output_mp4": str(saved) if saved else None,
        "completed_local": time.strftime("%Y-%m-%d %H:%M %Z"),
    }
    RECEIPT.write_text(json.dumps(rec, ensure_ascii=False, indent=2))
    print(json.dumps(rec, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
