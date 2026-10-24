# -*- coding: utf-8 -*-
"""EP04 放学抓捕线 4×15s 本地梅林串行跑批。"""
from __future__ import annotations
import subprocess, sys, time
from pathlib import Path

PY = Path(r"F:\Work-Fisher纯净包2026.8.7\python\python.exe")
RUN = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\scripts\run_local_meilin.py")
EP = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep04")
CHAR = EP / "归档素材" / "人物"
SCN = EP / "归档素材" / "场景"
LOG = EP / "capture_batch_run.log"

JOBS = [
    {
        "id": "01",
        "tag": "ep04_s01_after_school",
        "prompt": EP / "红绳片段01" / "动作流_H3纯提示词.txt",
        "out": EP / "红绳片段01" / "视频草稿" / "E04-01_放学出门_未审核草稿.mp4",
        "img1": CHAR / "陆沉_人设.png",
        "img2": SCN / "场景_红杉高中校门_晴天_无人.png",
        "img3": CHAR / "陆沉_人设.png",
    },
    {
        "id": "02",
        "tag": "ep04_s02_badge_run",
        "prompt": EP / "红绳片段02" / "动作流_H3纯提示词.txt",
        "out": EP / "红绳片段02" / "视频草稿" / "E04-02_亮证甩手_未审核草稿.mp4",
        "img1": CHAR / "陆沉_人设.png",
        "img2": CHAR / "ND调查员_赵凯.png",
        "img3": SCN / "场景_红杉高中校门_晴天_无人.png",
    },
    {
        "id": "03",
        "tag": "ep04_s03_van_block",
        "prompt": EP / "红绳片段03" / "动作流_H3纯提示词.txt",
        "out": EP / "红绳片段03" / "视频草稿" / "E04-03_开车封口_未审核草稿.mp4",
        "img1": CHAR / "陆沉_人设.png",
        "img2": CHAR / "ND值班员_小月.png",
        "img3": SCN / "场景_教学楼雨中.png",
    },
    {
        "id": "04",
        "tag": "ep04_s04_cuff_alley_v2",
        "prompt": EP / "红绳片段04" / "动作流_H3纯提示词.txt",
        "out": EP / "红绳片段04" / "视频草稿" / "E04-04_反拷目击_未审核草稿.mp4",
        # 场景锁 = 片段03末帧（巷内封口）；安娜只作远景描述，不占近景参考槽
        "img1": CHAR / "陆沉_人设.png",
        "img2": EP / "红绳片段04" / "参考" / "E04-03_末帧_巷内封口.png",
        "img3": CHAR / "ND调查员_赵凯.png",
    },
]


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def main() -> int:
    LOG.write_text(f"=== EP04 capture batch start {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n", encoding="utf-8")
    # health
    import urllib.request
    try:
        urllib.request.urlopen("http://127.0.0.1:8188/", timeout=5).read(64)
        log("ComfyUI 8188 OK")
    except Exception as e:
        log(f"ComfyUI 不可用: {e}")
        return 1

    fails = []
    t_all = time.time()
    for j in JOBS:
        for p in (j["prompt"], j["img1"], j["img2"], j["img3"], RUN, PY):
            if not Path(p).exists():
                log(f"缺失: {p}")
                fails.append(j["id"])
                break
        else:
            if j["out"].exists():
                log(f"跳过已有成片 {j['id']}: {j['out']}")
                continue
            cmd = [
                str(PY), str(RUN),
                "--prompt", str(j["prompt"]),
                "--img1", str(j["img1"]),
                "--img2", str(j["img2"]),
                "--img3", str(j["img3"]),
                "--seconds", "15",
                "--tag", j["tag"],
                "--out", str(j["out"]),
                "--template", "0.5",
            ]
            log(f"开始 片段{j['id']} → {j['out'].name}")
            t0 = time.time()
            r = subprocess.run(cmd, cwd=str(RUN.parent))
            dt = (time.time() - t0) / 60
            if r.returncode != 0 or not j["out"].exists():
                log(f"失败 片段{j['id']} rc={r.returncode} {dt:.1f}min")
                fails.append(j["id"])
            else:
                log(f"完成 片段{j['id']} {dt:.1f}min size={j['out'].stat().st_size}")
    log(f"全部结束 总耗时{(time.time()-t_all)/60:.1f}min fails={fails}")
    return 0 if not fails else 2


if __name__ == "__main__":
    sys.exit(main())
