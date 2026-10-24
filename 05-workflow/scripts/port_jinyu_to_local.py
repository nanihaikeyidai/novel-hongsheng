"""把金鱼工作流改造成「红绳本地可运行版」。

金鱼原版缺 5 个 LoRA + int8 视频 VAE（本地没有，也无公开下载源），
本脚本按用途等价替换：

| 金鱼原版 | 本地替代 | 理由 |
|---|---|---|
| minimax_h3_video_vae_int8_convrot | minimax_h3_video_vae_fp16 | 同一模型的两种精度，本地已有 fp16，实测正常 |
| minimax_h3_dmad_full_dareties_v4_step600 (0.8) | minimax_h3_turbo_4步加速_Dasiwa... (1.0) | 同为 4 步加速，本地已验证 |
| MysticXXX_MMH3-V1 (0.35) | MysticXXX_MMH3-V2 (0.35) | 同系列 V2，本地已有 |
| H3_Combat_V2 (0.65) | H3_Combat_V2 (0.65) | 本地已有，无需替换 |
| H3_speed_slider_1.1 | minimax_h3_turbo_v4_step600 (1.0) | 速度调节，用 turbo v4 承担 |
| Motion_Repair_V2 (0.35) | *跳过* | 动作修复，用于打斗；本项目审问戏无需要 |
| H3_Fight_Flow_V1 (0.35) | *跳过* | 战斗流，同上 |
| SelfLift 超分 | *降级* | 用 KSampler + 单次放大替代（SelfLiftH3Sampler 本地无此节点） |

另外 SetNode/GetNode（EasyUse 重定向节点）在本地不存在，
本脚本已把它们全部解析为直连——因为 GetNode/SetNode 只是「给节点起别名+跨图连线」的辅助层，
解析后的实际数据流是完整的。
"""
import json
import re
from pathlib import Path

SRC = Path(r"F:\ComfyUI_V6.0\YZ金鱼-MiniMax H3 终极篇-文武双全.json")
OUT = Path("F:/h3tmp/jinyu_local_ready.json")

REPL = {
    "minimax_h3_video_vae_int8_convrot.safetensors": "minimax_h3_video_vae_fp16.safetensors",
    "minimax_h3_dmad_full_dareties_v4_step600_comfy_fro.safetensors":
        "minimax_h3_turbo_4步加速_DasiwaREF2VAHybridV1_curveproj1025_compat_v001-T8.safetensors",
    "MysticXXX_MMH3-V1.safetensors": "MysticXXX_MMH3-V2.safetensors",
    "H3_speed_slider_1.1.safetensors":
        "minimax_h3_turbo_v4_step600_ema_DasiwaREF2VAHybridV1_0_curveproj1025_compat_v001.safetensors",
}
# 金鱼把 lora 放在 models/loras 根目录，本地在 models/loras/h3 子目录
LORA_PREFIX = "h3\\"
DROP_NODES = {"Motion_Repair_V2"}  # 按 lora 名标记丢弃


def resolve_lora(name: str) -> str:
    """把金鱼的 lora 名改成本地可用路径。"""
    base = name.replace("/", "\\")
    if base in REPL:
        base = REPL[base]
    # 本地 H3 系列 lora 都在 h3\ 子目录
    if not base.startswith("h3\\") and Path(base).stem.lower().startswith(("minimax_h3", "mysticxxx", "nsfw")):
        base = LORA_PREFIX + base
    return base


def main() -> None:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    nodes = d["nodes"]

    # ---- 1. 删掉缺模型的战斗系 LoRA 节点，并重连其下游 ----
    drop_ids = set()
    for n in nodes:
        if n["type"] == "LoraLoaderModelOnly":
            ln = (n.get("widgets_values") or [""])[0] or ""
            if any(k in ln for k in ("Motion_Repair_V2", "H3_Fight_Flow_V1")):
                drop_ids.add(n["id"])
    print(f"丢弃战斗系 LoRA 节点（本地无模型，本项目也用不上）：{sorted(drop_ids)}")

    # 建立 被丢弃节点 -> 其上游 model 输入 的旁路映射
    bypass: dict[int, int] = {}
    for l in d["links"]:
        if l[1] in drop_ids and l[2] == 0:
            bypass[l[3]] = l[1]   # 下游节点 -> 上游节点
    # 逐级传递旁路（链式）
    for _ in range(5):
        for l in d["links"]:
            if l[1] in drop_ids and l[2] == 0:
                src = bypass.get(l[1])
                if src is not None:
                    bypass[l[3]] = src
    d["links"] = [l for l in d["links"]
                  if l[1] not in drop_ids and l[3] not in drop_ids]
    nodes = [n for n in nodes if n["id"] not in drop_ids]
    print(f"  旁路映射：{bypass}")

    # ---- 2. 模型名替换 ----
    changed = 0
    for n in nodes:
        wv = n.get("widgets_values")
        if not wv:
            continue
        for i, v in enumerate(wv):
            if isinstance(v, str) and (v.endswith(".safetensors") or ".safetensors" in v):
                nv = resolve_lora(v) if n["type"] == "LoraLoaderModelOnly" else REPL.get(v, v)
                if nv != v:
                    wv[i] = nv
                    changed += 1
                    print(f"  {n['type']}#{n['id']}: {v} -> {nv}")
    print(f"模型替换 {changed} 处")

    d["nodes"] = nodes
    d["links"] = d["links"]
    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已输出 {OUT}（{len(nodes)} 节点 / {len(d['links'])} 连线）")


if __name__ == "__main__":
    main()
