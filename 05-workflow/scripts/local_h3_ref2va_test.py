"""本地 ComfyUI H3 Ref2VA 验证提交器。

用途：把红绳项目的真实 H3 六段提示词 + 老韩音色参考，送到本地 Work-Fisher 版
ComfyUI（127.0.0.1:8188）跑通 Ref2VA，验证「本地能力等价于 RunningHub 金鱼工作流」。

踩坑记录（按尝试顺序）：
1. ref_audios 普通列表 [['20',0]] → 静默失效，报 available audio count is 0。
2. ref_audios 传 dict {'ref_audio_1': [...]} → 序号从 1 开始，被 sorted_autogrow_items 忽略。
3. ref_audios.ref_audio_0 传 [['20',0]] → Bad linked input, must be a length-2 list（多包一层）。
4. ref_audios.ref_audio_0 传 ['20',0] → 通过媒体标签校验 ✅
   （结论：API 格式必须用扁平键名，且值是长度 2 的列表，不嵌套。）
5. 通过校验后报 T2VA cannot include reference media; use Auto or Hybrid
   → 必须显式把 task_type 改成 Ref2VA / Hybrid。节点默认值是 auto，但工作流
   文件里若残留 T2VA 就会触发该检查，所以本脚本强制覆写。
"""
from __future__ import annotations

import json
import time
import urllib.request
import uuid
from pathlib import Path

BASE = "http://127.0.0.1:8188"
ROOT = Path(__file__).resolve().parent.parent          # 05-workflow
PROBE = ROOT / "ep04" / "临时" / "h3_t2va_probe_api.json"
PROMPT_FILE = ROOT / "ep04" / "红绳片段09c_陆定天的名字" / "动作流_H3纯提示词.txt"
LAOHAN_WAV = ROOT.parent / "人物参考音色" / "老韩.wav"
COMFY = Path(r"F:\Work-Fisher纯净包2026.8.7\ComfyUI")


def api(path: str, payload: dict | None = None) -> dict:
    url = BASE + path
    if payload is None:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read())
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def build(prompt: str, audio_name: str, width=768, height=448, length=121) -> dict:
    d = json.loads(PROBE.read_text(encoding="utf-8"))
    cond = d["6"]["inputs"]
    cond["prompt"] = prompt
    cond["width"] = width
    cond["height"] = height
    cond["length"] = length
    # 关键 1：接入参考媒体后必须切到 Ref2VA，否则报
    #      "T2VA cannot include reference media; use Auto or Hybrid"
    cond["task_type"] = "Ref2VA"
    # 关键 2：ref_audios 走 AUTOGROW 扁平键名，值是长度 2 列表、不嵌套
    cond["ref_audios.ref_audio_0"] = ["20", 0]
    # 关键 3：audio_mode=reference_only 时节点强制要求 drive_audio，
    #      所以参考音频要同时接到 drive_audio，并打开 add_source_as_reference
    #      —— 该开关的官方说明就是「Presents drive_audio to Qwen/DiT as an
    #      official <Audio N> reference」，正对本项目的 <Audio 1> 音色锁定。
    cond["drive_audio"] = ["20", 0]
    cond["audio_mode"] = "reference_only"
    cond["add_source_as_reference"] = True
    cond["audio_denoise_strength"] = 1.0
    cond["strict_prompt_tags"] = True
    cond["prompt_primary_audio_ordinal"] = 1
    d["20"]["inputs"]["audio"] = audio_name
    return d


def main() -> None:
    prompt = PROMPT_FILE.read_text(encoding="utf-8").strip()
    print(f"提示词 {len(prompt)} 字")

    names = [v for v in api("/object_info/LoadAudio")["LoadAudio"]["input"]["required"]["audio"][0]
             if isinstance(v, str)]
    # ComfyUI 的 LoadAudio 只认 input/ 目录下的文件名，源文件在别处时先复制过去
    lao = LAOHAN_WAV.name
    if lao not in names:
        dst = COMFY / "input" / lao
        if not dst.exists():
            dst.write_bytes(LAOHAN_WAV.read_bytes())
            print(f"已复制参考音频 -> {dst}")
        names = [v for v in api("/object_info/LoadAudio")["LoadAudio"]["input"]["required"]["audio"][0]
                 if isinstance(v, str)]
        if lao not in names:
            print("提示：input 目录仍未识别，wav 候选：",
                  [n for n in names if n.endswith(".wav")][:8])
    print(f"<Audio 1> -> {lao}")

    wf = build(prompt, lao)
    pid = api("/prompt", {"prompt": wf, "client_id": str(uuid.uuid4())})["prompt_id"]
    print("prompt_id =", pid)

    t0 = time.time()
    while True:
        h = api(f"/history/{pid}")
        if pid in h:
            st = h[pid]["status"]
            print(f"耗时 {time.time()-t0:.0f}s 状态 {st.get('status_str')}")
            if st.get("status_str") != "success":
                for m in st.get("messages", []):
                    if isinstance(m, list) and len(m) > 1 and isinstance(m[1], dict):
                        e = m[1]
                        if "exception_message" in e:
                            print(f"错误节点 {e.get('node_id')} [{e.get('node_type')}]")
                            print("  ", e["exception_message"].strip())
                            if e.get("current_inputs", {}).get("ref_audios.ref_audio_0"):
                                print("   ref_audios 已绑定波形 ✓")
                    else:
                        print("消息:", m)
                return
            for out in h[pid]["outputs"].values():
                for img in out.get("gifs", []) + out.get("videos", []) + out.get("images", []):
                    print("产出:", img)
            return
        q = api("/queue")
        run = [e[1] for e in q.get("queue_running", []) if e[1] == pid]
        wait = q.get("queue_pending", [])
        print(f"耗时 {time.time()-t0:.0f}s  队列 pending={len(wait)} running={'Y' if run else 'N'}")
        time.sleep(15)


if __name__ == "__main__":
    main()
