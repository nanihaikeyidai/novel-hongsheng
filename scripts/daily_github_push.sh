#!/bin/bash
# 红绳仓库每日 GitHub 同步脚本
# 触发：每晚 0 点由 automation 调用
#
# 规则（用户 2026-11-19 拍板）：
#   1. 提交范围完全沿用仓库现有 .gitignore（不新增过滤规则）
#   2. 远程有新提交时先 git pull --rebase 合并，再 push；绝不 force push
#   3. rebase 冲突 -> 立即 abort 并退出，本次不推送，留待人工处理
#   4. 无本地改动 -> 跳过 commit，仍尝试 push（幂等）
#
# 日志：D:/HermesWorkspace/_hongsheng_sync_logs/YYYYMMDD_HHMMSS.log（仓库外，不污染提交）

set -euo pipefail

REPO="D:/HermesWorkspace/ai小说/红绳"
LOG_DIR="D:/HermesWorkspace/_hongsheng_sync_logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/$(date +%Y%m%d_%H%M%S).log"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

cd "$REPO" || { log "ERR 无法进入仓库 $REPO"; exit 1; }

BRANCH=$(git rev-parse --abbrev-ref HEAD)
log "=== 每日同步开始 | 分支: $BRANCH ==="

log "[1/5] fetch origin"
if ! git fetch origin 2>&1 | tee -a "$LOG"; then
  log "ERR fetch 失败，终止（不提交不推送）"
  exit 1
fi

log "[2/5] git add -A（沿用现有 .gitignore）"
git add -A

if git diff --cached --quiet; then
  log "      无本地改动，跳过 commit"
else
  CNT=$(git diff --cached --name-only | wc -l | tr -d ' ')
  log "      暂存 $CNT 个文件，commit 中..."
  if ! git commit -m "chore: 每日定时同步 $(date '+%Y-%m-%d %H:%M')" 2>&1 | tee -a "$LOG"; then
    log "ERR commit 失败，终止"
    exit 1
  fi
fi

AB=$(git rev-list --left-right --count "origin/$BRANCH...$BRANCH")
BEHIND=$(echo "$AB" | awk '{print $1}')
AHEAD=$(echo "$AB" | awk '{print $2}')
log "[3/5] 与远程差异: behind=$BEHIND ahead=$AHEAD"

if [ "$BEHIND" -gt 0 ]; then
  log "[4/5] 远程有 $BEHIND 个新提交，pull --rebase"
  if ! git pull --rebase origin "$BRANCH" 2>&1 | tee -a "$LOG"; then
    log "ERR rebase 冲突，已 abort；本次不推送，请人工处理"
    git rebase --abort 2>/dev/null || true
    exit 2
  fi
else
  log "[4/5] 本地领先或与远程一致，无需 rebase"
fi

log "[5/5] push origin $BRANCH"
if ! git push origin "$BRANCH" 2>&1 | tee -a "$LOG"; then
  log "ERR push 失败（下次运行会重试）"
  exit 3
fi

log "=== 每日同步完成 ==="
