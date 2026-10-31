# -*- coding: utf-8 -*-
"""
红绳 · 本地梅林出片（ComfyUI 8188）—— 项目默认视频路径（2026-10-19）
配方：0.7MP(约1152x640) / 8步 / Spark SM89 / DMaD 加速LoRA / int8_convrot VAE；API 默认 15s 段
（2026-10-25 定稿：DMaD 取代 turbo EMA，0.7 取代 0.6；2026-10-31 增加 vbvr 变体 --template vbvr）
UI 默认工作流：梅林全流程.json（与规范/AGENTS 同步）

用法:
  python run_local_meilin.py --prompt <提示词文件> --img1 <人设.png> [--img2 <场景.png>] [--img3 <分镜.png>]
                             [--seconds 15] [--out <输出mp4>] [--tag 名字]
                             [--template 0.7|vbvr|0.5|路径]
提示词文件内容会写入节点 263；图片自动复制进 ComfyUI/input 并按 49/50/51 槽位绑定。
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

COMFY = 'http://127.0.0.1:8188'
INPUT_DIR = Path(r'F:\Work-Fisher纯净包2026.8.7\ComfyUI\input')
TPL_DIR = Path(r'D:\HermesWorkspace\ai小说\红绳\05-workflow\全局文档\工作流规范')
TEMPLATE_DEFAULT = TPL_DIR / '本地梅林模板_SparkON_0.7MP_15s_dmad.json'
TEMPLATE_VBVR = TPL_DIR / '本地梅林模板_SparkON_0.7MP_15s_dmad_vbvr.json'
TEMPLATE_05 = TPL_DIR / '本地梅林模板_SparkON_0.5MP_15s.json'
TEMPLATE_06 = TPL_DIR / '本地梅林模板_旧版留存_turboEMA_0.6MP_20261025.json'
SLOTS = ['49', '50', '51']

# 开工前置同步（用户 2026-10-31 规则：每次制作前固定先拉云端代码）
REPO_ROOT = Path(__file__).resolve().parents[2]
SYNC_SCRIPT = REPO_ROOT / '05-workflow' / 'scripts' / 'pre_work_sync.sh'


def pre_work_sync(skip: bool = False) -> int:
    """开工前拉取云端代码。返回 0=已同步，1=同步失败(仍继续)，2=跳过。"""
    if skip:
        print('[sync] 已按 --no-sync 跳过开工同步')
        return 2
    if not SYNC_SCRIPT.exists():
        print(f'[sync] 警告：找不到同步脚本 {SYNC_SCRIPT}，跳过')
        return 1
    print('[sync] 开工前拉取云端代码 ...')
    try:
        r = subprocess.run(['bash', str(SYNC_SCRIPT)], cwd=str(REPO_ROOT),
                           capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        print('[sync] 同步超时（网络问题），继续制作')
        return 1
    out = (r.stdout or '') + (r.stderr or '')
    tail = '\n'.join(out.strip().splitlines()[-8:])
    print(tail)
    if r.returncode != 0:
        print(f'[sync] 同步返回 {r.returncode}，继续制作（本地改动未受影响）')
        return 1
    print('[sync] 云端代码已是最新')
    return 0


def post(path, payload, timeout=120):
    req = urllib.request.Request(COMFY + path, data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def get(path, timeout=60):
    with urllib.request.urlopen(COMFY + path, timeout=timeout) as r:
        return json.load(r)


def resolve_template(arg: str | None) -> Path:
    if not arg or arg in ('0.7', '0.7mp', 'dmad', 'default'):
        return TEMPLATE_DEFAULT
    if arg in ('vbvr', '0.7vbvr'):
        return TEMPLATE_VBVR
    if arg in ('0.6', '0.6mp', 'turbo'):
        return TEMPLATE_06
    if arg in ('0.5', '0.5mp'):
        return TEMPLATE_05
    p = Path(arg)
    if not p.exists():
        raise FileNotFoundError(f'template not found: {arg}')
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prompt', required=True)
    ap.add_argument('--img1', default=None)
    ap.add_argument('--img2', default=None)
    ap.add_argument('--img3', default=None)
    ap.add_argument('--seconds', type=float, default=15.0)
    ap.add_argument('--tag', default='local_meilin')
    ap.add_argument('--out', default=None)
    ap.add_argument('--template', default='0.7', help='0.7 | vbvr | 0.5 | 0.6(旧turbo) | path-to-api-json')
    ap.add_argument('--no-sync', action='store_true',
                    help='跳过开工前的云端代码同步（默认每次都拉）')
    a = ap.parse_args()

    # 开工第一件事：拉云端代码（用户 2026-10-31 规则）
    pre_work_sync(skip=a.no_sync)

    tpl = resolve_template(a.template)
    wf = json.loads(tpl.read_text(encoding='utf-8'))['prompt']
    prompt_text = Path(a.prompt).read_text(encoding='utf-8').strip()
    wf['263']['inputs']['text'] = prompt_text
    wf['259']['inputs']['value'] = a.seconds
    mp = (wf.get('252') or {}).get('inputs', {}).get('megapixels')
    print(f'template={tpl.name} | mp={mp} | 提示词 {len(prompt_text)} 字符 | 时长 {a.seconds}s')

    for slot, src in zip(SLOTS, [a.img1, a.img2, a.img3]):
        if not src:
            continue
        src_p = Path(src)
        if not src_p.exists():
            raise FileNotFoundError(src)
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
        dst = INPUT_DIR / src_p.name
        shutil.copy2(src_p, dst)
        wf[slot]['inputs']['image'] = src_p.name
        print(f'  槽位 {slot} <- {src_p.name}')

    for nid in ('214', '264'):
        if nid in wf:
            wf[nid]['inputs']['filename_prefix'] = a.tag

    t0 = time.time()
    resp = post('/prompt', {'prompt': wf})
    pid = resp.get('prompt_id')
    if not pid:
        print('提交失败:', resp)
        return 2
    print(f'已提交 prompt_id={pid}')

    while time.time() - t0 < 3600:
        time.sleep(20)
        el = (time.time() - t0) / 60
        try:
            q = get('/queue')
            run = len(q.get('queue_running') or [])
            pend = len(q.get('queue_pending') or [])
        except Exception:
            run = '?'; pend = '?'
        hist = {}
        try:
            hist = get(f'/history/{pid}')
        except Exception:
            pass
        print(f'  [{el:.1f}min] running={run} pending={pend}')
        if hist and pid in hist:
            rec = hist[pid]
            st = (rec.get('status') or {}).get('status_str')
            print('  完成:', st, f'耗时 {(time.time()-t0)/60:.1f} 分钟')
            outs = (rec.get('outputs') or {})
            saved = []
            for nid, o in outs.items():
                for v in (o.get('gifs') or o.get('videos') or []):
                    fn = v.get('filename'); sub = v.get('subfolder', '')
                    src = FALLBACK_OUT / sub / fn if sub else FALLBACK_OUT / fn
                    print('  输出:', src)
                    if a.out and src.exists():
                        out_p = Path(a.out)
                        out_p.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, out_p)
                        print('  已复制到', out_p)
                        saved.append(out_p)
            if st and st != 'success':
                return 3
            return 0 if (outs or st == 'success') else 4
    print('超时未完成')
    return 5


FALLBACK_OUT = Path(r'F:\Work-Fisher纯净包2026.8.7\ComfyUI\output')

if __name__ == '__main__':
    import urllib.parse
    sys.exit(main())
