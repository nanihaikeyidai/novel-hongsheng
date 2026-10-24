"""从 EP04 四段提示词里提取台词（<d>[Chinese]…</d>），作为 ASR 比对基准。"""
import re
from pathlib import Path

ROOT = Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep04")
SEGS = [
    ("09c", "红绳片段09c_陆定天的名字"),
    ("10a", "红绳片段10a_看照片的人"),
    ("10b", "红绳片段10b_到底是什么机构"),
    ("10c", "红绳片段10c_笑容僵住"),
]
# 终版各段起始秒（含 0.25s 段间黑场）
STARTS = {"09c": 0.0, "10a": 15.333, "10b": 30.666, "10c": 46.0}

out = []
for sid, folder in SEGS:
    t = (ROOT / folder / "动作流_H3纯提示词.txt").read_text(encoding="utf-8")
    lines = re.findall(r"<d>\[Chinese\](.*?)</d>", t, re.S)
    body = [x.strip() for x in lines if x.strip()]
    print(f"=== {sid}  起始 {STARTS[sid]:.2f}s ===")
    for i, b in enumerate(body):
        print(f"  [{i+1}] {b}  ({len(b)} 字)")
        out.append((sid, i + 1, b))
    print()

# 汇总成 JSON 便于后续比对
import json
Path("F:/h3tmp/r2t2_ep04/expected_dialogue.json").write_text(
    json.dumps([{"seg": s, "idx": i, "text": t} for s, i, t in out],
               ensure_ascii=False, indent=1), encoding="utf-8")
print("基准已存 expected_dialogue.json")
