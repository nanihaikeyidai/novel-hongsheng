#!/usr/bin/env bash
# EP06 S06 v7｜本地梅林 0.5MP/Spark/DMaD。
# 四点改动（其他不变，含 G29 台词四层锁、口罩时序、镜头顺序）：
#   ① 踢出/子弹时间刀保持实体：BLADE LOCK 改 SOLID OPAQUE matte metal + hard edges + dull glint；Avoid 删 glowing blades（A 型负向泄漏）
#   ② 蓝隼躲避改自信：Shot3 GAZE/EXPRESSION LOCK 写 CALM CONFIDENT / FAINT COCKY SMIRK / UNHURRIED，无紧张类否定词（A 型）
#   ③ 说话镜单人正面特写：Shot5 拆 (a)蓝隼 solo frontal (b)安娜 solo 静默 (c)安娜 solo 回复 (d)安娜 solo 特写；ONE person ONLY/NO two-shot/双耳等宽/墨镜等宽（G21）
#   ④ 蓝隼台词改「多年不见，身手变熟练了」10字~1.5s：11.0->12.5；静默 12.5-13.2；安娜 13.2-13.7；尾段 SILENT acting。
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
  --prompt "$SEG/提示词/梅林_S06_v7_刀实体_自信躲避_单人正面特写_新台词.txt" \
  --img1  "$PACK/ep06s01c_garage.png" \
  --img2  "$PACK/ep06s01c_lansun_clean.png" \
  --img3  "$SEG/安娜_凝刃战斗姿态_ref.png" \
  --img4  "$ARCH/陆沉_人设.png" \
  --audio1 "$VOICE/蓝隼.wav" \
  --audio2 "$VOICE/安娜.wav" \
  --tag S06_v7_local_meilin \
  --out "$SEG/视频草稿/EP06_S06_v7_本地_刀实体_自信躲避_单人正面特写.mp4" \
  --no-sync
