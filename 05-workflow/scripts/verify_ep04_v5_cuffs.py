"""EP04 v5 三段（10a/10b/10c）手铐位置验收。

09c 沿用 v4（已验收合格），本脚本只查 v5 三段。
判定：手腕上有闭合铐环 = 通过；铐具平放桌面 / 张开 / 消失 = 不通过。
"""
import shutil
import subprocess
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep04")
TMP = Path("F:/h3tmp")
SEGS = [
    ("10a", "红绳片段10a_看照片的人", "E04-10a_看照片的人_v5_未审核草稿.mp4"),
    ("10b", "红绳片段10b_到底是什么机构", "E04-10b_到底是什么机构_v5_未审核草稿.mp4"),
    ("10c", "红绳片段10c_笑容僵住", "E04-10c_笑容僵住_v5_未审核草稿.mp4"),
]


def main() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    for sid, folder, name in SEGS:
        src = ROOT / folder / "视频草稿" / name
        if not src.exists():
            print(f"[{sid}] 缺失")
            continue
        asc = TMP / f"v5_{sid}.mp4"
        shutil.copy(src, asc)
        # 手腕区域特写：陆沉固定在画面左侧
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(asc),
                        "-vf", "select='eq(n\\,30)+eq(n\\,200)+eq(n\\,340)',"
                               "crop=520:340:60:120,scale=520:-1,tile=3x1",
                        "-frames:v", "1", str(TMP / f"v5_{sid}_wrist.jpg")], check=True)
        # 全景一张，看铐具有没有跑到桌面中央
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(asc),
                        "-vf", "select='eq(n\\,200)',scale=640:-1",
                        "-frames:v", "1", str(TMP / f"v5_{sid}_wide.jpg")], check=True)
        print(f"[{sid}] ok")
    print("输出 ->", TMP)


if __name__ == "__main__":
    main()
