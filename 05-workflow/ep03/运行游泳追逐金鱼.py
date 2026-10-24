# -*- coding: utf-8 -*-
"""用云端金鱼工作流跑 EP03 游泳追逐特写（15秒，无对白）。"""
from __future__ import annotations
import sys
import time
from pathlib import Path

RUNNINGHUB_SCRIPTS = Path(r'C:\Users\Administrator\.codex\skills\runninghub\scripts')
sys.path.insert(0, str(RUNNINGHUB_SCRIPTS))

from runninghub import download_file, fix_mov_to_mp4, poll_task, require_api_key  # noqa
from runninghub_app import _guess_ext_from_url, apply_modifications, get_node_info, submit_task  # noqa

ROOT = Path(r'D:\HermesWorkspace\ai小说\红绳')
APP_ID = '2093984226331938818'
SLOT_NODES = ('51', '49', '50', '43', '19', '23')

SEG = ROOT / '05-workflow' / 'ep03' / '红绳片段10'
PROMPT_FILE = SEG / '视频提示词_游泳追逐特写.md'
OUT = SEG / '视频草稿' / 'E03-10_游泳追逐特写_未审核草稿.mp4'

REFS = [
    ROOT / '05-workflow' / 'ep03' / '归档素材' / '人物' / '安娜_游泳社人设.png',
    ROOT / '05-workflow' / 'ep03' / '归档素材' / '人物' / '李想_游泳社人设.png',
    ROOT / '05-workflow' / 'ep03' / '归档素材' / '场景' / '场景_室内标准泳池_无人.png',
]


def main():
    api_key = require_api_key(None)
    prompt = PROMPT_FILE.read_text(encoding='utf-8')
    print('提示词字符数:', len(prompt), flush=True)

    node_args = [
        f'263:text={prompt}',
        '252:aspect_ratio=16:9 (Widescreen)',
        '252:megapixels=0.6',
        '259:value=15',
        '283:value=1',
    ]
    file_args = []
    for i, p in enumerate(REFS):
        if not p.exists():
            raise FileNotFoundError(p)
        file_args.append(f'{SLOT_NODES[i]}:image={p}')
        print('  参考图:', p.name, flush=True)

    print('提交金鱼应用...', flush=True)
    nodes = apply_modifications(api_key, get_node_info(api_key, APP_ID), node_args, file_args)
    data = None
    for attempt in range(1, 41):
        try:
            data = submit_task(api_key, APP_ID, nodes)
            break
        except Exception as exc:
            msg = str(exc)
            if 'TASK_QUEUE_MAXED' in msg or '421' in msg:
                print(f'  [尝试{attempt}] 队列满（并发=1），60秒后重试...', flush=True)
                time.sleep(60)
                continue
            print('  提交异常:', msg[:300], flush=True)
            raise
    if not data:
        raise RuntimeError('重试40次仍无法提交（队列一直满）')
    task_id = str(data.get('taskId'))
    print('taskId:', task_id, flush=True)

    final = poll_task(api_key, task_id)
    results = final.get('results') or []
    print('结果数:', len(results), flush=True)
    for i, item in enumerate(results, 1):
        url = item.get('url') or item.get('outputUrl')
        if not url:
            continue
        out = OUT if len(results) == 1 else OUT.with_name(f'{OUT.stem}_{i}{OUT.suffix}')
        d = download_file(url, str(out))
        fix_mov_to_mp4(d)
        print(f'OUTPUT_FILE:{d}', flush=True)
    usage = final.get('usage') or {}
    print('COST:', usage.get('consumeMoney') or usage.get('consumeCoins'), flush=True)


if __name__ == '__main__':
    main()
