#!/usr/bin/env bash
# EP06 S07 v1「飞刀被拍飞」｜本地梅林 0.5MP/Spark/DMaD。
# 按武戏模板 + G29 台词四层锁新写（旧批量版有耳麦/negativePrompt，已清理）。
#   ① 0秒入动作：Shot1 直接甩腕掷三刀，无对峙前摇
#   ② 因果链：掷出→三记不同拍飞→钉车门溃散灰银雾→横移挡位（武戏模板禁重复招式/受力方向）
#   ③ 三记不同：palm edge RAPS up / palm back SWEEPS down-side / fingertips FLICK aside
#   ④ 台词：蓝隼 ONE line 21字~3.0s 8.0->11.0，LIPS LOCK + 尾段 SILENT acting；单人正面特写（G21）
#   ⑤ 陆沉残骸边蜷着捂胸喘气、入画余光不抢戏、CLOSED
# 图槽映射（--imgN ≠ <Picture N>，G05）：
#   --img1 -> <Picture 2> 车库 ; --img2 -> <Picture 3> 蓝隼
#   --img3 -> <Picture 1> 安娜 ; --img4 -> <Picture 4> 陆沉
# 音频：--audio1 蓝隼(S1)；台词写回 <d> 仅音频不渲染字幕。
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
  --prompt "$SEG/提示词/梅林_S07_v1_飞刀被拍飞_武戏模板_G29台词.txt" \
  --img1  "$PACK/ep06s01c_garage.png" \
  --img2  "$PACK/ep06s01c_lansun_clean.png" \
  --img3  "$SEG/安娜_凝刃战斗姿态_ref.png" \
  --img4  "$ARCH/陆沉_人设.png" \
  --audio1 "$VOICE/蓝隼.wav" \
  --tag S07_v1_local_meilin \
  --out "$SEG/视频草稿/EP06_S07_v1_本地_飞刀被拍飞_武戏模板.mp4" \
  --no-sync
