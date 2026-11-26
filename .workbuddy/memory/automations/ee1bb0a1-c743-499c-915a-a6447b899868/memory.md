# 自动化执行记忆：红绳当日改动归档提交推送

## 2026-10-31 23:30
- 触发：每日归档自动化。
- 流程：`git fetch`（落后 6、领先 0）→ `bash 05-workflow/scripts/pre_work_sync.sh --only code`（跳过 ComfyUI 内核，避免无关仓库操作）→ 同步到 b67db15，无未跟踪冲突、无需备份 → `git add -A` → 暂存 64 个文件 → 密钥/体积核查（最大 2.5MB，无明文 key）→ 提交 + 推送。
- 结果：commit `b701876`，push `b67db15..b701876` 成功；之后 origin/main 与 HEAD 一致（0/0）。
- 排除的临时文件（未入库，留工作区）：`05-workflow/ep05/营救陆沉/制作文档/rh_task_status.json`（含本地绝对路径与 stdout tail 的运行态缓存）、`05-workflow/scripts/_poll_ep05_p01.py`（硬编码 taskId 的一次性轮询脚本）。
- 经验：本仓库 `rh_submit_*/timeline_*/rh_result_*.json` 属可追溯的提交/回执凭证，按惯例入库；仅运行态 status 与一次性调试脚本排除。`*.png` 仅 `人物/场景/道具` 目录例外，道具图可正常入库。
- 遗留提醒：`.agents/skills/directorMaster/references/runninghub-guide.md` 曾把旧 API Key（82bc…）明文写进历史提交；本次已改为读环境变量，但历史中的旧 key 仍在 git 历史里，需要时按吊销处理。

## 2026-11-01 23:30
- 触发：每日归档自动化。
- 流程：`git fetch`（落后 1、领先 0）→ `pre_work_sync.sh --only code` ff 合并到 ce6e66b（P09 v11），无未跟踪冲突 → `git add -A` 配合 pathspec 排除 4 项临时产物 → 暂存 43 个文件（最大 20KB，无密钥特征）→ 提交 + 推送。
- 结果：commit `794c9d8`，push `ce6e66b..794c9d8` 成功；origin/main 与 HEAD 0/0。
- 排除项：`.workbuddy/`（agent 本地记忆/自动化状态，不入共享仓库）、`rh_task_status.json`（运行态缓存）、`_poll_ep05_p01.py`（一次性脚本）、`_acl-repair/`（本机 ACL 修复临时产物与备份）。
- 经验：用 `git add -A -- . ':(exclude)<path>'` 一次性排除多路径，比先全量 add 再 reset 更可控；本机 git 会提示 LF→CRLF，属正常无需处理。

## 2026-11-02 23:30
- 触发：每日归档自动化。
- 流程：`git status -sb` + `git fetch origin` → 与 origin/main 0/0 一致，无已跟踪文件改动（`git diff --stat HEAD` 为空）→ 按「无改动不空提交」规则直接结束，未创建 commit。
- 结果：HEAD = origin/main = `794c9d8`（11-01 归档提交），推送无需执行。
- 留在工作区的未跟踪文件（与 11-01 相同，均不入库）：`.workbuddy/`（agent 本地记忆/自动化状态）、`05-workflow/ep05/营救陆沉/制作文档/rh_task_status.json`（运行态缓存）、`05-workflow/scripts/_poll_ep05_p01.py`（一次性脚本）、`_acl-repair/`（本机 ACL 修复临时产物）。

## 2026-11-04 23:30
- 触发：每日归档自动化。
- 流程：fetch 后与 origin/main 0/0 一致（远程今日已有云端推送 0982408，本地无落后）→ 无已跟踪文件改动，仅新增未跟踪文件 → `git add -A` 带 pathspec 排除 `.workbuddy/`、`_acl-repair/`、`_poll_ep05_p01.py` → 暂存 10 文件中发现 `红绳片段14/视频草稿/_baseline_v2_audio.wav`（482KB 生成音频大资产，规范不入库）→ `git rm --cached` 移出 → 密钥扫描（`5724` 命中为节点坐标数字巧合；脚本均走环境变量）→ 提交 9 文件。
- 结果：commit `43594e8`，push `0982408..43594e8` 成功；origin/main 与 HEAD 一致（0/0）。
- 内容：_ripple_doc（H3 Ripple 工作流 JSON×3 + vfx-edit.md）、P14 金鱼 v3 提示词与提交日志、P09 Ripple/V2V 测试脚本、P14 金鱼 v3 跑批脚本。
- 留在工作区（不入库）：`.workbuddy/`、`_acl-repair/`、`_poll_ep05_p01.py`（一次性脚本）、`红绳片段14/视频草稿/`（大资产）、`P14_v3_submit_log.txt`（有任务正在运行，日志持续追加「Waiting for result」，属运行态，待任务结束后次日归档）。

## 2026-11-03 23:30
- 触发：每日归档自动化。
- 流程：`git status -sb` + `git fetch origin`（落后 1、领先 0）→ `pre_work_sync.sh --only code` ff 合并到 f5fa798（云端推送的 docs 更新：视频技巧_David.md）→ `git add -A` 带 pathspec 排除 4 项临时产物后暂存区为空（`git diff --cached --stat` 无内容）→ 无本地改动，按规则不创建空提交、无需推送。
- 结果：HEAD = origin/main = `f5fa798`（0/0 一致）。本地拉取了云端 1 个提交，无本地内容需要归档。
- 留在工作区的未跟踪文件（连续多日相同，均不入库）：`.workbuddy/`、`05-workflow/ep05/营救陆沉/制作文档/rh_task_status.json`（运行态缓存）、`05-workflow/scripts/_poll_ep05_p01.py`（一次性脚本）、`_acl-repair/`（本机临时产物）。

## 2026-11-05 23:30
- 触发：每日归档自动化。
- 流程：fetch 后与 origin/main 0/0 一致（无需合并）→ `git add -A` 带 pathspec 排除（.workbuddy、_acl-repair、_poll_ep05_p01.py、红绳片段14/验收_v3~v7 整目录、红绳片段16/验收 的质检图与 wav、片段16/上传包 的 jpg/wav 派生物）→ 单独补入 验收/make_scene_ref.py → 暂存 47 文件（最大 1.7MB 场景图，属规范允许入库的场景 png）→ 密钥扫描干净（脚本走 os.environ，无硬编码 key）→ 提交 + 推送。
- 结果：commit `788fcc7`，push `43594e8..788fcc7` 成功；origin/main 与 HEAD 0/0。
- 内容：P14 金鱼 v4~v7 提交日志/RH 回执/v2~v7 复盘、P16 车库分镜与生图提示词与脚本、本地 MOSS 生图工作流文档+t2i 模板+楼梯井提示词、8 个跑批/生图脚本、三份规范文档更新、场景图 地下车库_v3。
- 留在工作区（不入库）：`.workbuddy/`、`_acl-repair/`、`_poll_ep05_p01.py`（一次性脚本）、`红绳片段14/验收_v3~v7`（质检 wav/png 大资产）、`红绳片段16/验收`（质检图，仅脚本入库）、`红绳片段16/上传包`（参考图/音频派生物）。
- 经验：v3/v4~v7 submit_log 均以 {"done":...} 收尾且不再增长，按 10-31 惯例作为凭证入库（此前 11-04 因任务运行中而排除 v3 log 的处理今日已闭环）。

## 2026-11-06 23:30
- 触发：每日归档自动化。
- 流程：fetch 后与 origin/main 0/0（无需合并）→ `git add -A` 带 17 条 pathspec 排除（.workbuddy、_acl-repair、_poll_ep05_p01.py、片段14 验收_v3~v7、片段16 上传包+framees_v1、片段17 上传包/验收/视频草稿、重配音实验室 4 个媒体目录）→ 单独补入 验收/候选声学对比.json → 暂存 39 文件（最大 11KB）→ 密钥扫描干净 → 提交 + 推送。
- 结果：commit `8fb5d4a`，push `788fcc7..8fb5d4a` 成功；origin/main 与 HEAD 0/0。
- 内容：P16 v1 成片复盘 + RH 回执、P17 全链路（分镜/提示词/开发说明币耗/回执/复盘）、片段划分.md P16 已成片+P17 新增、重配音实验室（README+6 脚本+12 工作流 API+config+4 轮 case+复盘）、AnyAudio 情绪配音文档、3 个跑批/后期脚本。
- 留在工作区（不入库）：`.workbuddy/`、`_acl-repair/`、`_poll_ep05_p01.py`、片段14/16/17 的验收图与上传包与视频草稿、重配音实验室的 wav/m4a/mp4（候选音频/参考音频/成片/验收试听）。
- 经验：`.gitignore` 已挡 *.jpg/*.png（仅人物/场景/道具例外）、*.mp4/*.mp3，但 **wav 与 m4a 不被忽略**，上传包与验收目录需显式 exclude；重配音实验室这类"实验室"目录宜按扩展名收（md/json/py/txt），媒体子目录单独排除，其 `验收/*.wav` `验收/*.m4a` 仍是未跟踪残留。

## 2026-11-08 03:08（任务类型变更为 DSH / 微信链路夜检）
- 触发：每晚检查 DeepSeek Harness（dsh web）是否正常、微信能否通信，异常时恢复。
- 固化工具：新增 `D:\HermesWorkspace\wechat-bridge\dsh_health_check.py`（只读自检，支持 `--json` / `--fix-url`），三项检查：①3080 端口+带 token 的 HTTP（**必须用 curl**，urllib 默认头会被服务端判 401，别误判为故障）②DeepSeek 官方 API（balance/models/chat）③微信渠道 `ilink/bot/getconfig`（只读、不消费消息，ret=0 且有 typing_ticket 即通）。
- 本次结果：dsh web OK（pid 58452，23:08 启动，303/401 正常）；微信渠道 OK（getconfig 200/ret=0/typing_ticket=true，state.json 会话 1、已见消息 51、出站 69）；**DeepSeek 官方 API FAIL：余额 -0.02 元 → chat 402 Insufficient Balance**（只影响走 deepseek-* 模型的会话与 Codex CLI，默认 agent 模型是 workbuddy:hy4free，故微信链路不受影响；今日 ledger 有 2 次 workbuddy:hy4free 成功调用）。
- 已修：补写缺失的 `dsh_url.txt`（23:08 那次重启脚本被终端关闭打断，锁文件与 URL 都没落地）、清理过期 `dsh_restart.lock`。
- 未修（有意不动）：`bsk probe failed`（browser-skill 插件缺 bsk CLI）、`CODEX_BINARY_UNAVAILABLE`、`CURSOR_BINARY_UNAVAILABLE` 三条非致命告警，均不影响微信；为它们重启在跑的服务风险大于收益。
- 经验：微信 `state.json` 只在有消息时写，空闲时长不能当断线证据；判定连通一律用 getconfig 探活。需用户动作的只有 DeepSeek 充值。

## 2026-11-09 03:00（DSH / 微信链路夜检）
- 触发：每晚检查 DeepSeek Harness（dsh web）、DeepSeek 官方 API、微信通信，异常时恢复。
- 结果：**三项全部 OK，无需修复动作**。
  ① dsh web OK：3080 端口在听，带 token HTTP 303（urllib 401 属预期，勿误判）。
  ② DeepSeek 官方 API OK：余额 **49.95 元**（11-08 曾 -0.02 触发 402，用户已充值），models/chat 均 200，可用模型 `deepseek-flash` / `deepseek-v4-pro`。
  ③ 微信渠道 OK：`ilink/bot/getconfig` 200 / ret=0 / typing_ticket=true；state 会话 1、已见消息 60、出站累计 83。
- 未修（沿用 11-08 结论，有意不动）：`bsk probe failed`、`CODEX_BINARY_UNAVAILABLE`、`CURSOR_BINARY_UNAVAILABLE` 三条非致命告警，均不影响微信链路，为它们重启在跑的服务风险大于收益。

## 2026-11-11 03:00（DSH / 微信链路夜检）
- 触发：每晚检查 DeepSeek Harness（dsh web）、DeepSeek 官方 API、微信通信，异常时恢复。
- 结果：**三项全部 OK，无需修复动作**。
  ① dsh web OK：3080 端口在听，带 token HTTP 303（urllib 401 属预期，勿误判）。
  ② DeepSeek 官方 API OK：余额 **48.91 元**（11-10 为 49.20，正常消耗），models/chat 均 200，可用模型 `deepseek-flash` / `deepseek-v4-pro`。
  ③ 微信渠道 OK：`ilink/bot/getconfig` 200 / ret=0 / typing_ticket=true；state 会话 1、已见消息 61、出站累计 85（state 空闲约 43h，仅表示无新消息，不作断线证据）。
- 未修（沿用 11-08 结论，有意不动）：`bsk probe failed`、`CODEX_BINARY_UNAVAILABLE`、`CURSOR_BINARY_UNAVAILABLE` 三条非致命告警，均不影响微信链路；插件无新增冲突。

## 2026-11-12 03:00（DSH / 微信链路夜检）
- 触发：每晚检查 DeepSeek Harness（dsh web）、DeepSeek 官方 API、微信通信，异常时恢复。
- 结果：**三项全部 OK，无需修复动作**。
  ① dsh web OK：3080 端口在听，带 token HTTP 303（urllib 401 属预期，勿误判）。
  ② DeepSeek 官方 API OK：余额 **48.46 元**（11-11 为 48.91，正常消耗），models/chat 均 200，可用模型 `deepseek-flash` / `deepseek-v4-pro`。
  ③ 微信渠道 OK：`ilink/bot/getconfig` 200 / ret=0 / typing_ticket=true；state 会话 1、已见消息 63、出站累计 89（state 空闲约 13h，仅表示无新消息，不作断线证据）。
- 未修（沿用 11-08 结论，有意不动）：`bsk probe failed`、`CODEX_BINARY_UNAVAILABLE`、`CURSOR_BINARY_UNAVAILABLE` 三条非致命告警，均不影响微信链路；插件无新增冲突。

## 2026-11-13 09:04~09:27（DSH 重启 + 换模型 V4.1-Flash）
- 用户报「又开始了」（再次退化）并要求重启 DSH、把模型换成 DeepSeek-V4.1-Flash。
- 已改：①`cordis.patch.yml` agent-default-model 从 hy4free → **workbuddy:deepseek-v4.1-flash**（effort high，新会话生效）②V4.1-Flash `maxTokens 128000→16384`（与 space-bunny 同样防刷屏）③space-bunny 保持 16384。
- ⚠️ **会话级模型选择改投影文件没用**：projection 的 modelSelection 会被 DSH 从 session 事件流重建（seq 会回跳），现有微信会话仍锁在 space-bunny。换会话模型唯一可靠途径 = 用户在微信发 `/model` 选 V4.1-Flash，或发 `/new` 开新会话（自动用新默认模型）。
- **重大踩坑：cmd 脚本必须 CRLF**。Write 工具写出的 LF 结尾 .cmd 会让 cmd 解析异常——`cd /d` 行被吞，重定向 `> 相对路径` 全部落到**调用方 cwd**（红绳项目根目录）。后果：dsh_web.out.log 里永远等不到 token，重启脚本 45s 超时误报 failed，还产生 EADDRINUSE 多实例叠加。修复：python 写 CRLF + **重定向用绝对路径**（`> "D:\HermesWorkspace\wechat-bridge\dsh_web.out.log"`），彻底与 cwd 无关。`dsh_health_check.py` 无需改（token 重新出现在 out.log，自检恢复全绿）。
- 本次折腾出的多实例残留（13776/30008/30608 等带 EADDRINUSE 的僵尸）已全部 taskkill 清掉，最终单实例运行，09:26 自检 4 项全 OK（dsh 303 / DeepSeek 46.83 / 微信 ret=0）。
- 遗留：`红绳\dsh_web.out2.log`、`dsh_web.err2.log`（09:21 错位日志，11 字节级）被 safe-delete 钩子卡住删不掉（genie-trash 对中文路径失败且 fail-closed），无害，等用户手动删。
- 待用户动作：微信里发 `/model` → 选 DeepSeek-V4.1-Flash（当前会话仍会用 space-bunny 直到切换）。

## 2026-11-13 08:34（DSH 乱回话事故 —— 定位 + 修复）
- 现象：微信 bot 回复里反复出现 `课×数千~上万` 的重复垃圾（turn 97/112/116），今晨用户发 `css` 测试串，bot 竟原样回显 `css`/`课` 刷屏。模型 workbuddy:space-bunny（defaultEffort max，免费渠道）文本退化循环，垃圾进历史后进一步自我强化；会话上下文已 745k/1M，其中 messageTokens 461k 含巨型垃圾段。
- bot 自身在 turn 120/121 已承认故障并把「重复碎片立即停笔」等 4 条硬规则写进用户级记忆。
- 已做修复：
  1. `~/.dsh/profiles/web/cordis.patch.yml` 里 space-bunny `maxTokens: 128000 → 16384`（防止单次退化输出灌几万字），`dsh --profile web --dump-config` 已确认生效。
  2. 重启 DSH web 使配置生效（新 pid 3304，token 已写入 dsh_url.txt），重启后自检 4 项全 OK，DeepSeek 余额 46.83。
- 踩坑：**从 WorkBuddy 工具会话跑 restart_dsh3.ps1 必失败**——沙箱环境同时带 `path` 与 `Path` 两个变量，脚本里 Start-Process 抛「已添加项。字典中的关键字:path」；schtasks 又被沙箱拒绝。解法：新建 `wechat-bridge/start_dsh_detached.cmd`（纯 ASCII 路径），用 `cmd //c start "" //min` 分离启动 node + 日志重定向，启动后手工把 out.log 里的 token URL 写回 dsh_url.txt。桌面双击「重启DSH.cmd」不受影响。
- 待用户动作（我无法代办）：在微信里发一次 `/compact`（压缩会话、清掉历史里的巨型垃圾段，保留任务连续性）；若想彻底换环境可发 `/new`（会丢上下文）。若之后再退化，微信里发 `/model` 可切回 hy4free（只接受 high 档）。
- 自检脚本 dsh_health_check.py 仍为 08:14 升级版（系统代理自愈），本次无需改动。

## 2026-11-13 03:00（DSH / 微信链路夜检）—— 首次出现真实故障并修复
- 现象：初次自检三项里 DeepSeek / 微信全 FAIL，错误统一为 `WinError 10061 目标计算机积极拒绝`。
- 定位：**不是服务故障，是系统代理坏死**。`HKCU\...\Internet Settings` 里 `ProxyEnable=1`、`ProxyServer=http://127.0.0.1:65532`，但该端口无任何进程监听（Clash Verge 退出时没清代理）。所有走 WinINET 的程序（python urllib、curl、浏览器）全部 10061；DSH 自身是 node fetch 不走系统代理，所以日志里 `api.deepseek.com/models` 一直正常加载——这是关键鉴别点。
- 修复：`ProxyEnable` 置 0（保留 ProxyServer 记录便于恢复）→ 直连恢复，baidu 200、deepseek 401（无 key 的正确响应）。
- 工具升级：`wechat-bridge/dsh_health_check.py` 新增第 0 项「系统代理」检查 + **默认自动修复**（只在 enabled 且端口无监听时动手，`--no-fix-proxy` 可只报告）；代理坏死时自动切直连取证（`_USE_DIRECT`），避免把环境故障误判成服务故障。已双向演练（打回 1 → 自动关闭 → 输出 FIXED → ProxyEnable 回 0）。
- 最终自检：0 代理 OK / 1 dsh web OK（303）/ 2 DeepSeek OK（余额 48.04，models+chat 200）/ 3 微信 OK（getconfig 200 ret=0 typing_ticket=true；state 会话 1、已见 64、出站 90，较昨日各 +1，说明确有一次真实收发）。
- 插件核查：`integrations/dsh-weixin` 单账号无重复（wx_d6fc00...2b36），`dsh-im` 无第二个微信绑定，无 EADDRINUSE / 模块缺失；仅沿用 bsk/CODEX/CURSOR 三条非致命告警，仍有意不动。
- 复发风险：Clash Verge 异常退出会再次留下死代理；夜检已能自愈，用户侧无需操作。

## 2026-11-10 03:00（DSH / 微信链路夜检）
- 触发：每晚检查 DeepSeek Harness（dsh web）、DeepSeek 官方 API、微信通信，异常时恢复。
- 结果：**三项全部 OK，无需修复动作**。
  ① dsh web OK：3080 端口在听，带 token HTTP 303（urllib 401 属预期，勿误判）。
  ② DeepSeek 官方 API OK：余额 **49.20 元**（11-09 为 49.95，正常消耗），models/chat 均 200，可用模型 `deepseek-flash` / `deepseek-v4-pro`。
  ③ 微信渠道 OK：`ilink/bot/getconfig` 200 / ret=0 / typing_ticket=true；state 会话 1、已见消息 61、出站累计 85。
- 未修（沿用 11-08 结论，有意不动）：`bsk probe failed`、`CODEX_BINARY_UNAVAILABLE`、`CURSOR_BINARY_UNAVAILABLE` 三条非致命告警，均不影响微信链路；插件无新增冲突。

## 2026-11-14 03:00（DSH / 微信链路夜检）—— 发现「静默丢轮次」新故障型，工具已升级
- 四项探活全绿：代理未启用 / dsh web 303 / DeepSeek 46.69（models+chat 200）/ 微信 getconfig 200 ret=0 typing_ticket=true（已见消息 79，较 11-12 的 63 增 16，属 11-13 上午密集对话）。
- **真正的故障是探活抓不到的**：11-13 11:00:52 用户发「新开一个会话」→ bot 只回了「已排队，等待前序消息处理。」→ 11:29:40 进程被重启（无计划任务，系手动/另一会话）→ turn 128 被掐断、队列丢失 → 该消息整晚无人应答。11-14 00:00:01 定时提醒又起 turn 129，跑 hyperflow 时长压测 2 分钟后被 00:02:26 的重启掐断（peak 15.8GB 时 15s 段 crash）。state.json 的 sessions 仍指向旧会话，即「新开会话」从未生效。
- 会话未关闭轮次会由 DSH 在下次写开时自动补 `interruptedTurnClosers`（`dsh-session` → `agent-loop` 的 `persistence.open(id,"write")`），因此**不会永久卡死**，用户下条消息即开新轮次；无需人工改投影/事件。
- 工具升级（`wechat-bridge/dsh_health_check.py` 新增第 4 项「应答闭环」）：①最后入站(receivedAt/messageTimeMs) 晚于最后出站 5min 以上 → 判未应答 ②最后一条出站若只是「已排队/已提交补充指令」回执 → 判正文未发出 ③读会话投影 `turnBoundary.openTurnStartSeq` + 投影 mtime，openTurn 非空且 >30min 未更新 → 判「轮次被重启打断」。已实测：本晚场景正确输出 WARN，前 3 项仍 OK。
- 插件核查无冲突：3080 单监听（node 11980，00:02 启动）、单 dsh 实例、weixin 账号单条（wx_d6fc00…2b36）、dsh-im 无第二绑定、外连 140.207.56.23:443（03:03 刚重建，长轮询活着）、`dsh-promptgen` 软链虽在 package.json 里显示乱码但实际解析到 `F:\WorkFisher…\ComfyUI\dsh-promptgen` 有效、out.log 零错误行。沿用 bsk/CODEX/CURSOR 三条非致命告警不动。
- 配置观察：`cordis.patch.yml` agent-default-model 已于 11-13 11:28 从 deepseek-v4.1-flash 回落 hy4free（注释仍写 V4.1-Flash），当前会话 lastUsed 仍是 space-bunny/max。属用户 UI 侧改动，未擅自改回；要换在微信发 `/model` 或 `/new`。

## 2026-11-15 03:00（DSH / 微信链路夜检）
- 触发：每晚检查 DeepSeek Harness（dsh web）、DeepSeek 官方 API、微信通信，异常时恢复。
- 结果：**四项探活三项全 OK，无需修复动作**。
  ① 系统代理 OK：未启用（ProxyEnable=0），无坏死代理。
  ② dsh web OK：3080 仅 PID 11980 单实例监听（11-14 00:02 启动的同一进程，无堆叠），带 token HTTP 303（urllib 401 属预期）。
  ③ DeepSeek 官方 API OK：余额 **45.44 元**（11-14 为 46.69，正常消耗），models/chat 均 200，可用模型 `deepseek-flash` / `deepseek-v4-pro`。
  ④ 微信渠道 OK：`ilink/bot/getconfig` 200 / ret=0 / typing_ticket=true；账号 wx_d6fc00…2b36 单条；state 已见消息 79（与 11-14 持平，11-13 11:01 后无新入站，约 40h 空闲，不作断线证据）。
- 应答闭环 WARN（延续 11-14 结论，非新故障）：最后一条出站仍是 11-13 11:01 的「已排队，等待前序消息处理。」回执——用户那条「新开一个会话」始终未被执行；此后无任何新入站消息触发处理。会话投影 openTurn 已为空（interruptedTurnClosers 已生效），链路本身健康，**用户下一条消息即可正常开始新轮次**。
- 待用户动作：在微信里发 `/new`（真正完成「新开会话」，摆脱旧会话巨型上下文），或直接发下一条消息验证链路。
- 插件核查：无新增冲突，仍沿用 bsk probe failed / CODEX_BINARY_UNAVAILABLE / CURSOR_BINARY_UNAVAILABLE 三条非致命告警（有意不动，均不影响微信）。

## 2026-11-17 03:00（DSH / 微信链路夜检）
- 触发：每晚检查 DeepSeek Harness（dsh web）、DeepSeek 官方 API、微信通信，异常时恢复。
- 结果：**四项探活三项全 OK，无需修复动作**。
  ① 系统代理 OK：未启用（ProxyEnable=0），无坏死代理。
  ② dsh web OK：3080 仅 PID 11980 单实例监听（11-14 00:02 起同一进程，稳定运行三天），带 token HTTP 303（urllib 401 属预期）。
  ③ DeepSeek 官方 API OK：余额 **44.94 元**（11-16 为 45.19，正常消耗），models/chat 均 200，可用模型 `deepseek-flash` / `deepseek-v4-pro`。
  ④ 微信渠道 OK：`ilink/bot/getconfig` 200 / ret=0 / typing_ticket=true；账号 wx_d6fc00…2b36 单条；state 已见消息 79（与 11-14~16 持平，约 88h 无新入站，不作断线证据）。
- 应答闭环 WARN（延续 11-13~16 结论，非新故障）：最后一条出站仍是 11-13 11:01 的「已排队，等待前序消息处理。」回执；此后无任何新入站消息，链路本身健康，用户下一条消息即可正常开始新轮次（建议发 `/new` 真正完成新开会话）。
- 插件核查：3080 单监听、单 dsh 实例、无新增冲突；沿用 bsk / CODEX / CURSOR 三条非致命告警（有意不动，均不影响微信）。

## 2026-11-16 03:00（DSH / 微信链路夜检）
- 触发：每晚检查 DeepSeek Harness（dsh web）、DeepSeek 官方 API、微信通信，异常时恢复。
- 结果：**四项探活三项全 OK，无需修复动作**。
  ① 系统代理 OK：未启用（ProxyEnable=0），无坏死代理。
  ② dsh web OK：3080 仅 PID 11980 单实例监听（11-14 00:02 起同一进程，稳定运行两天），带 token HTTP 303（urllib 401 属预期）。
  ③ DeepSeek 官方 API OK：余额 **45.19 元**（11-15 为 45.44，正常消耗），models/chat 均 200，可用模型 `deepseek-flash` / `deepseek-v4-pro`。
  ④ 微信渠道 OK：`ilink/bot/getconfig` 200 / ret=0 / typing_ticket=true；账号 wx_d6fc00…2b36 单条；state 已见消息 79（与 11-14/11-15 持平，约 64h 无新入站，不作断线证据）。
- 应答闭环 WARN（延续 11-13/14/15 结论，非新故障）：最后一条出站仍是 11-13 11:01 的「已排队，等待前序消息处理。」回执；此后无任何新入站消息，链路本身健康，用户下一条消息即可正常开始新轮次（建议发 `/new` 真正完成新开会话）。
- 插件核查：3080 单监听、单 dsh 实例、无新增冲突；沿用 bsk / CODEX / CURSOR 三条非致命告警（有意不动，均不影响微信）。

## 2026-11-19 03:00（DSH / 微信链路夜检）
- 触发：每晚检查 DeepSeek Harness（dsh web）、DeepSeek 官方 API、微信通信，异常时恢复。
- 结果：**五项探活全部 OK，无需任何修复动作**。
  ① 系统代理 OK：未启用（ProxyEnable=0），无坏死代理。
  ② dsh web OK：3080 仅 PID 43848 单实例监听（注意：进程已从 11980 换代，昨晚 11-18 的 CDP 修复后重启过），带 token HTTP 303（urllib 401 属预期）。
  ③ DeepSeek 官方 API OK：余额 **44.32 元**（11-18 为 44.70，正常消耗），models/chat 均 200，可用模型 `deepseek-flash` / `deepseek-v4-pro`。
  ④ 微信渠道 OK：`ilink/bot/getconfig` 200 / ret=0 / typing_ticket=true；账号 wx_d6fc00…2b36 唯一；长轮询 TCP ESTABLISHED 到 140.207.56.23:443 且归属 DSH 进程 43848（活跃）；state 已见消息 81（较 11-17 的 79 增 2）、出站累计 141，最后入站 11-18 07:27、出站 08:08，应答闭环 OK 无 WARN。
  ⑤ 会话活跃：投影 11.6 分钟前仍被写过（夜间守护探针在跑），agent 闭环活着。
- 插件核查：无新增冲突；沿用 bsk probe failed / CODEX_BINARY_UNAVAILABLE / CURSOR_BINARY_UNAVAILABLE 三条非致命告警（有意不动，均不影响微信）。日志无 fatal，err 仅 0.1MB。
- 结论：链路健康，微信通信正常，今晚未做任何干预。

## 2026-11-18 03:15（DSH / 微信链路夜检）—— 无故障，工具两处升级
- 五项探活全 OK，无需恢复动作：代理未启用 / dsh web 303（PID 11980，11-14 00:02 起单实例）/ DeepSeek 44.70（models+chat 200）/ 微信 getconfig 200 ret=0 typing_ticket=true（账号 wx_d6fc00…2b36 唯一，长轮询 TCP 连着 182.50.15.252:443）/ 应答闭环 OK。
- **活跃性证据（新增判据）**：微信主会话 `session-fc64c2d8…` 昨晚连开三个子会话（00:06/01:18/02:18），turn 153 于 03:03:04 正常 completed（模型回复 + pwsh 调用 + turn/end），turn 154 亦收尾 → agent 闭环活着，不是只有 HTTP 通。最近 6 轮回复均为「守护在线（pid=38496），未做任何重启。」，无 11-13 那种重复碎片退化。
- 工具升级 1（消误报）：`reply_loop` 增加 `STALE_HOURS=24` 保鲜期 + `inbound_age_h` 字段。只回执不答/入站未回应超过 24h 降级为 note（历史遗留），不再每晚报 WARN——此前连续 4 晚报的都是 11-13 那条 5 天前的静默事件。
- 工具升级 2（消性能隐患）：`err_scan` 原来每个模式各整篇读一遍 27 万行日志（9.7MB），改为头部 256KB + 尾部 1MB 窗口（`ERR_HEAD_BYTES`/`ERR_TAIL_BYTES`）并输出 `size_mb`；全量自检 2s 完成，启动期 bsk/CODEX/CURSOR 告警仍能扫到。err.log 的 5.5 万条 `TAG_RESOLVE_FAILED`（`!!js` 标签）来自 `dsh-plugin-ops-core` 内置的普通 yaml 解析器，**只读不回写**，属噪声；`start_dsh_detached.cmd` 的 `>` 会在重启时清零，无需手动清理。
- 已查清非问题：`--dump-config` 里 tool-bash 与 tool-pwsh 都 disabled 是 web-app 层的正常设计（改用 persistent-* 版本，Windows 下 persistent-pwsh 启用）；bili-whale 新插件 `notify.type=none`、夜间仅 wake 1 次，不抢微信；node 进程共 8 个但只有 PID 11980 是 DSH，其余是 WorkBuddy 自身 MCP。
- 结构性提醒（不建议自动化擅改）：微信 p2p 绑的会话同时被定时任务/守护探针复用（154 轮、2.13 亿 input token），忙时会回「已排队」——这正是 11-13 丢消息的机理。该会话仍锁 `workbuddy:space-bunny`（max），而配置默认已是 hy4free、model_probe 也报 `activeModel=hy4free`；改投影无效（DSH 从事件流重建），只能由用户在微信发 `/new`（推荐，甩掉巨型上下文）或 `/model` 切模型。
- 待用户动作：微信随手发一条消息验证入站（已静默 112h，getconfig 只能证明凭证有效）。

## 2026-11-25 03:00（DSH / 微信链路夜检）—— DSH 进程死亡，已重启恢复
- 现象：自检第 1 项 FAIL——3080 端口完全无监听（netstat 确认），DSH web 进程消失（其余 node 进程均为 WorkBuddy 自身 MCP）。11-24 14:52 用户有一条微信消息未被回复（最后出站停在 11-21 16:10 的「模型服务正在限流 MODEL_RATE_」错误回执），推断 DSH 在 11-21 限流错误后某个时间点死亡/未再启动。
- 修复：`cmd //c start "" //min D:\HermesWorkspace\wechat-bridge\start_dsh_detached.cmd` 分离启动成功（PID 40308，单实例）；新 token `UIRGwNz…` 与旧的不同，已回写 `dsh_url.txt`。
- 重启后自检：0 代理 OK（ProxyEnable=1 且 65532 端口有监听，非坏死，未触发自动切直连）/ 1 dsh web OK（303）/ 2 DeepSeek OK（余额 42.13，11-19 为 44.32，正常消耗）/ 3 微信 OK（getconfig 200 ret=0 typing_ticket=true，账号 wx_d6fc00…2b36 唯一）。
- 未自动恢复项：11-24 那条消息已被消费（seen 83→84）但未处理，重启后开放轮次 seq 20297 仍未闭合（interruptedTurnClosers 需下次写开才补），**该消息不会自动重放**。无专用出站发送工具，按惯例不代发微信；用户重发该消息即可正常获得回复。last outbound 仍是限流错误文本属历史遗留（STALE 24h 已降级为 note 级）。
- 插件核查：无新增冲突；沿用 bsk probe failed / CODEX_BINARY_UNAVAILABLE / CURSOR_BINARY_UNAVAILABLE 三条非致命告警（有意不动，均不影响微信）。
- 经验：本轮首次出现「DSH 进程整体死亡」型故障（此前都是限流/静默丢轮次）；`start_dsh_detached.cmd` + 手工回写 dsh_url.txt 流程一次成功，约 30s 起监听。

