"""读出金鱼工作流的关键配置，并与本地已跑通的探针工作流逐项对比。"""
import json
from pathlib import Path

api = json.loads(Path("F:/h3tmp/jinyu_api.json").read_text(encoding="utf-8"))
probe = json.loads(
    Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep04\临时\h3_t2va_probe_api.json")
    .read_text(encoding="utf-8"))

KEEP = ("UNETLoader", "CLIPLoader", "VAELoader", "LoraLoaderModelOnly",
        "MiniMaxH3ReferenceToVideo", "SelfLiftH3Sampler",
        "KSamplerSelect", "BasicScheduler", "MiniMaxH3SigmaShift",
        "BlockSparseAttention", "ModelAttentionBackend", "ResolutionSelector",
        "VHS_VideoCombine", "忽略多组孤海")

print("=" * 74)
print("金鱼工作流关键节点配置")
print("=" * 74)
for nid, n in sorted(api.items(), key=lambda kv: int(kv[0])):
    if n["class_type"] not in KEEP:
        continue
    ins = n["inputs"]
    print(f"\n--- #{nid} {n['class_type']} ---")
    for k, v in ins.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            print(f"   {k} = {v}")
        else:
            print(f"   {k} = {json.dumps(v, ensure_ascii=False)[:90]}")

print()
print("=" * 74)
print("本地探针（已跑通的 Ref2VA）对应配置")
print("=" * 74)
for nid, n in sorted(probe.items(), key=lambda kv: int(kv[0])):
    if n["class_type"] not in KEEP:
        continue
    print(f"\n--- #{nid} {n['class_type']} ---")
    for k, v in n["inputs"].items():
        if k == "prompt":
            print(f"   prompt = <{len(v)} 字，省略>")
        else:
            print(f"   {k} = {json.dumps(v, ensure_ascii=False)[:90]}")
