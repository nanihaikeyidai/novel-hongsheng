# -*- coding: utf-8 -*-
"""EP03 钩子片段：赵凯×小月 ND 办公室对话（15秒，含人设图+音色参考）。"""
from __future__ import annotations
import sys
from pathlib import Path

RUNNINGHUB_SCRIPTS = Path(r'C:\Users\Administrator\.codex\skills\runninghub\scripts')
sys.path.insert(0, str(RUNNINGHUB_SCRIPTS))

from runninghub import download_file, fix_mov_to_mp4, poll_task, require_api_key  # noqa
from runninghub_app import apply_modifications, get_node_info, submit_task  # noqa

ROOT = Path(r'D:\HermesWorkspace\ai小说\红绳')
APP_ID = '2093984226331938818'

SEG = ROOT / '05-workflow' / 'ep03' / '红绳片段17_钩子'
PROMPT_FILE = SEG / '视频提示词_ND办公室对话.md'
OUT = SEG / 'E03-17_钩子_ND办公室对话_未审核草稿.mp4'

# (路径, 节点ID, 字段名)
SLOTS = [
    (ROOT / '05-workflow' / '归档素材' / '人物' / 'ND调查员_赵凯.png', '51', 'image'),
    (ROOT / '05-workflow' / '归档素材' / '人物' / 'ND值班员_小月.png', '49', 'image'),
    (ROOT / '05-workflow' / 'ep02' / '归档素材' / '场景' / '场景_ND值班中心_无人.png', '50', 'image'),
    (ROOT / '05-workflow' / '归档素材' / '人物参考音色' / '赵凯.wav', '48', 'audio'),
    (ROOT / '05-workflow' / '归档素材' / '人物参考音色' / '小月.wav', '14', 'audio'),
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
    for path, node, field in SLOTS:
        if not path.exists():
            raise FileNotFoundError(path)
        file_args.append(f'{node}:{field}={path}')
        print(f'  素材 {node}:{field} -> {path.name}', flush=True)

    print('提交金鱼应用...', flush=True)
    nodes = apply_modifications(api_key, get_node_info(api_key, APP_ID), node_args, file_args)
    data = submit_task(api_key, APP_ID, nodes)
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
