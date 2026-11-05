# 默认生图工作流：本地 ComfyUI MOSS

> 用户 2026-11-05 明确指定：「**视图生图用本地 ComfyUI MOSS 工作流生成**」。
> 生成参考图 / 场景图 / 视图 / 锚点图，一律走本链路；不再用云端 RH 生图应用，也不用内置 ImageGen。

## 一、为什么切换

| 渠道 | 状态 | 原因 |
|---|---|---|
| 内置 ImageGen | 停用 | 右下角带「AI生成 WORKBUDDY」水印，需裁切；风格与成片不贴 |
| 云端 RH 生图应用 `2112991658311766017` | 停用 | 2026-11-04 连续 5 次 `805` 工作流运行失败（node62=None、plus 实例均试过），API 侧不可用 |
| **本地 ComfyUI MOSS** | **现行** | 无水印、中文提示词直出、写实建筑/人物质感与 H3 成片一致、不烧云端币 |

## 二、工作流与模型

- 工作流文件：`F:\Work-Fisher纯净包2026.8.7\ComfyUI\user\default\workflows\【WorkFisher】全能生图王 _ 适配所有类型.json`
- API 精简模板（14 节点，从历史出图 PNG 元数据还原）：`红绳/05-workflow/ep05/营救陆沉/_ripple_doc/moss_t2i_prompt_template.json`

| 节点 | 类 | 值 |
|---|---|---|
| 28 | UNETLoader | `moss_image_sft_bf16.safetensors`（省显存可用 `moss_image_sft_int8_convrot.safetensors`） |
| 41 | LoraLoaderModelOnly | `KOOK-MOSS-SFT-观澜.safetensors` @ 1.0 |
| 38 | SkipLayerGuidanceDiTSimple | `single_layers=22`, `0.0→0.5` |
| 30 | CLIPLoader | `qwen3.5_9b_int8_convrot.safetensors`, type=`moss_image` |
| 32 | VAELoader | `flux2-vae.safetensors` |
| 19 | ResolutionSelector | `16:9 (Widescreen)` / `2.0MP` / multiple 16 → 1936×1088 |
| 35 | EmptyFlux2LatentImage | 宽高接 19 |
| **57** | PrimitiveStringMultiline | **正向提示词（中文可用）** |
| 36 | CLIPTextEncode | 负向提示词 |
| 31 | KSampler | 25 步 / cfg 3.0 / `er_sde` / `simple` / denoise 1.0 |
| 37 / 9 | VAEDecode / SaveImage | `filename_prefix` 可改 |
| 63 | PrimitiveStringMultiline | 超长说明文档，**孤立无引用，提交前必须剔除**（否则请求体 100KB+） |

## 三、通用脚本

`红绳/05-workflow/scripts/gen_image_moss_local.py`

```bash
python gen_image_moss_local.py \
  --prompt-file <提示词.txt> \
  --ratio "16:9 (Widescreen)" --mp 2.0 --seed 20261105 --steps 25 \
  --prefix moss_hongsheng_xxx \
  --out "<绝对路径>/视图_v1.png"
```

- `--dry-run` 只打印最终 prompt 不提交
- `--unet` 可切 int8 版；`--lora` 可调观澜强度
- 访问 `127.0.0.1:8188` **必须绕过系统代理**（脚本内已用 `ProxyHandler({})`）
- 实测：bf16 / 2.0MP / 25 步，单张约 **90 秒**（含模型加载）

## 四、出图自检（沿用避坑手册）

1. 无水印、无文字 / 伪汉字标牌 / 数字 / logo（P15 曾出伪汉字标牌）
2. 场景空间几何是否写对：楼梯要写清折返（switchback）结构、平台、方向反转，不能只写 `stairs going DOWN`（避坑手册 J 型）
3. 人物参考图要写清发色硬设定（安娜 = 蓝黑长发，dark navy；避坑手册 E-b）
4. 参考图总数 ≤ 6 张，本场景按 2 人物 + 1 场景 = 3 张

## 五、前置条件

- ComfyUI 服务需运行（`python -u main.py --windows-standalone-build`，整合包 python；沙箱内 `Start-Process` 分离进程会被回收，用后台任务方式启动）
- 启动后核对 `WN_Ripple*` 等节点不影响本链路；本链路只依赖核心节点 + `MOSSImageControl` 扩展
