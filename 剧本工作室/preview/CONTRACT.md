# preview 工具架构契约（实现前必读）

> 本文件是 Web 前端、`server.py`、`cli.py` 三方共同遵守的唯一约定。
> 任何一方改动接口，必须同步改本文件。

## 1. 分层

```
episodes/epXX.md          ← 唯一真相源（磁盘上的 markdown）
        ↑ core.py          ← 唯一写入通道：解析 / 编辑 / 校验 / 备份 / 落盘
        ↑                    server.py（HTTP，供 Web）   cli.py（命令行，供 Agent）
                              两者都只调 core.py 的 API，不得各自实现写入逻辑
```

**硬规则**：JS 里**不得**再出现「把 DOM 拼回 markdown」的逻辑。
前端只负责：读出用户改了哪些块 → 转成结构化 ops → POST 给 server → server 调 core 落盘。

## 2. core.py 对外 API

```python
# preview/core.py

ROOT: Path            # 剧本工作室根
EP_DIR: Path          # ROOT/"episodes"
INDEX: Path           # ROOT/"preview/index.html"
BACKUP_DIR: Path      # ROOT/"preview/.backups"

def list_episodes() -> list[dict]
    """返回 [{id, meta: {...}, markdown: str}, ...]，按 id 排序。meta 含 id/title/status/updated。"""

def parse_episode(md: str) -> dict
    """
    解析一集 markdown，返回:
    {
      "meta": {str: str},          # frontmatter 键值
      "scenes": [
        {
          "id": "6-1a",           # 场次号（含字母后缀）
          "heading": "6-1a 地下车库 夜 内",
          "titleLine": "地下车库 夜 内",
          "lineStart": int,        # ### 标题所在行（0 基，绝对行号）
          "lineEnd": int,          # 场次正文结束行（含）
          "characters": [str],     # 人物行
          "blocks": [
            {"type": "action"|"dialogue"|"note"|"beat",
             "who": str,            # 仅 dialogue
             "text": str,           # 去掉 △ / 说话人前缀后的正文；note 为整段内容
             "lineStart": int, "lineEnd": int,   # 该块覆盖的原文行区间
             "prefix": str}        # 仅 dialogue：原文里的分隔符（如 "："）
          ]
        }
      ],
      "sceneTable": [[str]],       # 分场表行
      "lines": [str],              # 全文按行切分（不含换行符）
      "eol": "\r\n" | "\n",
    }
    """

def apply_ops(md: str, ops: list[dict]) -> tuple[str, dict]
    """
    把一组操作应用到 markdown，返回 (新 markdown, 变更摘要)。
    ops 见第 3 节。摘要形如 {"changed": 3, "deleted": 0, "note": "..."}。
    必须是纯函数：同样的 md + ops → 同样的结果。
    """

def check_integrity(old: str, new: str, deleted: dict | None = None) -> list[str]
    """完整性校验，返回问题列表（空 = 通过）。deleted = {"lines": int, "notes": int}。"""

def save_episode(ep_id: str, markdown: str, deleted: dict | None = None) -> dict
    """落盘。内部：校验 → 备份 → 保留 CRLF 写入 → 刷新内嵌。返回 {"path": str}。
    校验不通过抛 ValueError，消息含 "拒绝写入"。"""

def diff_lines(old: str, new: str) -> list[dict]
    """逐行 diff，返回 [{op: "same"|"del"|"add", old: str|None, new: str|None, line: int}]。"""
```

## 3. 操作（ops）协议

前端与 CLI 都用这套结构描述「要改什么」。**行号一律是 0 基绝对行号**，指向**原文**的 md。

| op | 字段 | 语义 |
|---|---|---|
| `replace_block` | `lineStart`, `lineEnd`, `type`, `text` | 替换整块内容。`type` ∈ action/dialogue/note/beat。`text` 是**去掉 △ 或「说话人：」前缀后的正文**；note 的 text 是**整段附注内容（每行以 "- " 开头）**。行数必须与原块一致（多退少补由 core 处理）。 |
| `replace_line` | `line`, `text` | 替换单行原文（用于人物行、场次标题行、frontmatter 行）。`text` 为该行完整内容。 |
| `delete_block` | `lineStart`, `lineEnd` | 删除整块。 |
| `insert_after` | `line`, `text` | 在 `line` 之后插入一行完整原文（如 `△新的动作` 或 `角色：台词`）。 |

**不变量**：
- 一个 op 不得跨越其它 op 的行区间；重叠即报错。
- 所有 op 一次性应用，不允许「基于上一次结果再改」。

## 4. HTTP API（server.py）

### GET /api/episodes
```json
{ "episodes": [ {"id": "ep06", "meta": {...}, "markdown": "..."} ] }
```

### GET /api/parse?id=ep06
```json
{ "id": "ep06", "meta": {...}, "parsed": { /* core.parse_episode 的返回 */ } }
```
前端渲染用这个（带行号与块结构），不要自己解析。

### POST /api/save
请求：
```json
{ "id": "ep06", "ops": [ ...ops... ], "deleted": {"lines": 0, "notes": 0} }
```
- `deleted` 是**本次主动删除**的行数与附注段数，供完整性闸门放行。
- 服务端：解析 ops → apply_ops → check_integrity → save_episode → 重跑 sync。
- 成功：`200 {"ok": true, "id": "ep06", "episodes": [...], "diff": [...]}`（`diff` 用 core.diff_lines 算，供前端展示）
- 校验不通过：`400 {"error": "拒绝写入，完整性校验未通过：..."}`
- ops 非法：`400 {"error": "..."}`

### GET /api/diff?id=ep06
返回当前磁盘内容与 git HEAD 的差异（用 core.diff_lines 对比 git show 的版本），供 CLI/前端查改动。

## 5. CLI 协议（cli.py）

所有子命令支持 `--json`（机器可读）与人类可读两种输出。

```
python preview/cli.py list                      # 列出所有集
python preview/cli.py show ep06 [--scene 6-1a] # 打印整集或某场
python preview/cli.py parse ep06                # 输出结构化解析结果（行号、块）
python preview/cli.py set ep06 --block 125:127 --type dialogue --text "我来帮你。"
python preview/cli.py set ep06 --line 130 --text "△安娜头也不回。"
python preview/cli.py del ep06 --block 125:127
python preview/cli.py ins ep06 --after 125 --text "△新动作"
python preview/cli.py replace ep06 --find "我来帮你。" --replace "我来帮你啊！"
python preview/cli.py meta ep06 --set status=定稿
python preview/cli.py diff ep06                # 与 git HEAD 比
python preview/cli.py check ep06               # 完整性自检（不落盘）
```

- `set --block A:B` 的 `--text` 是**正文**（不含 △ 与「说话人：」），由 core 按 type 补前缀。
- `replace --find/--replace` 做全文精确替换（可跨行），命中多处在输出里逐条列出。
- 所有写操作走 core.save_episode，带备份与完整性闸门。

## 6. 完整性与备份

- 落盘前 `check_integrity`：新内容的台词行/动作行/附注段数量，不得比原文少出「本次主动删除量」以外的量。
- 落盘前自动备份到 `preview/.backups/epXX.<YYYYmmdd-HHMMSS>.md`。
- 写入保留原文件换行风格（CRLF 文件继续用 CRLF），避免 git 视整个文件全改。
- 写完自动 `sync.main()` 刷新 index.html 内嵌数据。

## 7. 命名与格式约定（剧本侧，不得擅自更改）

- 场次表头：`### 6-1a 地下车库 夜 内`（同场分段用 a/b/c…）
- 动作行：`△` 开头
- 台词行：`角色名：台词`
- 附注块：`【表演附注 6-1a】` 起头，内容每行 `- ` 开头
- frontmatter 用 ```yaml 包裹
- 文件编码 UTF-8，Windows 下为 CRLF

## 8. 测试要求

实现完成后必须跑通（用真实 ep06/ep07，不破坏原文件）：

1. 改一句台词 → git diff 只该行变化
2. 改一个动作行 → 同上
3. 改一段附注 → 同上
4. 删一个块 → 精确对应行数
5. 插入一个动作行 → 精确 +1
6. 改 frontmatter → 只有 frontmatter 行变化
7. 截断内容 → 被拒，文件不动
8. CLI 与 Web 改同一集，结果一致
9. 全程无控制台错误
