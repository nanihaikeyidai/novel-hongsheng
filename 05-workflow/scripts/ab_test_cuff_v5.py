"""用本地 ComfyUI 验证 10b 的手铐是否落在手腕上（v5 修复效果，免费快）。

对比策略：同一提示词渲两版——
  A. v5 修复版（Subject 4 主语重排 + 镜头描述改为「两个手腕上的铐具」）
  B. v4 原版（把 Subject 4 开头换回「桌沿的固定环与手铐」，镜头描述换回「桌面铐具」）
两版只差铐具定位这一处，用来确认修复是否真的起作用，而不是运气。
"""
import json
import shutil
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from local_h3_ref2va_test import PROBE, api  # noqa: E402

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep04")
TMP = Path("F:/h3tmp")
TXT = ROOT / "红绳片段10b_到底是什么机构" / "动作流_H3纯提示词.txt"
LAOHAN = Path(r"D:\HermesWorkspace\ai小说\红绳\人物参考音色\老韩.wav")
COMFY = Path(r"F:\Work-Fisher纯净包2026.8.7\ComfyUI")

V5_HEAD = "<Subject 4> 是陆沉手腕上戴着的一副银色手铐"
V4_HEAD = "<Subject 4> 是桌沿的固定环与手铐"
V5_SHOT = "与陆沉两个手腕上的铐具（铐环闭合、锁舌已插入，短链朝桌沿方向拉紧）"
V4_SHOT = "与桌面铐具"


def make(prompt: str) -> dict:
    d = json.loads(PROBE.read_text(encoding="utf-8"))
    c = d["6"]["inputs"]
    c["prompt"] = prompt
    c["width"], c["height"], c["length"] = 768, 448, 121
    c["task_type"] = "Ref2VA"
    c["ref_audios.ref_audio_0"] = ["20", 0]
    c["drive_audio"] = ["20", 0]
    c["audio_mode"] = "reference_only"
    c["add_source_as_reference"] = True
    c["audio_denoise_strength"] = 1.0
    c["strict_prompt_tags"] = True
    c["prompt_primary_audio_ordinal"] = 1
    d["20"]["inputs"]["audio"] = LAOHAN.name
    return d


def to_v4(prompt: str) -> str:
    """把 v5 的两处铐具定位回退成 v4 写法，做 A/B 对照。"""
    out = prompt.replace(V5_HEAD, V4_HEAD, 1).replace(V5_SHOT, V4_SHOT)
    assert V4_HEAD in out and V4_SHOT in out, "回退失败，检查文本"
    return out


def run(wf: dict, tag: str) -> Path:
    pid = api("/prompt", {"prompt": wf, "client_id": str(uuid.uuid4())})["prompt_id"]
    t0 = time.time()
    while True:
        h = api(f"/history/{pid}")
        if pid in h:
            st = h[pid]["status"]
            if st.get("status_str") != "success":
                for m in st.get("messages", []):
                    if isinstance(m, list) and isinstance(m[1], dict) and "exception_message" in m[1]:
                        print(f"[{tag}] 失败: {m[1]['exception_message'].strip()[:200]}")
                return None
            for out in h[pid]["outputs"].values():
                for v in out.get("gifs", []) + out.get("videos", []):
                    src = COMFY / "output" / v["filename"]
                    dst = TMP / f"cmp_{tag}.mp4"
                    shutil.copy(src, dst)
                    print(f"[{tag}] {time.time()-t0:.0f}s -> {dst}")
                    return dst
            return None
        print(f"[{tag}] {time.time()-t0:.0f}s 运行中…", flush=True)
        time.sleep(20)


def frames(video: Path, tag: str) -> None:
    out = TMP / f"cmp_{tag}.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video),
                    "-vf", "select='eq(n\\,20)+eq(n\\,150)+eq(n\\,350)',scale=440:-1,tile=3x1",
                    "-frames:v", "1", str(out)], check=True)
    print(f"[{tag}] 抽帧 -> {out}")


def main() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    dst = COMFY / "input" / LAOHAN.name
    if not dst.exists():
        dst.write_bytes(LAOHAN.read_bytes())

    p5 = TXT.read_text(encoding="utf-8").strip()
    assert V5_HEAD in p5, "落盘 txt 不是 v5 版本，先跑 export_ep04_prompts.py"
    p4 = to_v4(p5)

    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    for tag, prompt in (("v5", p5), ("v4", p4)):
        if which not in ("both", tag):
            continue
        v = run(make(prompt), tag)
        if v:
            frames(v, tag)


if __name__ == "__main__":
    main()
