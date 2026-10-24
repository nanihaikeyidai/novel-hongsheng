"""检查 10a/10b/10c 落盘提示词里的铐态描述是否已同步为 v4 版本。"""
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep04")
SEGS = {
    "09c": "红绳片段09c_陆定天的名字",
    "10a": "红绳片段10a_看照片的人",
    "10b": "红绳片段10b_到底是什么机构",
    "10c": "红绳片段10c_笑容僵住",
}
BAD = ("允许变化：手铐的咬合状态", "手铐凭空消失", "手腕上没有铐具",
       "打开着放在", "摘下放在", "放在桌沿固定环旁")

for sid, folder in SEGS.items():
    f = ROOT / folder / "动作流_H3纯提示词.txt"
    if not f.exists():
        print(f"[{sid}] 缺文件")
        continue
    t = f.read_text(encoding="utf-8")
    print(f"=== {sid}  {len(t)} 字 ===")
    for b in BAD:
        if b in t:
            print(f"  ✗ 命中旧/反噬表述：{b}")
    # 打印 Subject 4 段落
    i = t.find("<Subject 4>")
    j = t.find("<Subject 5>")
    seg = t[i:j] if i >= 0 else "(未找到 Subject 4)"
    print("  " + seg[:400].replace("\n", "\n  "))
    print()
