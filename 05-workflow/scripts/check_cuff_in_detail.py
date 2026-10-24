"""检查四段提示词的 detailed_description 里是否存在把铐具定位到桌面的表述。"""
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep04")
SEGS = {
    "09c": "红绳片段09c_陆定天的名字",
    "10a": "红绳片段10a_看照片的人",
    "10b": "红绳片段10b_到底是什么机构",
    "10c": "红绳片段10c_笑容僵住",
}
KEY = ("手铐", "铐环", "铐具", "短链", "金属环")

for sid, folder in SEGS.items():
    t = (ROOT / folder / "动作流_H3纯提示词.txt").read_text(encoding="utf-8")
    i = t.find("detailed_description:")
    j = t.find("overall_soundscape:")
    body = t[i:j]
    print(f"===== {sid} =====")
    for line in body.replace("。", "。\n").split("\n"):
        if any(k in line for k in KEY):
            print("   ", line.strip())
    print()
