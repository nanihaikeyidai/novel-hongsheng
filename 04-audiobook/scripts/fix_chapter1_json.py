#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""人工修正第一章有声小说 JSON 的角色归属与旁白/对话类型。"""

import json
from pathlib import Path


def main():
    path = Path("04-audiobook/ch01_红绳伞/红绳_第01章_有声小说.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    lines = data["chapters"][0]["lines"]

    # 1. 角色修正：index -> character
    character_fixes = {
        3: "林明",    # "为什么是我"
        5: "王老师",  # "这位是林明同学..."
        11: "王老师", # "等下午领了新教材再说。"
        13: "林晓",   # "看这边。"
        18: "陈老师", # "新来的，林明是吧？你来。"
        30: "林晓",   # "你步骤写得比老师还快。"
        31: "林明",   # "……"
        33: "林晓",   # "你以前数学很好吧？"
        38: "李想",   # "前桌林晓，我们班班花..."
        42: "李想",   # "现在没兴趣，以后不好说。"
        44: "林晓",   # "还有这个。"
        46: "林晓",   # "你先用。"
        50: "林晓",   # "嗯。"
        52: "林晓",   # "你叫林明？"
        56: "林晓",   # "你不去吃饭？"
        60: "林晓",   # "那吃点这个。下午课很长。"
        62: "林晓",   # "不是给你的。"
        64: "林晓",   # "是还你人情..."
        68: "林晓",   # "不用总谢。"
        70: "林晓",   # "你话好少。"
        72: "林晓",   # "你先拿回去看..."
        74: "林晓",   # "拿着。"
        76: "林晓",   # "我不想明天被老师问..."
        80: "林晓",   # "拿着。"
        84: "林晓",   # "明天还我。"
        89: "妈妈",   # "新学校怎么样？"
        91: "妈妈",   # "交几个朋友。"
    }
    for idx, char in character_fixes.items():
        lines[idx]["character"] = char

    # 2. 不应作为对话的引号内容 -> 改为旁白
    to_narration = {
        24: "原来如此",
        87: "林晓",
        104: "不感兴趣",
    }
    for idx, content in to_narration.items():
        lines[idx]["type"] = "narration"
        lines[idx]["content"] = content
        lines[idx]["character"] = None

    # 3. 合并连续旁白
    merged = []
    for line in lines:
        if line["type"] == "narration" and merged and merged[-1]["type"] == "narration":
            merged[-1]["content"] += "\n" + line["content"]
        else:
            merged.append(line)

    data["chapters"][0]["lines"] = merged

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已修正并保存，共 {len(merged)} 行")


if __name__ == "__main__":
    main()
