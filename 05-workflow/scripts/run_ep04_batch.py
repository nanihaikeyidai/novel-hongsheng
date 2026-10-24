# -*- coding: utf-8 -*-
"""EP04 审讯线批量渲染：串行跑多个片段，逐段体检，失败不中断。

用法：
    python run_ep04_batch.py 09b 09c 09d 10a 10b 10c
"""
from __future__ import annotations

import importlib.util
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("rh", HERE / "run_ep04_interrogation_rh.py")
rh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rh)

EP = rh.EP if hasattr(rh, "EP") else Path(r"D:\HermesWorkspace\ai小说\红绳\05-workflow\ep04")


def main() -> int:
    segs = sys.argv[1:]
    if not segs:
        print("用法：python run_ep04_batch.py <片段编号...>")
        return 1
    bad = [s for s in segs if s not in rh.SEGMENTS]
    if bad:
        print(f"未知片段编号：{bad}\n可用：{sorted(rh.SEGMENTS)}")
        return 1

    api_key = rh.require_api_key(os.environ.get("RH_API_KEY"))
    t0 = time.time()
    results: list[tuple[str, bool, str]] = []
    for i, seg in enumerate(segs, 1):
        print(f"\n{'=' * 62}\n[{i}/{len(segs)}] 片段 {seg} {rh.SEGMENTS[seg]['title']}")
        print(f"{'=' * 62}", flush=True)
        s = time.time()
        try:
            rc = rh.run_segment(api_key, seg)
        except Exception as e:  # 单段失败不中断整批
            print(f"❌ 片段{seg}异常：{e}", file=sys.stderr)
            rc = 1
        dt = (time.time() - s) / 60
        print(f"--- 片段 {seg} {'完成' if rc == 0 else '失败'}，耗时 {dt:.1f} 分钟")
        results.append((seg, rc == 0, f"{dt:.1f}min"))

    print(f"\n{'=' * 62}\n批量执行结束，总耗时 {(time.time() - t0) / 60:.1f} 分钟")
    for seg, ok, info in results:
        print(f"  {'✓' if ok else '✗'} 片段{seg}  {info}")
    print("=" * 62)
    return 0 if all(ok for _, ok, _ in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())