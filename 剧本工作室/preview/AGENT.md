# Agent 操作手册 · 剧本工作室

> 给 AI Agent 看的：如何在不打开浏览器的情况下，用命令行安全地维护《红绳》剧本。
> 所有写操作都走 `preview/core.py` 唯一通道，自带备份与完整性闸门。

## 0. 前提

```bash
cd D:/HermesWorkspace/ai小说/红绳/剧本工作室
```

剧本正文在 `episodes/epXX.md`，那是唯一真相源。**不要绕过 CLI 手改文件**——手改不会经过备份与闸门。

## 1. 先摸清现状

```bash
python preview/cli.py list              # 有哪些集
python preview/cli.py show ep06         # 看整集（人读）
python preview/cli.py parse ep06 --json # 结构化：场次、块、行号
```

`parse --json` 的结构：

```jsonc
{
  "ok": true,
  "id": "ep06",
  "meta": { "status": "定稿", "updated": "2026-11-07", ... },
  "parsed": {
    "scenes": [
      {
        "id": "6-1b",                 // 场次号（带字母后缀）
        "titleLine": "地下车库 夜 内",
        "lineStart": 111,             // ### 标题行号（0 基）
        "characters": ["安娜","陆沉","蓝隼"],
        "blocks": [
          { "type": "action",   "text": "……", "lineStart": 115, "lineEnd": 115 },
          { "type": "dialogue", "who": "安娜", "text": "快跑，我拖住他。",
            "lineStart": 121, "lineEnd": 121 },
          { "type": "note",     "text": "- 节拍：…\n- 情绪线：…",
            "lineStart": 145, "lineEnd": 151 }
        ]
      }
    ]
  }
}
```

**`lineStart` / `lineEnd` 是 0 基绝对行号**，指向原文 md。所有编辑命令都用它定位。

## 2. 改剧本

| 目的 | 命令 | 注意 |
|---|---|---|
| 改一句台词 | `set ep06 --block 125:125 --type dialogue --text "我来帮你啊！"` | `--text` 是**正文**，不含「说话人：」 |
| 改说话人 | 同上，但 `--text` 里给完整正文；说话人由 `--who` 指定（若命令支持） | 先 `parse` 看原 `who` |
| 改一个 △ 动作 | `set ep06 --block 115:115 --type action --text "安娜撑地站起……"` | `--text` 是**正文**，不含 `△` |
| 改整段附注 | `set ep06 --block 145:151 --type note --text "- 节拍：…\n- 情绪线：…"` | 每行必须以 `- ` 开头 |
| 删一个块 | `del ep06 --block 125:125` | |
| 插一行 | `ins ep06 --after 125 --text "△新动作"` | `--text` 是**完整原文行** |
| 全文替换 | `replace ep06 --find "我来帮你。" --replace "我来帮你啊！"` | 命中多处会逐条列出 |
| 改 frontmatter | `meta ep06 --set status=草稿` | |
| 看当前改动 | `diff ep06` | 与 git HEAD 比 |
| 自检 | `check ep06` | 不落盘 |

### 长文本用 stdin（推荐，避免引号转义地狱）

```bash
printf '%s' "新的台词内容" | python preview/cli.py set ep06 --block 125:125 --type dialogue
```

多行附注：

```bash
cat <<'EOF' | python preview/cli.py set ep06 --block 145:151 --type note
- 节拍：新的节拍
- 情绪线：新的情绪线
EOF
```

## 3. 给 Agent 的调用约定

1. **先 parse，再改**。不要凭记忆猜行号——改稿前后的行号会变，永远用当次 `parse` 的结果。
2. **改完立刻 `diff` 确认**。`git diff --numstat` 应该只显示你预期的那几行。
3. **一次只改一个集**。多集并发改会互相覆盖。
4. **闸门拒了就别重试**。输出形如「拒绝写入，完整性校验未通过：台词行少了 N 个」——这说明 ops 区间算错了（比如把附注整段当成一行覆盖），需要重新 parse 拿行号。
5. **保留锁定项**。用户锁定的台词逐字不动，只规范标点。

## 4. 安全网

- 每次落盘前自动备份到 `preview/.backups/epXX.<时间戳>.md`
- 落盘前跑完整性闸门：台词行/动作行/附注段数量不得比原文少出「本次主动删除量」以外的量，超了直接拒绝写入，文件不动
- 写入保留原文件 CRLF 换行，git diff 只显示真正改动的行
- 写完自动重跑 `sync.py` 刷新 `preview/index.html` 的内嵌数据（网页预览立刻可见）

## 5. 机器可读输出

所有命令加 `--json`（放子命令前后都行）：

```bash
python preview/cli.py set ep06 --block 125:125 --type dialogue --text "新台词" --json
```

返回：

```json
{ "ok": true, "id": "ep06", "changed": 2, "diff": [ {"op":"del","line":125,"old":"陆沉：我来帮你。"},
                                                     {"op":"add","line":125,"new":"陆沉：新台词"} ] }
```

失败时 `ok: false` 且带 `error`，退出码非 0。

## 6. 与网页的关系

网页（`preview/server.py`）和 CLI 用的是**同一套 core.py**，所以：

- 网页上改的，CLI 立刻能读到；反之亦然
- 两边的写入都受同一道完整性闸门保护
- 网页开着的时候 CLI 改文件，网页点「重新载入」即可看到
