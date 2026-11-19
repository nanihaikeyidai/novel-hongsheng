# LearnHarness 使用卡（本机已装）

> 安装日期 2026-11-18｜版本 **v0.6.1**（Windows x64）｜来源 [amosblomqvist/learnharness](https://github.com/amosblomqvist/learnharness)

---

## 1. 它是什么

**一个装在电脑上的 AI 私教**（独立 Electron 桌面应用，**不是 DSH 插件**）。
用 agent 教你学东西，四步闭环：

| 步骤 | 做什么 |
|---|---|
| **Measure（摸底）** | 先测你懂到哪——靠**你的答案 + 信心 + 思考过程**定位起点 |
| **Plan（规划）** | 从你的起点到目标画依赖图，**你能看见路线图** |
| **Teach（教）** | 每一步建在你已懂的东西上；**让你先猜再讲**，当场检查，卡住立刻换讲法补 |
| **Practice（练）** | 出题让你**在不被点名的情况下**自己把知识调出来 |

外加**持久化知识图谱**：学过的东西存成「命题 + 推理链」（不是能力评分），下次打开接着教。

---

## 2. 本机信息

| 项 | 值 |
|---|---|
| 安装路径 | `C:\Users\Administrator\AppData\Local\Programs\LearnHarness\LearnHarness.exe` |
| 数据目录 | `C:\Users\Administrator\AppData\Roaming\LearnHarness\data\` |
| 密钥文件 | `C:\Users\Administrator\AppData\Roaming\LearnHarness\auth.json`（**明文**，见 §5） |
| 日志 | `C:\Users\Administrator\AppData\Roaming\LearnHarness\logs\main.log` |
| 卸载 | 设置 → 应用，或跑 `Uninstall LearnHarness.exe` |
| 官网 / 仓库 | [learnharness.ai](https://learnharness.ai) · [GitHub](https://github.com/amosblomqvist/learnharness) |

**启动**：桌面快捷方式，或
```powershell
Start-Process "$env:LOCALAPPDATA\Programs\LearnHarness\LearnHarness.exe"
```
**带调试端口启动**（自动化用）：
```powershell
Start-Process "$env:LOCALAPPDATA\Programs\LearnHarness\LearnHarness.exe" -ArgumentList "--remote-debugging-port=9335"
```
然后 `http://127.0.0.1:9335/json/list` 能拿到页面 target，可用 CDP 驱动。

---

## 3. 模型配置（已配好，直接能用）

走**自定义 OpenAI 兼容端点**接的是 **DeepSeek 官方 API**（不是我们 DSH 的 WorkBuddy 路由）。

| 槽位 | 模型 | 思考档 | 用途 |
|---|---|---|---|
| Strong | `deepseek-flash` | high | 主对话 + 摸底（prober/teacher） |
| Cheap | `deepseek-flash` | low | 后台角色（researcher/extractor/auditor） |
| Vision | `deepseek-flash` | low | 看图（visualMaker/pdfReader） |

- 端点：`https://api.deepseek.com/v1`（**LearnHarness 不会自动补 /v1**，要写全）
- key 来源：`~/.dsh/.credentials.yaml` 的 `DEEPSEEK_API_KEY`（与 DSH 共用同一个）
- 两个模型都可用：`deepseek-flash`（**支持图像**）、`deepseek-v4-pro`（纯文本）

**配置改法**（源码：`src/core/settings.ts` / `src/core/auth-keys.ts`）：
- `data/settings.json` → `customProvider`（baseUrl + models + `credentialBindingId`）
- `auth.json` → **两个键**：
  - `__learnharness_custom_provider_binding`：JSON 字符串 `{"version":1,"id":"<32位hex>","baseUrl":"...","authMode":"apiKey","fileKeyBaseUrl":"..."}`
  - `CUSTOM_OPENAI_API_KEY`：key 本身

⚠️ **`settings.json` 的 `credentialBindingId` 必须等于 binding 里的 `id`，`baseUrl` 和 `authMode` 也必须一致**——否则 `customBindingMatches()` 判否，provider 不会被注册（界面会退回 "Set up your models" 首启向导）。

**重写配置的脚本**：`D:\HermesWorkspace\_tmp\learnharness\write_config2.py`（改完必须重启应用）。

---

## 4. 踩过的坑（都修好了）

### 坑 1：官方 v0.6.1 打包漏了 `@shikijs/*` → 整站 HTTP 500
- 现象：日志刷 `ERR_MODULE_NOT_FOUND: Cannot find package '@shikijs/core'`，每个页面 500
- 根因：`shiki@3.23.0` 需要 6 个 `@shikijs/*` 包，官方只打包了 `@shikijs/vscode-textmate` 一个
- 修法：从 npm 装**精确版本 3.23.0**（不是 latest 4.6.0）的 6 个包 → `resources\server\standalone\node_modules\@shikijs\`
  - `core` `types` `themes` `langs` `engine-javascript` `engine-oniguruma`
- ⚠️ 解压时注意：包名要落在 `@shikijs\<name>` 下，别多套一层 `@shikijs\@shikijs\<name>`

### 坑 2：`auth.json` 位置搞错
- **`auth.json` 在 `%APPDATA%\LearnHarness\`（跟 `data\` 平级），不在 `data\` 里**
- 依据：`config.ts` 的 `AUTH_FILE = process.env.LH_AUTH_FILE` → Electron 主进程指向 `userData/auth.json`
- 写错位置 → 日志显示 `auth.json: ABSENT (no BYOK keys yet)`

### 坑 3：只写 key 不写 binding → 弹首启向导
- 现象：点 Send 弹出 "Set up your models / Choose your provider and paste its API key"
- 原因：`customKeyAuthorized()` 要求 binding 与 settings **三个字段全对**，光有 key 不够

### 坑 4：Windows 安装包未签名
- `Get-AuthenticodeSignature` → `NotSigned`
- README 自己写了会弹 SmartScreen 警告。**安装时选"仍要运行"**（我们是用 `/S` 静默装的，没触发）

---

## 5. 安全边界（用之前要知道）

| 事实 | 含义 |
|---|---|
| **API key 明文存 `auth.json`** | 不是加密保险箱，权限受限但**别把整个 LearnHarness 配置目录打包或分享** |
| **文件工具只读，但有广泛文件系统访问权** | 拖进 PDF/图片 = 把路径给 agent；它只挡"已知凭据/私密目录"，**不是所有敏感内容都挡** |
| **文件内容会被送到配置的模型供应商** | 拿它学红绳的私有剧本/设定 = 把创作素材发给 DeepSeek |
| **本地存储 ≠ 离线处理** | 模型请求、网页研究、听写都会联网 |
| **知识图谱存的是命题+推理链，不是能力分** | 里面是你自己写下的思考过程 |
| **Windows 安装包未签名 + 550 个未关 issue** | 项目一个月大，成熟度有限；建议**别拿主力机的私密文件喂它** |

**给我们的用法建议**：
- ✅ 用来学**通用技术**（H3 原理、ComfyUI 参数、模型对比、编程概念）
- ✅ 用来学**我们自己的公开工作流**（如 ComfyUI 工作流 JSON、脚本）
- ⚠️ **不要**喂红绳的私有剧本、角色设定、未发布的分镜
- ⚠️ 它的"思考过程"会留在本地知识图谱里，别在同一个账号混放敏感内容

---

## 6. 已知限制

- **自动更新已关**（`settings.json` 的 `general.autoUpdate: false`）——本机系统代理 `127.0.0.1:65532` 是死的，会导致 `net::ERR_CONNECTION_RESET`。**要更新手动去 GitHub Releases 重装**。
- 网页研究（Tavily/Brave/Exa/Firecrawl/Ollama）和听写（Deepgram）**都没配 key**，这两个功能不可用。
- 没有中文界面（`electronLanguages: en`）。

---

## 7. 待办

- [ ] 配一个搜索 key（Tavily 或 Brave）→ 让 researcher 角色能查资料。**本机的 web-search-deepseek baseURL 曾经 402，搜不了**——LearnHarness 用自己的 key，不走 DSH 那套。
- [ ] 试一次「Extract files…」把 ComfyUI 工作流 JSON 喂进去，验证本地文件读取链路。
- [ ] 若上游发新版（>0.6.1），重装后**必须重做坑 1 的 shiki 补包**。
