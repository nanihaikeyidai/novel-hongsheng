# 《红绳》项目

本目录存放小说《红绳》从原始素材到成品有声书的全部项目文件。

## 目录结构

| 目录 | 说明 |
|---|---|
| `00-source/` | 原始素材：聊天记录导出、历史备份、行号转储等 |
| `01-docs/` | 项目文档：大纲、人物设定、需求、计划、剧情流程图 |
| `02-manuscript/` | 成稿：章节正文（chapters/）、PDF、HTML |
| `03-intermediate/` | 中间稿 / 早期试写：20260625-红绳 阶段的草稿与试做 |
| `04-audiobook/` | 有声书工程：MOSS-TTS 生成脚本、参考音色、章节音频 |

## 常用入口

- **成稿阅读**：`02-manuscript/红绳.pdf` 或 `02-manuscript/红绳.html`
- **章节 Markdown**：`02-manuscript/chapters/`
- **有声书生成**：
  ```cmd
  cd D:\HermesWorkspace\ai小说\红绳\04-audiobook
  D:\HermesWorkspace\MOSS-TTS\.venv\Scripts\python.exe scripts\generate_moss_tts_audiobook.py
  ```
  详见 `04-audiobook/README_moss_tts.md`。

## 项目外通用资源

与《红绳》无关或跨项目通用的技能和模板已移到 `ai小说/` 根目录：

- `skills/chinese-novelist-skill/`
- `skills/novel-to-audiobook-skill/`
- `templates/小说转有声剧本模板.txt`
- `archive/古风穿越小说大纲/`
