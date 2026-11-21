#!/usr/bin/env bash
# EP06 S06 v6｜本地梅林 0.5MP/Spark/DMaD。
# 合并上一轮被打断的三点 + 本轮新反馈（其他不变，含 G29 台词四层锁）：
#   ① 出脚时刀看得见：BLADE LOCK 强化为 PROMINENT / CLEARLY VISIBLE every frame，Shot1-3 写死刀在场
#   ② 刀尖划过子弹时间：Shot3 写死 blade TIP traces a VISIBLE ARC in EXTREME SLOW MOTION
#   ③ 口罩时序：Shots1-3 白色口罩遮嘴 → Shot4 脱身后 PULLS MASK DOWN 再咳嗽（嘴露出）→ Shot5 无口罩露嘴说话
# 台词内容/秒数/双句隔离/闭嘴锁/禁字幕声明原样保留（G29）。
# 图槽映射（--imgN ≠ <Picture N>，G05）：
#   --img1 -> <Picture 2> 车库 ; --img2 -> <Picture 3> 蓝隼
#   --img3 -> <Picture 1> 安娜 ; --img4 -> <Picture 4> 陆沉
# 音频：--audio1 蓝隼(S1) / --audio2 安娜(S2)；台词写回 <d> 仅音频不渲染字幕。
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
  --prompt "$SEG/提示词/梅林_S06_v6_刀刃可见_摘口罩咳嗽_无口罩说话.txt" \
  --img1  "$PACK/ep06s01c_garage.png" \
  --img2  "$PACK/ep06s01c_lansun_clean.png" \
  --img3  "$SEG/安娜_凝刃战斗姿态_ref.png" \
  --img4  "$ARCH/陆沉_人设.png" \
  --audio1 "$VOICE/蓝隼.wav" \
  --audio2 "$VOICE/安娜.wav" \
  --tag S06_v6_local_meilin \
  --out "$SEG/视频草稿/EP06_S06_v6_本地_刀刃可见_摘口罩咳嗽_无口罩说话.mp4" \
  --no-sync
