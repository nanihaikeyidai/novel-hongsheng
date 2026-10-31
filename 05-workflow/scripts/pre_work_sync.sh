#!/usr/bin/env bash
# 开工前置同步（统一入口）—— 每次开始制作前第一条命令。
#
# 规则（用户 2026-10-31 明确要求）：**每次制作时都固定先拉一下云端的代码**。
#
# 覆盖三个仓库：
#   1. 红绳项目       D:/HermesWorkspace/ai小说/红绳          (git@github.com:nanihaikeyidai/novel-hongsheng.git)
#   2. directorMaster D:/HermesWorkspace/directorMaster       (git@github.com:nanihaikeyidai/directorMaster.git)
#   3. ComfyUI 内核   F:/Work-Fisher纯净包2026.8.7/ComfyUI     (gh-proxy → github.com/comfyanonymous/ComfyUI)
#
# 用法:
#   bash 05-workflow/scripts/pre_work_sync.sh            # 全量同步
#   bash 05-workflow/scripts/pre_work_sync.sh --dry-run  # 只看状态，不改任何东西
#   bash 05-workflow/scripts/pre_work_sync.sh --only code  # 只同步项目代码，跳过 ComfyUI 内核
#
# 安全约束:
#   - 绝不丢弃已跟踪文件的本地改动（不 checkout / 不 reset / 不 stash）
#   - 未跟踪文件与远程新增同路径时：先备份到仓库外，再移走；备份失败立即中止该仓库
#   - ComfyUI 内核只允许 fast-forward；非 ff 需人工介入
#   - ComfyUI 升版本后必须复查 comfy-kitchen 是否还带 Spark 定制版

set -uo pipefail

DRY=0
ONLY=""
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --only)   ONLY="code" ;;
    --only=*) ONLY="${a#--only=}" ;;
  esac
done

HONG="/d/HermesWorkspace/ai小说/红绳"
DM="/d/HermesWorkspace/directorMaster"
COMFY="/f/Work-Fisher纯净包2026.8.7/ComfyUI"

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_ROOT="/d/HermesWorkspace/_git_untracked_backup_${STAMP}"
FAILED=0

echo "=================================================="
echo " 红绳 · 开工前置同步   $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="

sync_repo() {
  # $1=路径 $2=显示名 $3=是否允许 ff-only(1/0) $4=remote名(默认 origin)
  local repo="$1" name="$2" ffonly="$3" remote="${4:-origin}"
  echo
  echo "--------------------------------------------------"
  echo "【$name】 $repo"
  echo "--------------------------------------------------"

  if [ ! -d "$repo/.git" ]; then
    echo "  跳过：不是 git 仓库"
    return 0
  fi

  cd "$repo" || { echo "  跳过：无法进入目录"; return 0; }

  # remote 存在性检查
  if ! git remote get-url "$remote" >/dev/null 2>&1; then
    echo "  ⚠️ remote '$remote' 不存在，跳过"
    git remote -v | sed 's/^/    /'
    return 0
  fi

  local branch
  branch="$(git branch --show-current)"
  if [ -z "$branch" ]; then
    echo "  ⚠️ detached HEAD，跳过（不自动切分支）"
    return 0
  fi
  local local_branch="$branch"
  echo "  分支: $local_branch   remote: $remote"

  echo "  -- fetch --"
  # 注意：不要把 fetch 放进带 grep 的管道，管道退出码会取自 grep 导致误判失败
  local fetch_out
  fetch_out="$(git fetch "$remote" --prune 2>&1)"
  local fetch_rc=$?
  echo "$fetch_out" | tail -2 | grep -vE '^\s*$' | sed 's/^/    /'
  if [ "$fetch_rc" -ne 0 ]; then
    echo "  ⚠️ fetch 失败（网络？）跳过该仓库"
    return 0
  fi

  # upstream 分支名可能与本地分支名不同（如 local/v0.42-track -> release/v0.42）
  local upstream_branch
  upstream_branch="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)"
  if [ -n "$upstream_branch" ]; then
    # upstream 形如 ghproxy/release/v0.42 -> remote=ghproxy, branch=release/v0.42
    local up_remote up_branch
    up_remote="${upstream_branch%%/*}"
    up_branch="${upstream_branch#*/}"
    if git remote get-url "$up_remote" >/dev/null 2>&1; then
      remote="$up_remote"
      branch="$up_branch"
    fi
  fi
  echo "  实际对比: ${remote}/${branch}"

  # 确认 remote-tracking ref 存在
  local remote_ref="refs/remotes/${remote}/${branch}"
  if ! git rev-parse --verify "$remote_ref" >/dev/null 2>&1; then
    echo "  ⚠️ 无法取得 ${remote}/${branch}，跳过该仓库"
    git branch -r 2>/dev/null | head -5 | sed 's/^/    /'
    return 0
  fi

  local behind ahead
  behind="$(git rev-list --count "HEAD..${remote}/${branch}" 2>/dev/null || echo 0)"
  ahead="$(git rev-list --count "${remote}/${branch}..HEAD" 2>/dev/null || echo 0)"
  echo "  落后远程 ${behind} 个提交 | 本地未推送 ${ahead} 个提交"

  if [ "$behind" -eq 0 ]; then
    echo "  ✅ 已是最新"
    return 0
  fi

  echo "  -- 远程新提交 --"
  git log --oneline "HEAD..${remote}/${branch}" | head -15 | sed 's/^/    /'

  # 检测未跟踪文件冲突
  local tmp
  tmp="$(mktemp)"
  git diff --name-only --diff-filter=A "HEAD" "${remote}/${branch}" > "$tmp"
  local n=0
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    if [ -e "$f" ] && [ -n "$(git ls-files --others --exclude-standard -- "$f")" ]; then
      echo "  ⚠️ 未跟踪文件冲突: $f"
      n=$((n + 1))
    fi
  done < "$tmp"

  if [ "$DRY" -eq 1 ]; then
    echo "  [dry-run] 冲突 $n 个，未做任何改动"
    rm -f "$tmp"
    return 0
  fi

  # 备份并移走冲突的未跟踪文件
  if [ "$n" -gt 0 ]; then
    echo "  -- 备份 $n 个冲突文件到 $BACKUP_ROOT --"
    if ! mkdir -p "$BACKUP_ROOT/$name"; then
      echo "  ❌ 备份目录创建失败，中止该仓库"
      rm -f "$tmp"; FAILED=1; return 0
    fi
    while IFS= read -r f; do
      [ -z "$f" ] && continue
      if [ -e "$f" ] && [ -n "$(git ls-files --others --exclude-standard -- "$f")" ]; then
        mkdir -p "$BACKUP_ROOT/$name/$(dirname "$f")"
        if ! cp -p "$f" "$BACKUP_ROOT/$name/$f"; then
          echo "  ❌ 备份失败: $f —— 中止该仓库，不做任何改动"
          rm -f "$tmp"; FAILED=1; return 0
        fi
        if [ ! -s "$BACKUP_ROOT/$name/$f" ]; then
          echo "  ❌ 备份校验失败: $f —— 中止该仓库"
          rm -f "$tmp"; FAILED=1; return 0
        fi
        rm -f "$f"
      fi
    done < "$tmp"
    echo "  ✅ 备份完成: $(find "$BACKUP_ROOT/$name" -type f 2>/dev/null | wc -l) 个文件"
  fi
  rm -f "$tmp"

  echo "  -- pull --"
  if [ "$ffonly" -eq 1 ]; then
    git pull --ff-only "$remote" "${branch}" 2>&1 | tail -8 | sed 's/^/    /'
  else
    git pull --no-rebase "$remote" "${branch}" 2>&1 | tail -8 | sed 's/^/    /'
  fi
  # 上游分支名可能与本地分支名不同，用 upstream ref 复查
  local up_ref="${remote}/${branch}"

  local newbehind
  newbehind="$(git rev-list --count "HEAD..${remote}/${branch}" 2>/dev/null || echo 0)"
  if [ "$newbehind" -eq 0 ]; then
    echo "  ✅ 已同步到最新 ($(git rev-parse --short HEAD))"
  else
    echo "  ⚠️ 仍有 $newbehind 个提交未同步，需人工处理"
    FAILED=1
  fi

  # 本地已跟踪文件的改动必须原样保留
  local dirty
  dirty="$(git status --porcelain | grep -v '^??' | wc -l)"
  echo "  本地已跟踪文件改动仍保留: $dirty 项"
  return 0
}

# ---------- 1. 红绳项目 ----------
sync_repo "$HONG" "红绳项目" 0

# ---------- 2. directorMaster ----------
sync_repo "$DM" "directorMaster" 1

# ---------- 3. ComfyUI 内核 ----------
if [ "$ONLY" != "code" ]; then
  sync_repo "$COMFY" "ComfyUI内核" 1 ghproxy

  if [ "$DRY" -eq 0 ] && [ -d "$COMFY/.git" ]; then
    cd "$COMFY" || exit 0
    echo
    echo "  -- ComfyUI 版本 & Spark 复查 --"
    echo "    HEAD      : $(git rev-parse --short HEAD) $(git log -1 --format=%s)"
    echo "    版本文件  : $(grep -oE '__version__ = .*' "$COMFY/comfyui_version.py" 2>/dev/null | tail -1)"
    if [ -x "$COMFY/../python/python.exe" ]; then
      PY="$COMFY/../python/python.exe"
      "$PY" - <<'PYEOF' 2>/dev/null | sed 's/^/    /'
import importlib.metadata as md
try:
    print("comfy-kitchen:", md.version('comfy-kitchen'))
except Exception as e:
    print("comfy-kitchen: 读取失败", e)
try:
    from comfy_kitchen.backends.cuda import spark_attn
    print("Spark SM89   : ✅ 在位")
except Exception:
    print("Spark SM89   : ❌ 缺失 —— 需装 Spark-H3 定制版，否则 H3 渲染会崩")
PYEOF
    fi
    echo "    提示：若 kitchen 被升到无 Spark 的官方版，请从"
    echo "           F:/h3tmp/spark015/ComfyUI-Spark-H3/wheelhouse/ 重装定制 wheel"
  fi
fi

echo
echo "=================================================="
if [ "$FAILED" -eq 0 ]; then
  echo " ✅ 同步完成，可以开工"
else
  echo " ⚠️ 部分仓库未完全同步（见上），开工前请人工确认"
fi
[ -d "$BACKUP_ROOT" ] && echo " 本地旧稿备份目录: $BACKUP_ROOT"
echo "=================================================="
exit $FAILED
