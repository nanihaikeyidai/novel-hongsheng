from __future__ import annotations

import sys
from pathlib import Path

RUNNINGHUB_SCRIPTS = Path(r'C:\Users\Administrator\.codex\skills\runninghub\scripts')
sys.path.insert(0, str(RUNNINGHUB_SCRIPTS))

from runninghub import download_file, fix_mov_to_mp4, poll_task, require_api_key  # noqa: E402
from runninghub_app import apply_modifications, get_node_info, submit_task  # noqa: E402

ROOT = Path(r'D:\HermesWorkspace\ai小说\红绳')
APP_ID = '2093984226331938818'
BASE = ROOT / '05-workflow' / 'ep03' / '红绳片段02' / '视频对比' / '线稿故事板'


def main() -> None:
    api_key = require_api_key(None)
    prompt = (BASE / '视频提示词.md').read_text(encoding='utf-8')
    output = BASE / 'E03-02_线稿故事板参考_未审核草稿.mp4'
    refs = [
        '51:image=' + str(ROOT / '05-workflow' / 'ep03' / '归档素材' / '人物' / '安娜_游泳社人设.png'),
        '49:image=' + str(ROOT / '05-workflow' / 'ep03' / '归档素材' / '场景' / '场景_红杉高中校门_晴天_无人.png'),
        '50:image=' + str(BASE / '故事板_线稿空间参考.png'),
    ]
    for ref in refs:
        path = Path(ref.split('=', 1)[1])
        if not path.exists():
            raise FileNotFoundError(str(path))

    print('开始生成片段02线稿故事板参考版。', flush=True)
    node_args = [
        '263:text=' + prompt,
        '252:aspect_ratio=16:9 (Widescreen)',
        '252:megapixels=0.6',
        '259:value=15',
        '283:value=1',
    ]
    nodes = apply_modifications(api_key, get_node_info(api_key, APP_ID), node_args, refs)
    data = submit_task(api_key, APP_ID, nodes)
    final = poll_task(api_key, str(data['taskId']))
    results = final.get('results') or []
    if not results:
        raise RuntimeError('任务完成但没有返回视频文件')
    result = results[0]
    url = result.get('url') or result.get('outputUrl')
    if not url:
        raise RuntimeError('结果中没有视频地址')
    output.parent.mkdir(parents=True, exist_ok=True)
    downloaded = download_file(url, str(output))
    fix_mov_to_mp4(downloaded)
    print('OUTPUT_FILE:' + downloaded, flush=True)


if __name__ == '__main__':
    main()
