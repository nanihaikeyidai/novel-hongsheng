#!/usr/bin/env bash
# EP06 S05 v6 瞳孔红/镜头对陆沉｜本地梅林 0.5MP/Spark/DMaD。
# 三处反馈：①陆沉只有瞳孔两个针尖红点（非眼眶/眼白）②蓝隼眼睛不变红（墨镜不透光+眼周正常肤色）③陆沉朝镜头跑来进攻、进攻镜对着陆沉。
# 台词四层锁（G29）原样保留：结构归位/秒数锁/说完闭嘴/空窗表演填。
# 图槽映射（--imgN ≠ <Picture N>，G05）：
#   --img1 -> <Picture 2> 车库 ; --img2 -> <Picture 3> 蓝隼
#   --img3 -> <Picture 1> 安娜 ; --img4 -> <Picture 4> 陆沉
# 音频：蓝隼音色参考；台词写回 <d> 但仅音频不渲染字幕。
set -euo pipefail
ROOT="/d/HermesWorkspace/ai小说/红绳"
SEG="$ROOT/05-workflow/ep06/全本批量_梅林"
SCRIPTS="$ROOT/05-workflow/scripts"
PACK="$ROOT/05-workflow/ep06/6-1a_跳车掀车/上传包_云端"
ARCH="$ROOT/05-workflow/归档素材/人物"
VOICE="$ROOT/05-workflow/归档素材/人物参考音色"

if ! curl -s --max-time 5 http://127.0.0.1:8188/system_stats >/dev/null 2>&1; then
  echo "ABORT: ComfyUI 127.0.0.1:8188 未运行，请用绘世启动器自行启动。" >&2
  exit 9
fi

cd "$SCRIPTS"
python -u run_local_meilin.py \
  --prompt "$SEG/提示词/梅林_S05_v6_瞳孔红_镜头对陆沉.txt" \
  --img1  "$PACK/ep06s01c_garage.png" \
  --img2  "$PACK/ep06s01c_lansun_clean.png" \
  --img3  "$SEG/安娜_凝刃战斗姿态_ref.png" \
  --img4  "$ARCH/陆沉_人设.png" \
  --audio1 "$VOICE/蓝隼.wav" \
  --tag S05_v6_local_meilin \
  --out "$SEG/视频草稿/EP06_S05_v6_本地_瞳孔红_镜头对陆沉.mp4" \
  --no-sync
