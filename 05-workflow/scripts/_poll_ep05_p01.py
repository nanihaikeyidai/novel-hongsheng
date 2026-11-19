import json, os, time, requests
from pathlib import Path
API_KEY=os.environ.get("RH_API_KEY","")
QUERY="https://www.runninghub.cn/openapi/v2/query"
headers={"Authorization":f"Bearer {API_KEY}","Content-Type":"application/json"}
tasks={"P01a":"2114283413979750401","P01b":"2114283464705671170"}
out=Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep05\营救陆沉\制作文档\rh_task_status.json")
seg_dir=Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep05\营救陆沉\红绳片段01")
results={}
for name, tid in tasks.items():
    for i in range(30):
        try:
            r=requests.post(QUERY,headers=headers,json={"taskId":tid},timeout=60)
            d=r.json()
        except Exception as e:
            print(name, "query_err", e, flush=True)
            time.sleep(25)
            continue
        st=d.get("status") or (d.get("data") or {}).get("status")
        print(name, tid, st, flush=True)
        if st in ("SUCCESS","FAILED","ERROR"):
            results[name]={"taskId":tid,"status":st}
            if st=="SUCCESS":
                items=d.get("results") or (d.get("data") or {}).get("results") or []
                for item in items:
                    url=item.get("url")
                    if not url: continue
                    dest=seg_dir/f"片段01_{name}_云端草稿.mp4"
                    for attempt in range(3):
                        try:
                            vr=requests.get(url,timeout=300)
                            dest.write_bytes(vr.content)
                            results[name]["download"]=str(dest)
                            results[name]["bytes"]=len(vr.content)
                            print("downloaded", dest, len(vr.content), flush=True)
                            break
                        except Exception as e:
                            print("dl_err", e, flush=True)
                            time.sleep(10)
            else:
                results[name]["failedReason"]=str(d.get("failedReason") or d)[:500]
            break
        time.sleep(25)
    else:
        results[name]={"taskId":tid,"status":"STILL_RUNNING_OR_TIMEOUT"}
# retry P02 once
print("retry P02...", flush=True)
import subprocess, sys
p=subprocess.run([sys.executable, r"D:\HermesWorkspace\ai小说\红绳\05-workflow\scripts\run_ep05_rescue_rh_director.py", "--unit", "P02"], capture_output=True, text=True)
print(p.stdout[-800:] if p.stdout else "")
print(p.stderr[-400:] if p.stderr else "")
results["P02_retry_stdout_tail"]= (p.stdout or "")[-500:]
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
print("FINAL", json.dumps(results,ensure_ascii=False,indent=2))
