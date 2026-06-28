# 计划：解析聊天记录并改编为小说，生成PDF

## 阶段 1: 解析JSON文件
- 读取 /mnt/agents/upload/conversations.json
- 提取 request 和 response 字段
- 整理对话内容，保存为结构化数据
- 输出: 解析后的对话内容文件 (conversation_extracted.md)

## 阶段 2: 小说改编创作
- 技能: general-writing（小说创作）
- 基于对话内容组织成小说
- 主角名字替换: 梅林 → 林明
- 分章节，修改逻辑错误
- 列出小说大纲
- 输出: 小说.md + 大纲.md

## 阶段 3: 生成PDF
- 技能: pdf
- 将小说内容转换为PDF文档
- 输出: 最终PDF文件

## 阶段 4: 生成多角色有声书
- 引擎: MOSS-TTS-Local-Transformer-v1.5 + OpenMOSS-Team/MOSS-Audio-Tokenizer-v2
- 脚本: 04-audiobook/scripts/generate_moss_tts_audiobook.py
- 音色: 基于角色参考音频进行 zero-shot 音色克隆
- 输出: 04-audiobook/chXX_XXX/红绳_第XX章_moss_tts.wav + .mp3 + 元数据
