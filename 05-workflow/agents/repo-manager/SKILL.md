---
name: repo-manager
description: 红绳项目 Git 仓库管理 skill。触发词：用户说「提交」「拉代码」「同步代码」，或任何需要 git 提交/推送/拉取的时刻；其它 agent 开始开发前必须先用它拉新代码。职责：开发前 pull --rebase 同步、按项目规范提交并推送 origin main、守护大资产出库规则。不用于建分支、发 Release 或重写历史（那些需用户明确单独要求）。
---

# Repo Manager（红绳仓库管理）

仓库：`nanihaikeyidai/novel-hongsheng`（origin/main 为唯一主线）。
仓库原则：**只入库生视频必需的 人设图（含怪物）/场景图/参考音色 + 全部文档/剧本/提示词/脚本/Skill**。分镜线稿、首帧图、成片 mp4、BGM mp3、pv 素材等大资产**一律不入库**（文件保留在本地磁盘）。

## 铁律

1. **禁止 force-push**，除非用户明确要求重写历史（历史上 2026-10-24 做过一次 904MB→200MB 的瘦身，见 AGENTS.md）。
2. **大资产出库守护**：提交前扫描暂存区，任何单个文件 >20MB 或扩展名属于 `mp4/mov/mkv/mp3/zip/jpg`（人物图 jpg 除外）→ 停止并报告用户，不得入库。`.gitignore` 已配置规则，正常 `git add -A` 会自动排除。
3. **提交信息规范**：中文 conventional commits，格式见 §提交流程。
4. **仓库健康**：若发现 `refs/codex/*` 引用或 pack 超过 300MB，按 AGENTS.md「2026-10-24 目录清理说明」执行清理（删 ref + `git gc --prune=now`），并报告用户。
5. 业务冲突（剧本/提示词内容冲突）不擅自解决，报告用户决定。

## 双端开发同步（本地 ↔ GitHub ↔ 云端）

GitHub origin/main 是唯一同步中枢。本地电脑和云端 bot（使用 RunningHub 生成）都可能开发，规则：

1. **任何一端开始开发前，必须先拉取**：`git fetch origin && git pull --rebase origin main`——把另一端推送的新代码/素材/文档拉下来，禁止基于旧代码开发。
2. **任何一端开发完成，必须推送**：按 §提交流程 commit + push，让另一端下次拉取时拿到最新成果。
3. **本地离线时**：云端 bot 独立开发并推送到 GitHub；本地恢复在线后第一件事执行 §拉取流程 同步云端成果，再继续本地开发。
4. **冲突原则**：双端同时改同一文件产生 rebase 冲突时，以内容较新、信息较完整的版本为基础，但剧本/提示词等业务内容冲突必须报告用户裁决。
5. **环境差异记录**：云端 RunningHub 产物（工作流 JSON、跑批结果、提示词）入库；本地专属产物（本地渲染视频等大资产）不出库，仅在本地磁盘，并按需更新 AGENTS.md 说明。
6. **大资产规则两端一致**：无论哪端开发，`*.mp4/*.mp3/*.zip/*.jpg`（人物图除外）及非人物/场景 png 都不入库（.gitignore 两端共用）。

## 拉取流程（每次开发开始，必做）

用户说「拉代码」「同步」「开始开发」，或任何 agent 接手开发前：

1. `git -c core.quotepath=false status --porcelain` 检查本地未提交改动。
2. 有改动 → 先询问用户：提交后再拉，还是 stash。
3. `git fetch origin && git pull --rebase origin main`。
4. rebase 冲突 → 列出冲突文件，等待用户决定；工程性冲突（.gitignore/AGENTS.md）可自行合并后说明。
5. 汇报：当前 HEAD hash、拉到的新提交列表。

## 提交流程（用户说「提交」时执行）

1. **先拉后推**：`git fetch origin && git pull --rebase origin main`。
2. **变更盘点**：`git -c core.quotepath=false status --short`，按 A/M/D/?? 分类统计。
3. **大文件扫描**：`git diff --cached --stat` 及暂存区逐一检查 >20MB 文件 → 命中铁律 2 则中止。
4. **暂存**：`git add -A`（.gitignore 自动排除出库资产）。
5. **提交信息**（中文 conventional commits）：

   ```
   type: 一行中文摘要

   - 要点 1
   - 要点 2
   ```

   type 取值：`feat`（新剧本/素材/功能）、`docs`（文档/规范）、`fix`（修复）、`chore`（工程整理）、`refactor`（重构）。

6. **推送**：`git push origin main`。
7. **汇报**：commit hash、`--stat` 变更统计（N files, +X/-Y）、推送结果、是否触发大资产拦截。

## 常用命令速查

```bash
# 状态（中文路径可读）
git -c core.quotepath=false status --short
# 大文件检查（暂存前）
git ls-files -s | awk '{print $4}' | xargs -I{} du -m "{}" 2>/dev/null | awk '$1>20 {print "LARGE:", $1"MB", $2}'
# 仓库体积
git count-objects -vH | grep size-pack
```
