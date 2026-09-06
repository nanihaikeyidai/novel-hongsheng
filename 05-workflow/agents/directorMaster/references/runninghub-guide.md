# RunningHub 云端生成指南

> 当用户指定使用 RH / RunningHub / 云端生成时，使用本指南通过浏览器操作 RunningHub 线上工作流生成视频。
> 工作流 ID：`2096059277453643778`
> 工作流 URL：`https://www.runninghub.cn/workflow/2096059277453643778`

---

## 一、触发条件

用户输入以下任一命令时，切换到 RunningHub 云端生成模式：

- `/rh`
- `/runninghub`
- `/cloud`
- `/render rh`
- 自然语言："用 RH 生成"、"云端生成"、"RunningHub 生成"、"线上生成"

**默认渲染通道**：本地 ComfyUI（`http://127.0.0.1:8188`）。只有用户明确指定 RH 时才使用云端。

---

## 二、前置准备

### 2.1 加载浏览器自动化 Skill

操作 RunningHub 必须使用 `browser-use-automation` skill（`computer_use_tool` + `plane="bu"` + `seed_browser_use`）。

```python
computer_use_tool(plane="bu", code="""
import seed_browser_use as bu
bu.navigate("https://www.runninghub.cn/workflow/2096059277453643778")
bu.wait_for_load()
bu.snapshot()
""")
```

### 2.2 登录检查

打开工作流页面后，检查是否需要登录：

- 如果页面显示登录弹窗、扫码登录、或内容被登录遮罩遮挡 → **必须调用 `interaction.request_action`**，`type="browserControl"`，请用户手动完成登录。
- 如果页面已登录且工作流编辑器可见 → 继续操作。

**登录后必须重新 `bu.snapshot()` 获取新鲜 refs，旧 refs 失效。**

### 2.3 素材准备

RunningHub 云端生成需要将素材上传到工作流。提前整理好：

| 素材类型 | 数量限制 | 来源 |
|---|---|---|
| 全局参考图 | ≤5 张 | `05-images/人物/`、`05-images/场景/`、`05-images/道具/` |
| 全局参考音频 | ≤3 条 | `05-images/音色/` 或各 EP `归档素材/音色/` |
| 分段故事板 | 每分段1张 | 各 EP `红绳片段NN/故事板.png` |
| timeline_data | 1个 JSON | 按 phase 06 规范组装 |

将所有素材复制到一个临时目录，方便上传时选择。

---

## 三、操作流程

### 第一步：打开工作流并确认加载

1. 导航到工作流 URL
2. 等待页面完全加载（工作流画布、节点可见）
3. 确认 MiniMaxH3Director 节点存在（节点标题含 "Director" 或 "H3"）
4. 如果工作流未自动加载，点击页面上的"加载"或"打开"按钮

### 第二步：上传全局参考图

1. 找到 MiniMaxH3Director 节点的全局参考图上传区域（通常显示为图片占位框，标注"图片1"-"图片5"）
2. 点击第一个图片占位框 → 选择文件 → 上传对应人物/场景图
3. 依次上传全部全局参考图
4. 每张图上传后确认缩略图显示正确

**注意**：RunningHub 的图片上传可能需要点击"上传"按钮后在文件选择器中选择。如果 `bu.upload()` 不可用，使用 `interaction.request_action` 请用户手动上传。

### 第三步：上传全局参考音频

1. 找到音频上传区域（标注"音频1"-"音频3"）
2. 依次上传音色参考音频（.wav 或 .mp3）
3. 确认每条音频上传后显示文件名和时长

**如果没有参考音频**：跳过此步，在提示词中用 `<Audio N>` 文字描述音色基线。

### 第四步：填入 timeline_data

1. 找到 MiniMaxH3Director 节点的 `timeline_data` 输入框（通常是一个大文本框，标注 "timeline_data" 或 "时间线数据"）
2. 清空原有内容
3. 将组装好的 timeline_data JSON 完整粘贴进去
4. 确认 JSON 无语法错误（RunningHub 可能会实时校验）

**timeline_data 组装规范**：与本地 ComfyUI 完全一致，参见 `phases/06-comfyui-invoke.md` 第二步。

### 第五步：确认工作流参数

检查以下参数是否正确：

| 参数 | 期望值 |
|---|---|
| task_type | `r2v — 参考主体生视频(Reference to Video)` |
| width | 1056 |
| height | 608 |
| frame_rate | 24 |
| steps | 8 |
| sampler | euler |
| scheduler | simple |
| seed | 666（或用户指定） |
| total_frames | 各分段帧数之和 |

### 第六步：提交运行

1. 找到页面上的"运行"或"Run"按钮（通常在右上角或节点工具栏）
2. 点击运行
3. 确认任务已进入队列（页面显示运行状态、进度条或任务 ID）
4. 记录任务 ID 或运行链接

### 第七步：等待生成完成

RunningHub 云端生成时间取决于队列长度和视频时长：

- 单分段 15 秒：约 3-8 分钟
- 4 分段 60 秒：约 10-25 分钟
- 队列繁忙时可能更长

**等待策略**：
- 每 60 秒刷新一次页面或检查任务状态
- 使用 `bu.snapshot()` 查看进度
- 如果页面有"任务中心"或"历史记录"，可以在那里查看状态
- 生成完成后，页面会显示视频预览和下载按钮

### 第八步：下载视频

1. 生成完成后，找到视频输出节点的预览区域
2. 点击"下载"按钮，或右键视频预览 → "视频另存为"
3. 使用 `bu.download()` 或 `bu.wait_for_download()` 获取文件
4. 视频通常有两个版本（8bit 和 10bit），都下载

**下载文件命名**：
- `红绳_EPXX_片段NN-NN_8bit.mp4`
- `红绳_EPXX_片段NN-NN_10bit.mp4`

保存到 `05-workflow/epXX/` 目录。

---

## 四、常见问题处理

### 4.1 登录过期

如果操作过程中跳转到登录页，立即停止操作，调用 `interaction.request_action` 请用户重新登录。

### 4.2 上传失败

- 检查文件大小（RunningHub 可能有单文件大小限制，通常 ≤50MB）
- 检查文件格式（图片支持 png/jpg/webp，音频支持 wav/mp3）
- 重试上传；连续失败 2 次后请用户手动上传

### 4.3 timeline_data 粘贴失败

- 检查 JSON 是否有语法错误（用 `json.loads()` 验证）
- 检查文本框是否有字符数限制
- 如果文本框不支持直接粘贴大段 JSON，尝试分段粘贴或使用 `bu.js()` 注入

### 4.4 运行报错

- 读取页面上的错误信息
- 常见错误：素材未上传、timeline_data 格式错误、节点参数缺失
- 修正后重新提交
- 如果是 RunningHub 平台内部错误，记录错误信息，切换到本地 ComfyUI

### 4.5 队列等待过长

- 如果排队超过 30 分钟，告知用户当前队列状态
- 询问是否切换到本地 ComfyUI
- 用户同意后，按本地流程提交

---

## 五、本地 vs 云端对比

| 维度 | 本地 ComfyUI | RunningHub 云端 |
|---|---|---|
| 启动 | 需手动启动服务 | 无需启动，打开网页即用 |
| 速度 | 取决于本地 GPU（RTX 4070 Ti SUPER 约6-7分钟/分段） | 取决于云端队列和算力 |
| 成本 | 免费（本地硬件） | 可能消耗 RunningHub 积分/额度 |
| 素材管理 | 复制到 input 目录 | 网页上传 |
| 稳定性 | 本地环境可控 | 依赖网络和平台 |
| 适用场景 | 日常批量制作、迭代调试 | 本地不可用、需要云端算力、分享协作 |

**选择原则**：
- 用户未指定 → 默认本地 ComfyUI
- 用户指定 RH → 使用 RunningHub
- 本地 ComfyUI 不可用且用户未指定 → 告知用户，询问是否使用 RH

---

## 六、产出物

| 产出物 | 路径 |
|---|---|
| 下载的视频 | `05-workflow/epXX/红绳_EPXX_片段NN-NN_8bit.mp4` |
| timeline_data 备份 | `05-workflow/epXX/timeline_data_EPXX_rh.json` |
| 运行记录 | `05-workflow/epXX/rh_runs/`（任务ID、时间、状态） |
