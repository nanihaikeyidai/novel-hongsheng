# RH 提交记录（2026-10-25 Asia/Shanghai）

工作流 API `2084788947984666625` / 工作流 `2096059277453643778`  
脚本：`05-workflow/scripts/run_ep05_rescue_rh_director.py`

## 成功

| 单元 | taskId | 状态 | 本地下载（用户机） |
|---|---|---|---|
| P01a | 2114283413979750401 | SUCCESS | `05-workflow/ep05/营救陆沉/红绳片段01/片段01_P01a_云端草稿.mp4`（~4.99MB） |
| P01b | 2114283464705671170 | SUCCESS | `…/片段01_P01b_云端草稿.mp4`（~3.92MB） |

## 未成功（本轮）

| 单元 | 原因 |
|---|---|
| P02 | 先 errorCode 421 queue limit；后 ConnectionReset/ProxyError |
| P03 | 同上 421，后网络中断 |
| P04a / P04b / P05a / P05b | 本轮未再提交（避让队列与网络） |

素材上传缓存：`营救陆沉/制作文档/rh_upload_cache.json`（用户机）

重试：
```bat
cd /d D:\HermesWorkspace\ai小说\红绳
python 05-workflow\scripts\run_ep05_rescue_rh_director.py --unit P02 --poll
python 05-workflow\scripts\run_ep05_rescue_rh_director.py --unit all05 --poll
```
