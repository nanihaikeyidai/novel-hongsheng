"""EP04 终版四段手铐一致性总验收：09c(v4) + 10a(v5) + 10b(v5) + 10c(v7)。

每段取一帧手腕特写，横排对比，确认铐环位置/形态/链条走向一致。
"""
import shutil
import subprocess
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep04")
TMP = Path("F:/h3tmp")
SEGS = [
    ("09c", "红绳片段09c_陆定天的名字", "_v4"),
    ("10a", "红绳片段10a_看照片的人", "_v5"),
    ("10b", "红绳片段10b_到底是什么机构", "_v5"),
    ("10c", "红绳片段10c_笑容僵住", "_v7"),
]


def main() -> None:
    outs = []
    for sid, folder, suf in SEGS:
        cands = sorted((ROOT / folder / "视频草稿").glob(f"E04-{sid}_*{suf}_未审核草稿.mp4"))
        if not cands:
            print(f"[{sid}] 缺{suf}")
            continue
        asc = TMP / f"fin_{sid}.mp4"
        shutil.copy(cands[-1], asc)
        o = TMP / f"fin_{sid}.jpg"
        # 手腕区域，每段取一帧
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(asc),
                        "-vf", "select='eq(n\\,200)',crop=520:320:20:130,scale=420:-1",
                        "-frames:v", "1", str(o)], check=True)
        outs.append(o)
        print(f"[{sid}] {suf} ok")

    if not outs:
        return
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for o in outs:
        cmd += ["-i", str(o)]
    n = len(outs)
    filt = "".join(f"[{i}:v]" for i in range(n))
    # 统一高度后横向拼接
    cmd += ["-filter_complex",
            f"{filt}hstack=inputs={n}", "-frames:v", "1",
            str(TMP / "EP04_终版_四段手铐总验收.jpg")]
    subprocess.run(cmd, check=True)
    print("总验收图 ->", TMP / "EP04_终版_四段手铐总验收.jpg")


if __name__ == "__main__":
    main()
