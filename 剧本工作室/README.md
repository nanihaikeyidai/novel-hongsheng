# 《红绳》剧本工作室（ep06 起）

从第 6 集起的**唯一剧本维护入口**。不改动 `02-manuscript/screenplays` 与 `05-workflow` 里已有成片材料。

## 目录

```
剧本工作室/
  README.md
  项目.md              # 设定 + 事实/假设 + 分集总纲（一个文件）
  episodes/
    ep06.md            # 地下车库（蓝隼战）
    ep07.md            # 陆沉回社
  preview/
    core.py            # 唯一写入通道：解析 / 编辑 / 校验 / 备份 / 落盘
    server.py          # HTTP 服务：网页端走这条通道
    cli.py             # 命令行：Agent 走这条通道
    index.html         # 可交互预览 + 在线编辑（内嵌 episodes 数据）
    sync.py            # 刷新 index.html 的内嵌数据
    tests.py           # 测试套件（64 项：core / cli / web 端到端）
    CONTRACT.md        # 三方共同遵守的接口契约
    AGENT.md           # Agent 操作手册
    .backups/          # 保存前的自动备份（不入库）
```

## 两条维护路径，同一个内核

```
episodes/epXX.md          ← 唯一真相源
        ↑ core.py          ← 唯一写入通道
        ↑                    server.py（网页）    cli.py（Agent）
```

网页和命令行都只调 `core.py`，不各自实现写入逻辑。**不要手改 `episodes/*.md`**——手改不会经过备份与完整性闸门。

## 网页在线编辑

静态页用 `file://` 打开时浏览器没有写文件权限，所以要起本地服务：

```bash
cd D:/HermesWorkspace/ai小说/红绳/剧本工作室
python preview/server.py            # 默认 http://127.0.0.1:8765，会自动开浏览器
python preview/server.py --port 9000 --no-open
```

打开页面后：

1. 侧栏点「**进入编辑**」。
2. 可直接点击修改：**台词、说话人、△ 动作、表演附注、场次标题、frontmatter（状态/标题/更新日期）**。
3. 每场末尾有「**＋动作**」「**＋台词**」可插入新行；每行有「删除」按钮。
4. 点「**保存到文档**」→ 弹出**保存前 diff 预览** → 确认后写回 `episodes/epXX.md`。
5. 点「**撤销本次改动**」可丢弃未保存的编辑；「**重新载入**」从磁盘重读。

### 前端怎么参与写入

前端**不再自己拼 markdown**（这是旧实现最大的风险源——DOM 拼回来的内容和原文对不上，
于是出过「附注整段丢失」「删除按钮把没点的行也删了」「台词说话人被覆盖」这些事故）。

现在前端只做两件事：

1. 读出「用户改了哪些块」，转成一组**结构化 ops**；
2. `POST /api/save` 把 ops 交给服务端，由 `core.py` 统一落盘。

落盘、备份、CRLF 保留、完整性闸门全部在 `core.py` 里，网页与命令行共用同一条通道。
前端只保留一个极轻的本地检查：**ops 的行区间不能互相重叠**——真正的完整性判定在服务端，
服务端拒绝时页面直接把原因显示出来（前端不重复判定，也不自造闸门）。

发出的 op 长这样：

```json
{"op": "replace_block", "lineStart": 125, "lineEnd": 125, "type": "dialogue", "who": "陆沉", "text": "我来帮你啊！"}
{"op": "replace_line",   "line": 5, "text": "status: 草稿"}
{"op": "delete_block",   "lineStart": 87, "lineEnd": 87}
{"op": "insert_after",   "line": 100, "text": "△安娜回头。"}
```

字段口径见 `preview/CONTRACT.md`（第 2 节 core API、第 3 节 ops 协议、第 4 节 HTTP API）。

### 编辑时的小约束

- 附注的**标题行 `【表演附注 X】` 不进编辑区**，只改正文；服务端按原文保留标题行，
  所以改附注不会把标题吃掉。
- **场次号固定**（标题里 `6-1a` 不可改），因为附注标题依赖它；只改场次标题的文字部分。
- 附注正文每行必须以 `- ` 开头（缺了会自动补上）。
- 插入的台词要写成「角色：台词」，插入的动作行会自动补 `△` 前缀。

要点：

- 保存前自动备份旧版到 `preview/.backups/epXX.<时间戳>.md`。
- 写回保留原文件 CRLF 换行，git diff 只会显示真正改动的那几行。
- 编辑态下角色过滤与搜索会置灰——否则被隐藏的块改不到。
- 改过的块有左侧色条标记；保存成功后自动清掉。
- 页面在 `file://` 下打开是**只读**的（侧栏会提示如何启动服务）。
- 未保存就关页面会弹提醒。

## Agent 命令行

给 AI Agent 用的入口，详见 `preview/AGENT.md`：

```bash
cd D:/HermesWorkspace/ai小说/红绳/剧本工作室

python preview/cli.py list                      # 有哪些集
python preview/cli.py parse ep06 --json         # 场次/块/行号（机器可读）
python preview/cli.py show ep06 --scene 6-1b    # 看某一场
python preview/cli.py set ep06 --block 125:125 --type dialogue --text "我来帮你啊！"
python preview/cli.py ins ep06 --after 125 --text "△新动作"
python preview/cli.py del ep06 --block 125:125
python preview/cli.py replace ep06 --find "旧台词" --replace "新台词"
python preview/cli.py meta ep06 --set status=草稿
python preview/cli.py diff ep06                 # 与 git HEAD 比
python preview/cli.py check ep06                # 完整性自检（不落盘）
```

`--json` 放子命令前后都行，长文本可用 stdin 管道传入。

## 安全网

- **备份**：每次落盘前自动备份到 `preview/.backups/`。
- **完整性闸门**（前后端双保险）：写回内容若比原文少出「本次主动删除量」以外的台词行/动作行/附注段，一律拒绝写入，文件不动。网页与命令行都受这条保护。
- **CRLF**：写入保留原文件换行风格，git diff 干净。

## 测试

```bash
python preview/tests.py            # 全部
python preview/tests.py core       # 只跑 core / cli / web
```

测试在临时目录的副本上跑，不碰仓库里的真实剧本；结束时会校验真实文件未被改动。

## 手动改一集

确实需要手改时：

1. 只改 `episodes/epXX.md`（豆包格式：场次表头 / △ / 角色：台词 / 【表演附注】）。
2. 事实/集号/能力口径先改 `项目.md`。
3. 跑：`python preview/sync.py`。

版本用 git 或文件内「修订记录」；不要另存 `_r1` 副本，除非明确要归档。不要另增大纲 JSON。

## 命名

- 集文件：`ep06.md`、`ep07.md`…
- 场次表头：`### 6-1a 地下车库 夜 内`（同场分段用 a/b）
- 动作行：`△` 开头；台词行：`角色名：台词`；附注块：`【表演附注 6-1a】` + 每行 `- ` 开头
- 旧 screenplays（ep01–05）只作历史参考，本工作室不覆盖。
