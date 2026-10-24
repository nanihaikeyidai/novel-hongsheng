"""10c v6 验收：重点看桌面是否还多出第二副手铐。"""
import shutil
import subprocess
from pathlib import Path

SRC = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep04"
           r"\红绳片段10c_笑容僵住\视频草稿\E04-10c_笑容僵住_v6_未审核草稿.mp4")
TMP = Path("F:/h3tmp")


def main() -> None:
    asc = TMP / "v6_10c.mp4"
    shutil.copy(SRC, asc)
    # 全景多帧：看桌面
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(asc),
                    "-vf", "select='eq(n\\,15)+eq(n\\,120)+eq(n\\,200)+eq(n\\,300)',"
                           "crop=800:400:80:150,scale=520:-1,tile=2x2",
                    "-frames:v", "1", str(TMP / "v6_10c_desk.jpg")], check=True)
    # 手腕特写
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(asc),
                    "-vf", "select='eq(n\\,30)+eq(n\\,340)',crop=560:340:40:120,"
                           "scale=560:-1,tile=2x1",
                    "-frames:v", "1", str(TMP / "v6_10c_wrist.jpg")], check=True)
    print("ok ->", TMP)


if __name__ == "__main__":
    main()
