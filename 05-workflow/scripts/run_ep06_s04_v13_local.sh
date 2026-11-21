#!/usr/bin/env bash
# EP06 S04 v13 本地梅林出片（同一份 v13 提示词，走本地 0.5MP/Spark/DMaD）。
#
# 前提：用户已用整合包启动器启动 ComfyUI（127.0.0.1:8188）。本脚本绝不后台拉起 ComfyUI。
# 图槽映射（本地 --imgN 与 <Picture N> 不同号，G05）：
#   --img1 -> 节点49  -> <Picture 2> 车库
#   --img2 -> 节点50  -> <Picture 3> 蓝隼
#   --img3 -> 节点51  -> <Picture 1> 安娜
#   --img4 -> 节点520 -> <Picture 4> 陆沉
# 音频：<Audio 1> 蓝隼音色（锁中文台词/音色，压日语乱码）；本地音轨模型自生成=原生音轨，不做后期配音。
# 提示词 4853 字符，与 v9b 成功版 4925 字符同量级（G08 预算内）。
set -euo pipefail
ROOT="/d/HermesWorkspace/ai小说/红绳"
SEG="$ROOT/05-workflow/ep06/全本批量_梅林"
SCRIPTS="$ROOT/05-workflow/scripts"
PACK="$ROOT/05-workflow/ep06/6-1a_跳车掀车/上传包_云端"
ARCH="$ROOT/05-workflow/归档素材/人物"
VOICE="$ROOT/05-workflow/归档素材/人物参考音色"

# 启动前探针：ComfyUI 不在就明确退出，绝不自动启动。
if ! curl -s --max-time 5 http://127.0.0.1:8188/system_stats >/dev/null 2>&1; then
  echo "ABORT: ComfyUI 127.0.0.1:8188 未运行。请用整合包启动器自行启动后重跑本脚本。" >&2
  exit 9
fi

cd "$SCRIPTS"
python -u run_local_meilin.py \
  --prompt "$SEG/提示词/金鱼_S04_v13_朝蓝隼出拳_单腿踢_原声.txt" \
  --img1  "$PACK/ep06s01c_garage.png" \
  --img2  "$PACK/ep06s01c_lansun_clean.png" \
  --img3  "$SEG/安娜_凝刃战斗姿态_ref.png" \
  --img4  "$ARCH/陆沉_人设.png" \
  --audio1 "$VOICE/蓝隼.wav" \
  --tag S04_v13_local_meilin \
  --out "$SEG/视频草稿/EP06_S04_v13_本地_朝蓝隼出拳单腿踢.mp4" \
  --no-sync
