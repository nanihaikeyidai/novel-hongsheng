"""EP04 v4 四段手铐一致性终验：逐段抽帧拼成一张对照图。

判定标准（四段都应处于 cuffed 态）：
  合格：铐环闭合、套在手腕上、短链连桌沿
  不合格：铐环张开 / 铐具平放桌面 / 铐具消失 / 铐具变成绳索扎带
输出：ASCII 路径（ffmpeg 对中文输出路径会报 Could not open file）
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep04")
TMP = Path("F:/h3tmp")
SEGS = [
    ("09c", "红绳片段09c_陆定天的名字", "E04-09c_陆定天的名字_v4_未审核草稿.mp4"),
    ("10a", "红绳片段10a_看照片的人", "E04-10a_看照片的人_v4_未审核草稿.mp4"),
    ("10b", "红绳片段10b_到底是什么机构", "E04-10b_到底是什么机构_v4_未审核草稿.mp4"),
    ("10c", "红绳片段10c_笑容僵住", "E04-10c_笑容僵住_v4_未审核草稿.mp4"),
]


def main() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    rows = []
    for sid, folder, name in SEGS:
        src = ROOT / folder / "视频草稿" / name
        if not src.exists():
            print(f"[{sid}] 缺失 {src}")
            continue
        asc = TMP / f"v4_{sid}.mp4"
        shutil.copy(src, asc)
        out = TMP / f"v4_{sid}_f.jpg"
        # 每段取 3 帧：前 1/6、中、后 1/6
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(asc),
             "-vf", "select='eq(n\\,20)+eq(n\\,180)+eq(n\\,355)',scale=360:-1,tile=3x1",
             "-frames:v", "1", str(out)],
            check=True,
        )
        rows.append((sid, out))
        print(f"[{sid}] ok")

    # 4 段 x 3 帧 = 12 格，拼 3 行 x 4 列便于横向对比
    tiles = "".join(f"[{i}:v]" for i in range(len(rows)))
    inputs = []
    for _, p in rows:
        inputs += ["-i", str(p)]
    filt = "".join(f"[{i}:v]" for i in range(len(rows)))
    grid = f"{filt}xstack=inputs={len(rows)}:layout="
    layout = "|".join(f"0_{i}" for i in range(len(rows)))
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for _, p in rows:
        cmd += ["-i", str(p)]
    cmd += ["-filter_complex",
            f"{filt}concat=n={len(rows)}:v=1:a=0", "-frames:v", "1",
            str(TMP / "EP04_v4_四段手铐对照.jpg")]
    subprocess.run(cmd, check=True)
    print("对照图 ->", TMP / "EP04_v4_四段手铐对照.jpg")


if __name__ == "__main__":
    main()
