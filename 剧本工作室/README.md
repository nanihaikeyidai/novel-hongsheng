# 《红绳》剧本工作室（ep06 起）

从第 6 集起的**唯一剧本维护入口**。不改动 `02-manuscript/screenplays` 与 `05-workflow` 里已有成片材料。

## 目录

```
剧本工作室/
  README.md
  项目.md              # 设定 + 事实/假设 + 分集总纲（一个文件）
  episodes/
    ep06.md            # 地下车库（蓝隼战）
    ep07.md            # 陆沉回社（草稿）
  preview/
    index.html         # 可交互预览（内嵌 episodes 数据）
    sync.py            # 改 md 后跑一次，刷新内嵌
```

## 怎么改一集

1. 只改 `episodes/epXX.md`（豆包格式：场次表头 / △ / 角色：台词 / 【表演附注】）。
2. 事实/集号/能力口径先改 `项目.md`。
3. 跑：`python3 preview/sync.py`
4. 用浏览器打开 `preview/index.html`。

版本用 git 或文件内「修订记录」；不要另存 `_r1` 副本，除非明确要归档。不要另增大纲 JSON。

## 命名

- 集文件：`ep06.md`、`ep07.md`…
- 场次表头：`6-1a 场景名 时间 内外`（同场分段用 a/b）
- 旧 screenplays（ep01–05）只作历史参考，本工作室不覆盖。

## 预览能力

选集 · 全文/仅台词/分场表 · 按角色过滤 · 点场次跳转 · 搜关键字 · 表演附注可折叠。
