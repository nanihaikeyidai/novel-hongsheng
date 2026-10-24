# -*- coding: utf-8 -*-
"""把各场模块里的提示词变量导出到各片段目录的「动作流_H3纯提示词.txt」。

用法：
    python export_ep04_prompts.py            # 只导出并做门禁检查，不覆盖已有的（--force 强制覆盖）
    python export_ep04_prompts.py --force    # 强制覆盖全部
    python export_ep04_prompts.py 09a 10c    # 只处理指定片段
"""
import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import run_ep04_interrogation_rh as R          # noqa: E402

# 片段 ID -> (模块名, 模块内变量名)
MAPPING = {
    "09a": ("ep04_s09_prompts", "S09_S1"),
    "09b": ("ep04_s09_prompts", "S09_S2"),
    "09c": ("ep04_s09_prompts", "S09_S3"),
    "09d": ("ep04_s09_prompts", "S09_S4"),
    "10a": ("ep04_s10_prompts", "S10_S1"),
    "10b": ("ep04_s10_prompts", "S10_S2"),
    "10c": ("ep04_s10_prompts", "S10_S3"),
    "11a": ("ep04_s11_prompts", "S11_S1"),
    "11b": ("ep04_s11_prompts", "S11_S2"),
    "11c": ("ep04_s11_prompts", "S11_S3"),
    "11d": ("ep04_s11_prompts", "S11_S4"),
    "12a": ("ep04_s12_prompts", "S12_S1"),
    "12b": ("ep04_s12_prompts", "S12_S2"),
    "12c": ("ep04_s12_prompts", "S12_S3"),
    "12d": ("ep04_s12_prompts", "S12_S4"),
    "12e": ("ep04_s12_prompts", "S12_S5"),
    "12e2": ("ep04_s12_prompts", "S12_S5B"),
    "12f": ("ep04_s12_prompts", "S12_S6"),
    "12g": ("ep04_s12_prompts", "S12_S7"),
    "13a": ("ep04_s13_15_prompts", "S13_S1"),
    "13b": ("ep04_s13_15_prompts", "S13_S2"),
    "14a": ("ep04_s13_15_prompts", "S14_S1"),
    "14b": ("ep04_s13_15_prompts", "S14_S2"),
    "15a": ("ep04_s13_15_prompts", "S15_S1"),
    "15b": ("ep04_s13_15_prompts", "S15_S2"),
    "15c": ("ep04_s13_15_prompts", "S15_S3"),
}

H3_LABELS = ["subject_definitions:", "summary:", "retention_analysis:",
             "detailed_description:", "overall_soundscape:", "non_diegetic_music:"]


def check(seg_id: str, prompt: str) -> list[str]:
    """H3 硬门禁 + 台词时长门禁。"""
    errs = []
    pos = [prompt.find(l) for l in H3_LABELS]
    if any(i < 0 for i in pos) or pos != sorted(pos) \
            or not prompt.startswith("subject_definitions:"):
        errs.append("H3 六段标签缺失或顺序错误")
    n_aud = len(R.SEGMENTS[seg_id].get("audios", []))
    dec = len(set(re.findall(r"<Audio (\d+)>", prompt)))
    if dec != n_aud:
        errs.append(f"音频声明 {dec} ≠ 实际绑定 {n_aud}")
    if re.findall(r"\(S\d+\)\s*<d>", prompt):
        errs.append("重复说话人标签")
    for bad in ("```", "@图片", "**"):
        if bad in prompt:
            errs.append(f"含禁用记号 {bad}")

    lines = re.findall(r"<d>\[Chinese\](.*?)</d>", prompt, re.S)
    total = sum(len(re.sub(r"\s", "", x)) for x in lines)
    if total > 55:
        errs.append(f"台词过密 {total} 字（{total / 4.5:.1f}s / 上限 55 字）")
    for x in lines:
        k = len(re.sub(r"\s", "", x))
        if k > 34:
            errs.append(f"单句过长 {k} 字 —— {re.sub(chr(10), ' ', x)[:20]}…")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("segments", nargs="*", help="只处理这些片段 ID（默认全部）")
    ap.add_argument("--force", action="store_true", help="覆盖已有文件")
    args = ap.parse_args()

    mods = {}
    targets = args.segments or list(MAPPING)
    bad = written = skipped = 0

    for seg_id in targets:
        if seg_id not in MAPPING:
            print(f"跳过未知片段 {seg_id}")
            continue
        mod_name, var = MAPPING[seg_id]
        if mod_name not in mods:
            mods[mod_name] = __import__(mod_name)
        prompt = getattr(mods[mod_name], var).strip()

        errs = check(seg_id, prompt)
        seg = R.ROOT / "05-workflow" / "ep04" / R.SEGMENTS[seg_id]["dir"]
        out = seg / "动作流_H3纯提示词.txt"

        lines = re.findall(r"<d>\[Chinese\](.*?)</d>", prompt, re.S)
        total = sum(len(re.sub(r"\s", "", x)) for x in lines)
        mx = max([len(re.sub(r"\s", "", x)) for x in lines] or [0])

        if errs:
            bad += 1
            print(f"❌ {seg_id} {R.SEGMENTS[seg_id]['title']}  台词 {total} 字/{total/4.5:.1f}s")
            for e in errs:
                print(f"     - {e}")
            continue

        if out.exists() and not args.force:
            if out.read_text(encoding="utf-8").strip() == prompt:
                skipped += 1
                print(f"＝ {seg_id} 无变化")
                continue
            skipped += 1
            print(f"· {seg_id} 有更新（未覆盖，加 --force）")
            continue

        seg.mkdir(parents=True, exist_ok=True)
        out.write_text(prompt, encoding="utf-8")
        written += 1
        print(f"✓ {seg_id} {R.SEGMENTS[seg_id]['title']}  "
              f"台词 {total} 字/{total / 4.5:.1f}s 最长 {mx} 字  已导出")

    print(f"\n导出 {written} · 无变化/跳过 {skipped} · 门禁未过 {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
