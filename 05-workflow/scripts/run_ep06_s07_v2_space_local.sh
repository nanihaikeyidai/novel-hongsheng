#!/usr/bin/env bash
# EP06 S07 v2 空间标记控制｜本地梅林 0.5MP/Spark/DMaD
set -euo pipefail
ROOT="/d/HermesWorkspace/ai小说/红绳"
SEG="$ROOT/05-workflow/ep06/全本批量_梅林"
SCRIPTS="$ROOT/05-workflow/scripts"
CHARS="$ROOT/05-workflow/ep06/ep06素材/人物"
VOICE="$ROOT/05-workflow/归档素材/人物参考音色"
if ! curl -s --max-time 5 http://127.0.0.1:8188/system_stats >/dev/null 2>&1; then
  echo "ABORT: ComfyUI 127.0.0.1:8188 未运行，请用绘世启动器自行启动。" >&2
  exit 9
fi
cd "$SCRIPTS"
python -u run_local_meilin.py \
  --prompt "$SEG/提示词/梅林_S07_v2_空间标记控制.txt" \
  --img1 "$SEG/_diag/S07_空间标记参考图.png" \
  --img2 "$CHARS/蓝隼_EP06_角色参考.png" \
  --img3 "$SEG/安娜_露脸工装_ref.png" \
  --img4 "$CHARS/陆沉_EP06_白衬衫人设.png" \
  --audio1 "$VOICE/蓝隼.wav" \
  --tag S07_v2_local_space \
  --out "$SEG/视频草稿/EP06_S07_v2_本地_空间标记控制.mp4" \
  --no-sync
