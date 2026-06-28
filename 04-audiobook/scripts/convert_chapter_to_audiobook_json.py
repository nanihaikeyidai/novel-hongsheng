#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将《红绳》成稿 Markdown 章节转换为 MOSS-TTS 有声小说 JSON。
输出字段仅保留：type / content / character。
"""

import json
import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional


NAMES = ["王老师", "陈老师", "林明", "林晓", "李想", "妈妈"]
NAME_RE = "|".join(re.escape(n) for n in NAMES)

# 名字/代词 + 说/问/道/笑/应，后接标点（最常见）
NAME_SAID_PATTERN = re.compile(f"({NAME_RE})[说道问笑应]?[，。！？]")

# 名字出现在引号后、作为动作主语，如：班主任王老师用粉笔...
NAME_ACTION_PATTERN = re.compile(f"({NAME_RE})(?:说|道|问|笑|应|喊|叫|指|写|看|望|侧头|打断|推|递|塞|跑|走|站|凑|低|叹)?")

# 代词 + 说/问/道/笑/应
PRONOUN_ME_PATTERN = re.compile(r"我[说道问笑应]")
PRONOUN_SHE_PATTERN = re.compile(r"她[说道问笑应]")
PRONOUN_HE_PATTERN = re.compile(r"他[说道问笑应]")

# 环境提示词：这类引号内容更宜作为旁白（公告、屏幕、便签等）
ENV_CUES = ["电子屏", "屏幕", "便签", "公告栏", "红纸", "纸上", "写着", "贴着", "滚动", "递到"]


def is_environment_quote(prefix: str, suffix: str) -> bool:
    """判断引号内容是否是环境文字（屏幕、便签、公告等）。"""
    return any(cue in (prefix + suffix) for cue in ENV_CUES)


def pick_female(context: str, prev_speaker: Optional[str]) -> str:
    if "妈妈" in context:
        return "妈妈"
    if "林晓" in context:
        return "林晓"
    if prev_speaker in ("林晓", "妈妈"):
        return prev_speaker
    return "林晓"


def pick_male(context: str, prev_speaker: Optional[str]) -> str:
    if "陈老师" in context:
        return "陈老师"
    if "李想" in context:
        return "李想"
    if prev_speaker in ("李想", "陈老师", "林明"):
        return prev_speaker
    return "李想"


def infer_speaker(prefix: str, suffix: str, prev_speaker: Optional[str]) -> Optional[str]:
    """根据引号前后上下文推断说话人。"""
    near_suffix = suffix[:30]
    near_prefix = prefix[-30:]
    context = (prefix + suffix)[-120:]

    # 1. 引号后显式名字/代词 + 说/问/道/笑/应
    m = NAME_SAID_PATTERN.search(near_suffix)
    if m:
        return m.group(1)
    m = NAME_SAID_PATTERN.search(near_prefix)
    if m:
        return m.group(1)

    # 2. 引号后名字作为动作主语，如“班主任王老师用粉笔...”
    m = NAME_ACTION_PATTERN.match(near_suffix)
    if m:
        return m.group(1)
    m = NAME_ACTION_PATTERN.search(near_prefix)
    if m:
        return m.group(1)

    # 3. 人称代词
    if PRONOUN_ME_PATTERN.search(near_suffix) or PRONOUN_ME_PATTERN.search(near_prefix):
        return "林明"

    if PRONOUN_SHE_PATTERN.search(near_suffix) or PRONOUN_SHE_PATTERN.search(near_prefix):
        return pick_female(context, prev_speaker)

    if PRONOUN_HE_PATTERN.search(near_suffix) or PRONOUN_HE_PATTERN.search(near_prefix):
        return pick_male(context, prev_speaker)

    # 4. 引号后紧跟“说/道/问/笑/应”，说明是连续同角色发言
    if prev_speaker and re.match(r"^[，。]?[说道问笑应]", near_suffix):
        return prev_speaker

    # 5. 前缀中有明确主语 + 动作，如“她把课本推了推：”
    if re.search(r"她(?:把|将|用|伸|侧过|凑|看|站)?[\u4e00-\u9fa5]{0,4}，?$", near_prefix):
        return pick_female(context, prev_speaker)
    if re.search(r"他(?:把|将|用|伸|侧过|凑|看|站|压|嘿嘿)?[\u4e00-\u9fa5]{0,4}，?$", near_prefix):
        return pick_male(context, prev_speaker)

    return None


def parse_paragraph(paragraph: str) -> List[Dict]:
    """把一段文本拆成 narration / dialogue 片段，段落间说话人状态不继承。"""
    fragments = []
    quote_re = re.compile(r'"([^"]+)"')
    matches = list(quote_re.finditer(paragraph))

    if not matches:
        text = paragraph.strip()
        if text:
            fragments.append({"type": "narration", "content": text, "character": None})
        return fragments

    prev_speaker: Optional[str] = None
    last_end = 0

    for m in matches:
        start, end = m.start(), m.end()
        if start > last_end:
            narration = paragraph[last_end:start].strip()
            if narration:
                fragments.append({"type": "narration", "content": narration, "character": None})

        quote_text = m.group(1).strip()
        prefix = paragraph[max(0, start - 80):start]
        suffix = paragraph[end:min(len(paragraph), end + 80)]

        speaker = infer_speaker(prefix, suffix, prev_speaker)

        # 无明确说话人且环境提示明显 -> 视为旁白
        if speaker is None and is_environment_quote(prefix, suffix):
            fragments.append({"type": "narration", "content": quote_text, "character": None})
        else:
            # 默认归为第一人称叙述者林明（内心独白等）
            if speaker is None:
                speaker = "林明"
            fragments.append({"type": "dialogue", "content": quote_text, "character": speaker})
            prev_speaker = speaker

        last_end = end

    if last_end < len(paragraph):
        tail = paragraph[last_end:].strip()
        if tail:
            fragments.append({"type": "narration", "content": tail, "character": None})

    return fragments


def merge_consecutive_narration(lines: List[Dict]) -> List[Dict]:
    """合并连续旁白，减少 TTS 行数。"""
    merged = []
    for line in lines:
        if line["type"] == "narration" and merged and merged[-1]["type"] == "narration":
            merged[-1]["content"] += "\n" + line["content"]
        else:
            merged.append(line)
    return merged


def convert_chapter(input_path: Path, title: str = "红绳") -> Dict:
    raw = input_path.read_text(encoding="utf-8")
    # 去掉 markdown 标题行
    body = re.sub(r"^#.*\n+", "", raw, count=1).strip()
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]

    lines: List[Dict] = []
    for para in paragraphs:
        lines.extend(parse_paragraph(para))

    lines = merge_consecutive_narration(lines)

    return {
        "title": title,
        "chapters": [
            {
                "chapter_number": 1,
                "chapter_title": "第一章 红绳伞",
                "lines": lines,
            }
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Convert manuscript chapter to audiobook JSON")
    parser.add_argument("--input", "-i", required=True, type=Path, help="成稿 Markdown 路径")
    parser.add_argument("--output", "-o", required=True, type=Path, help="输出 JSON 路径")
    parser.add_argument("--title", "-t", default="红绳", help="书名")
    parser.add_argument("--report", "-r", type=Path, default=None, help="可选：输出可读审阅 Markdown")
    args = parser.parse_args()

    data = convert_chapter(args.input, args.title)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已生成 {args.output}，共 {len(data['chapters'][0]['lines'])} 行")

    if args.report:
        lines = data["chapters"][0]["lines"]
        report_parts = [f"# {data['title']} - {data['chapters'][0]['chapter_title']}\n"]
        for i, line in enumerate(lines, 1):
            t = line["type"]
            c = line["content"].replace("\n", "  ")
            ch = line["character"] or ""
            if t == "dialogue":
                report_parts.append(f'{i}. **{ch}**：「{c}」\n')
            else:
                report_parts.append(f"{i}. {c}\n")
        args.report.write_text("\n".join(report_parts), encoding="utf-8")
        print(f"已生成审阅报告 {args.report}")


if __name__ == "__main__":
    main()
