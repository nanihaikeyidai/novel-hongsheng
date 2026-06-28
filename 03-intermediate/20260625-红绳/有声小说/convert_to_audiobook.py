#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《红绳》第01章 有声小说格式转换脚本
基于 novel-to-audiobook-skill 规范生成结构化剧本
"""

import os
import re
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Literal
from enum import Enum


class EmotionTag(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEAR = "fear"
    SURPRISE = "surprise"
    EXCITED = "excited"
    CALM = "calm"
    WORRIED = "worried"
    COLD = "cold"
    GENTLE = "gentle"
    FIERCE = "fierce"
    MOCKING = "mocking"
    DESPERATE = "desperate"
    HOPEFUL = "hopeful"
    MYSTERIOUS = "mysterious"


@dataclass
class VoiceProfile:
    character_name: str
    voice_description: str
    default_emotion: EmotionTag = EmotionTag.NEUTRAL
    reference_audio_path: Optional[str] = None
    reference_text: Optional[str] = None
    speed_factor: float = 1.0


@dataclass
class ScriptLine:
    line_type: Literal["narration", "dialogue"]
    content: str
    character: Optional[str] = None
    emotion: EmotionTag = EmotionTag.NEUTRAL
    context_hint: str = ""

    def to_dict(self) -> dict:
        return {
            "type": self.line_type,
            "content": self.content,
            "character": self.character,
            "emotion": self.emotion.value,
            "context_hint": self.context_hint,
        }


@dataclass
class Chapter:
    chapter_number: int
    title: str
    lines: List[ScriptLine] = field(default_factory=list)

    @property
    def word_count(self) -> int:
        return sum(len(line.content) for line in self.lines)

    def to_dict(self) -> dict:
        return {
            "chapter_number": self.chapter_number,
            "title": self.title,
            "word_count": self.word_count,
            "lines": [line.to_dict() for line in self.lines],
        }


@dataclass
class AudiobookProject:
    title: str
    author: str
    chapters: List[Chapter] = field(default_factory=list)
    character_profiles: Dict[str, VoiceProfile] = field(default_factory=dict)
    output_dir: str = "./audiobook_output"

    @property
    def total_word_count(self) -> int:
        return sum(c.word_count for c in self.chapters)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "author": self.author,
            "total_chapters": len(self.chapters),
            "total_word_count": self.total_word_count,
            "characters": {
                k: {
                    "character_name": v.character_name,
                    "voice_description": v.voice_description,
                    "default_emotion": v.default_emotion.value,
                    "speed_factor": v.speed_factor,
                    "reference_audio_path": v.reference_audio_path,
                    "reference_text": v.reference_text,
                }
                for k, v in self.character_profiles.items()
            },
            "chapters": [c.to_dict() for c in self.chapters],
        }


# 情绪线索词库
EMOTION_CUES = {
    "happy": ["笑", "开心", "高兴", "喜悦", "兴奋", "欢呼", "眉开眼笑", "喜笑颜开"],
    "sad": ["哭", "泪", "悲伤", "难过", "伤心", "哽咽", "抽泣", "哀叹", "黯然", "垂泪", "痛苦"],
    "angry": ["怒", "生气", "愤怒", "恼火", "咆哮", "怒吼", "咬牙切齿", "拍桌", "瞪眼"],
    "fear": ["怕", "恐惧", "惊恐", "颤抖", "哆嗦", "后退", "脸色发白", "冷汗", "尖叫"],
    "surprise": ["惊", "惊讶", "震惊", "意外", "愣住", "瞪大眼睛", "倒吸一口凉气"],
    "worried": ["忧", "担心", "焦虑", "不安", "皱眉", "踱步", "叹气", "愁眉"],
    "cold": ["冷", "冷漠", "淡然", "面无表情", "冷笑", "不屑", "轻蔑", "冷淡"],
    "gentle": ["柔", "温柔", "轻声", "柔和", "温暖", "慈爱", "宠溺"],
    "fierce": ["狠", "凶狠", "严厉", "冷酷", "杀气", "凌厉"],
    "mocking": ["嘲", "嘲讽", "戏谑", "讥笑", "冷笑", "揶揄", "调侃"],
    "desperate": ["绝望", "崩溃", "无助", "瘫坐", "万念俱灰", "心如死灰"],
    "hopeful": ["希望", "期待", "憧憬", "向往", "曙光", "信心", "坚定"],
    "mysterious": ["神秘", "诡异", "阴森", "莫测", "幽深", "低沉"],
}


def infer_emotion(text: str, context: str = "", is_narration: bool = True) -> EmotionTag:
    """基于文本和上下文推断情绪"""
    combined = text + context
    scores = {tag: 0 for tag in EmotionTag}

    for emotion_key, cues in EMOTION_CUES.items():
        tag = EmotionTag(emotion_key)
        for cue in cues:
            scores[tag] += combined.count(cue) * 2

    if "！" in text or "!" in text:
        scores[EmotionTag.ANGRY] += 1
        scores[EmotionTag.EXCITED] += 1
        scores[EmotionTag.SURPRISE] += 1
    if "？" in text or "?" in text:
        scores[EmotionTag.SURPRISE] += 1
        scores[EmotionTag.WORRIED] += 1
    if "……" in text or "..." in text:
        scores[EmotionTag.SAD] += 1
        scores[EmotionTag.WORRIED] += 1

    if is_narration:
        scores[EmotionTag.NEUTRAL] += 2

    best_tag = max(scores, key=scores.get)
    return best_tag if scores[best_tag] > 0 else EmotionTag.NEUTRAL


def split_narration(text: str) -> List[str]:
    """将旁白长句拆分为短句（单句不超过25字）"""
    # 先按句号、问号、感叹号分句
    sentences = re.split(r'([。！？；])', text)
    result = []
    current = ""

    for part in sentences:
        if not part:
            continue
        if part in "。！？；":
            current += part
            if current.strip():
                result.append(current.strip())
            current = ""
        else:
            # 按逗号进一步拆分长句
            subs = part.split('，')
            for sub in subs:
                sub = sub.strip()
                if not sub:
                    continue
                if len(current) + len(sub) + 1 <= 25:
                    current = (current + "，" + sub).strip("，")
                else:
                    if current.strip():
                        result.append(current.strip())
                    current = sub

    if current.strip():
        result.append(current.strip())

    return [r for r in result if r]


def extract_dialogues(paragraph: str) -> List[Dict]:
    """提取段落中的对话和旁白片段，并记录对话前后上下文"""
    # 匹配中文引号 "..." 内的内容
    pattern = re.compile(r'"([^"]+)"')
    matches = list(pattern.finditer(paragraph))

    if not matches:
        return [{"type": "narration", "text": paragraph}]

    fragments = []
    last_end = 0
    for m in matches:
        start, end = m.start(), m.end()
        if start > last_end:
            fragments.append({"type": "narration", "text": paragraph[last_end:start]})
        # 取对话前后最多80个字符作为上下文
        prefix = paragraph[max(0, start - 80):start]
        suffix = paragraph[end:min(len(paragraph), end + 80)]
        fragments.append({
            "type": "dialogue",
            "text": m.group(1),
            "full": m.group(0),
            "prefix": prefix,
            "suffix": suffix,
            "start_pos": start,
            "end_pos": end
        })
        last_end = end
    if last_end < len(paragraph):
        fragments.append({"type": "narration", "text": paragraph[last_end:]})

    return fragments


def infer_speaker_from_context(prefix: str, suffix: str, text: str, prev_speaker: Optional[str]) -> str:
    """
    基于对话前后上下文推断说话人。
    使用关键词得分 + 上下文规则。
    """
    context = prefix + suffix
    # 1. 明确前缀中的角色名（如“李想压低声音说”）
    speaker_patterns = [
        r'([\u4e00-\u9fa5]{1,6})(?:说|道|喊|叫|问|答|喃喃|冷笑|怒喝|轻笑|低声|高声|急道|忙道|叹道|笑道|哭道|骂道|吼道)',
        r'([\u4e00-\u9fa5]{1,6})[：:]',
    ]
    for pattern in speaker_patterns:
        m = re.search(pattern, prefix)
        if m:
            name = m.group(1)
            if name in ["林明", "林晓", "李想", "王老师"]:
                return name

    # 特殊台词直接判断（不依赖关键词得分）
    if text in ["林明", "林明。", "林明？"]:
        if "林晓" in suffix:
            return "林晓"
        if "王老师" in context or "讲台上" in context or "站在过道里" in context:
            return "王老师"
        # 默认王老师（老师点名场景更常见）
        return "王老师"
    if text in ["拿着", "拿着。"] and ("又重复" in context or "塞进我手里" in context):
        return "林晓"
    if "从高一入学就戴着" in text or "从来不摘" in text:
        if "李想" in context:
            return "李想"

    # 2. 基于台词内容的关键词得分
    character_cues = {
        "林晓": ["你拿着", "明天还我", "雨太大", "伞上的装饰", "看错了", "旧了，别介意", "旧了", "拿着"],
        "李想": ["我靠", "真的假的", "哎，新来的", "我叫李想", "你同桌", "你从临川来啊", "临川是不是在北方",
                 "听说那边冬天会下雪", "我这辈子还没见过雪", "那你是不是会滑雪", "哦。", "刚才去厕所",
                 "学习贼好", "就是性格有点闷", "你别介意", "她手腕上那根红绳", "有人问过她", "从高一入学就戴着", "从来不摘"],
        "王老师": ["林明？", "进来吧", "这是新转来的", "从临川过来", "希望大家多帮助",
                   "第三排靠窗", "你先坐那儿", "同学们", "把暑假作业拿出来", "课代表收一下",
                   "你的暑假作业呢", "空位", "新转来"],
        "林明": ["我淋雨", "淋雨而已", "淋雨回去", "不用", "我之前在临川", "班主任说", "我不喜欢欠", "没兴趣", "不知道", "谢谢"],
    }

    scores = {"林明": 0, "林晓": 0, "李想": 0, "王老师": 0}
    for char, cues in character_cues.items():
        for cue in cues:
            if cue in text:
                scores[char] += 1

    # 林明的典型简短回应（排除其他角色关键词后）
    lin_ming_short = ["是。", "嗯。", "会。", "不会。", "不用。", "谢谢。", "不知道。", "没兴趣。", "算了。", "不用"]
    if text in lin_ming_short:
        scores["林明"] += 3

    # 选择得分最高者
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best

    # 3. 基于前后上下文推断
    if "王老师" in context or "讲台上" in context or "拍了拍讲台" in context or "站在过道里" in context:
        # 但如果 suffix 明确出现林晓，则优先林晓（如林晓在背后叫林明）
        if text in ["林明", "林明。", "林明？"] and "林晓" in suffix:
            return "林晓"
        return "王老师"
    if "李想" in context or "圆脸" in context or "黑框眼镜" in context or "自来熟" in context:
        return "李想"
    if "林晓" in context or "前座" in context or "那个女生" in context:
        # 林晓叫林明的场景
        if text in ["林明", "林明。", "林明？"]:
            return "林晓"
        # 林晓把伞塞给林明后重复"拿着"
        if text in ["拿着", "拿着。", "你拿着"] and ("塞进我手里" in context or "又重复" in context):
            return "林晓"
        return "林晓"

    # 4. 交替规则：他人提问/说话后的简短回应，通常是林明
    if prev_speaker in ["王老师", "李想", "林晓"] and len(text) <= 30:
        return "林明"

    return prev_speaker if prev_speaker else "林明"


def parse_chapter(text: str, chapter_num: int, title: str) -> Chapter:
    """解析单章为剧本"""
    chapter = Chapter(chapter_number=chapter_num, title=title)

    # 去掉标题行
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines and lines[0].startswith('#'):
        lines = lines[1:]

    # 先把所有段落拼成完整文本，便于跨段落提取上下文
    full_text = '\n'.join(lines)
    all_fragments = extract_dialogues(full_text)

    prev_speaker = None

    for frag in all_fragments:
        if frag["type"] == "narration":
            # 旁白按段落拆分
            narration_paragraphs = [p.strip() for p in frag["text"].split('\n') if p.strip()]
            for para in narration_paragraphs:
                short_sentences = split_narration(para)
                for sent in short_sentences:
                    if not sent.strip():
                        continue
                    emotion = infer_emotion(sent, is_narration=True)
                    # 林明第一人称旁白，仅在明显表达疏离/疲惫时标为 cold
                    cold_cues = ["不想", "不愿", "没兴趣", "无所谓", "累了", "厌烦", "冷淡", "冷漠", "淡然", "空洞"]
                    if any(w in sent for w in cold_cues):
                        emotion = EmotionTag.COLD
                    chapter.lines.append(ScriptLine(
                        line_type="narration",
                        content=sent,
                        emotion=emotion,
                        context_hint="林明第一人称视角，克制冷淡"
                    ))
        else:
            # 对话
            dialogue_text = frag["text"].strip()
            speaker = infer_speaker_from_context(
                frag.get("prefix", ""), frag.get("suffix", ""), dialogue_text, prev_speaker
            )
            prev_speaker = speaker
            emotion = infer_emotion(dialogue_text, frag.get("prefix", ""), is_narration=False)

            # 特殊处理：基于角色和语境修正情绪
            if speaker == "林明":
                if any(k in dialogue_text for k in ["不用", "没兴趣", "不知道", "我不会", "嗯。", "是。", "会。", "不会。"]):
                    emotion = EmotionTag.COLD
                elif "这红绳" in dialogue_text:
                    emotion = EmotionTag.SURPRISE
            elif speaker == "林晓":
                if any(k in dialogue_text for k in ["你拿着", "明天还我", "拿着"]):
                    emotion = EmotionTag.GENTLE
                elif "看错了" in dialogue_text or "雨太大" in dialogue_text:
                    emotion = EmotionTag.SAD
            elif speaker == "李想":
                if "我靠" in dialogue_text or "真的假的" in dialogue_text:
                    emotion = EmotionTag.EXCITED
                elif "从高一入学" in dialogue_text or "有人问过她" in dialogue_text or "神神秘秘" in frag.get("prefix", ""):
                    emotion = EmotionTag.MYSTERIOUS
                elif "是不是" in dialogue_text or "你见过" in dialogue_text or "那你是不是" in dialogue_text:
                    emotion = EmotionTag.SURPRISE
            elif speaker == "王老师":
                if dialogue_text in ["林明？", "林明。", "林明"] or "暑假作业" in dialogue_text or "空位" in dialogue_text or "希望" in dialogue_text:
                    emotion = EmotionTag.NEUTRAL

            chapter.lines.append(ScriptLine(
                line_type="dialogue",
                content=dialogue_text,
                character=speaker,
                emotion=emotion,
                context_hint=frag.get("prefix", "")
            ))

    return chapter


def create_project(chapter: Chapter) -> AudiobookProject:
    """创建有声小说项目，配置角色声音"""
    project = AudiobookProject(
        title="红绳",
        author="未署名",
        chapters=[chapter],
        output_dir="./audiobook_output"
    )

    project.character_profiles = {
        "旁白": VoiceProfile(
            character_name="旁白",
            voice_description="成年男性叙述者，声音沉稳清晰，带有克制的讲述感，语速中等偏慢",
            default_emotion=EmotionTag.NEUTRAL,
            speed_factor=0.95,
        ),
        "林明": VoiceProfile(
            character_name="林明",
            voice_description="十七岁青年男性，音色略低带哑，语气冷淡疏离，话少，语速偏慢",
            default_emotion=EmotionTag.COLD,
            speed_factor=0.9,
        ),
        "林晓": VoiceProfile(
            character_name="林晓",
            voice_description="十七岁青年女性，声音轻柔干净，说话克制隐忍，尾音微微发颤",
            default_emotion=EmotionTag.GENTLE,
            speed_factor=0.9,
        ),
        "李想": VoiceProfile(
            character_name="李想",
            voice_description="十七岁青年男性，声音明亮活泼，语速稍快，带着自来熟的热情",
            default_emotion=EmotionTag.HAPPY,
            speed_factor=1.1,
        ),
        "王老师": VoiceProfile(
            character_name="王老师",
            voice_description="中年女性教师，声音平稳严肃，不带太多情绪起伏",
            default_emotion=EmotionTag.NEUTRAL,
            speed_factor=0.95,
        ),
    }

    return project


def export_json(project: AudiobookProject, path: str):
    """导出JSON格式"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)


def export_markdown(project: AudiobookProject, path: str):
    """导出Markdown格式"""
    lines = []
    lines.append(f"# 《{project.title}》有声小说剧本")
    lines.append(f"**作者：** {project.author}")
    lines.append(f"**总章节：** {len(project.chapters)}章")
    lines.append(f"**总字数：** {project.total_word_count}字")
    lines.append("")
    lines.append("## 角色声音配置表")
    lines.append("")
    lines.append("| 角色 | 音色描述 | 默认情绪 | 语速 |")
    lines.append("|------|----------|----------|------|")
    for name, profile in project.character_profiles.items():
        lines.append(
            f"| {name} | {profile.voice_description} | {profile.default_emotion.value} | {profile.speed_factor}x |"
        )
    lines.append("")

    for chapter in project.chapters:
        lines.append(f"## 第{chapter.chapter_number}章：{chapter.title}")
        lines.append(f"*字数：{chapter.word_count}*")
        lines.append("")
        for line in chapter.lines:
            if line.line_type == "narration":
                lines.append(f"📖 **[旁白]** *{line.emotion.value}*  {line.content}")
            else:
                char = line.character or "未知角色"
                lines.append(f"🎭 **[{char}]** *{line.emotion.value}*  「{line.content}」")
        lines.append("")

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def export_agent_prompt(project: AudiobookProject, path: str):
    """导出Agent提示词格式"""
    lines = []
    lines.append("=== 有声小说生成指令 ===")
    lines.append(f"作品：《{project.title}》")
    lines.append(f"作者：{project.author}")
    lines.append("")
    lines.append("【角色配置】")
    for name, profile in project.character_profiles.items():
        lines.append(f"角色「{name}」:")
        lines.append(f"  - 音色：{profile.voice_description}")
        lines.append(f"  - 默认情绪：{profile.default_emotion.value}")
        lines.append(f"  - 语速：{profile.speed_factor}x")
        lines.append("")

    lines.append("【生成规则】")
    lines.append("1. 旁白使用叙述语气，按标注情绪生成")
    lines.append("2. 对话严格按标注情绪生成")
    lines.append("3. 同角色连续对话保持音色一致")
    lines.append("4. 章节间插入1秒静音")
    lines.append("5. 单句旁白控制在25字以内，保持呼吸感")
    lines.append("")
    lines.append("【章节内容】")

    for chapter in project.chapters:
        lines.append(f"\n--- 第{chapter.chapter_number}章：{chapter.title} ---")
        for line in chapter.lines:
            if line.line_type == "narration":
                lines.append(f"[NARRATION|emotion={line.emotion.value}] {line.content}")
            else:
                char = line.character or "未知"
                lines.append(f"[DIALOGUE|character={char}|emotion={line.emotion.value}] {line.content}")

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def export_voxcpm(project: AudiobookProject, path: str):
    """导出VoxCPM2指令格式"""
    emotion_desc = {
        EmotionTag.NEUTRAL: "平静的语气",
        EmotionTag.HAPPY: "开心的语气，带着微笑",
        EmotionTag.SAD: "悲伤低沉的语气",
        EmotionTag.ANGRY: "愤怒激动的语气",
        EmotionTag.FEAR: "恐惧紧张的语气，声音微颤",
        EmotionTag.SURPRISE: "惊讶的语气，语调上扬",
        EmotionTag.EXCITED: "兴奋激动的语气",
        EmotionTag.CALM: "沉稳冷静的语气",
        EmotionTag.WORRIED: "担忧焦虑的语气",
        EmotionTag.COLD: "冷漠淡然的语气",
        EmotionTag.GENTLE: "温柔柔和的语气",
        EmotionTag.FIERCE: "凶狠严厉的语气",
        EmotionTag.MOCKING: "嘲讽戏谑的语气",
        EmotionTag.DESPERATE: "绝望无助的语气",
        EmotionTag.HOPEFUL: "充满希望的语气",
        EmotionTag.MYSTERIOUS: "神秘诡异的语气",
    }

    instructions = []
    for chapter in project.chapters:
        for line in chapter.lines:
            if line.line_type == "narration":
                profile = project.character_profiles.get("旁白")
            else:
                profile = project.character_profiles.get(
                    line.character or "未知",
                    project.character_profiles.get("旁白")
                )

            desc = f"({profile.voice_description}, {emotion_desc[line.emotion]})"
            if profile.speed_factor != 1.0:
                speed_word = "稍快" if profile.speed_factor > 1.0 else "稍慢"
                desc = desc.replace(")", f", {speed_word})")

            instructions.append({
                "chapter": chapter.chapter_number,
                "type": line.line_type,
                "character": line.character,
                "emotion": line.emotion.value,
                "voxcpm_prompt": f"{desc}{line.content}",
                "raw_text": line.content,
            })

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(instructions, f, ensure_ascii=False, indent=2)


def export_qwen_tts(project: AudiobookProject, path: str):
    """导出Qwen-TTS适配JSON格式（role_list + juben）"""
    # 收集每个角色的台词，选择最有代表性的一句
    character_lines = {}
    for chapter in project.chapters:
        for line in chapter.lines:
            if line.line_type == "dialogue" and line.character:
                if line.character not in character_lines:
                    character_lines[line.character] = []
                character_lines[line.character].append(line.content)

    # 为每个角色选择代表性样本
    preferred_samples = {
        "旁白": "青屿的雨季总是这样，不讲道理。",
        "林明": "不用。我淋雨回去就行。",
        "林晓": "你拿着。明天还我就行。",
        "李想": "哎，新来的。我叫李想，你同桌。",
        "王老师": "这是新转来的林明同学，从临川过来。",
    }

    role_list = []
    for name, profile in project.character_profiles.items():
        sample = preferred_samples.get(name)
        if not sample and name in character_lines:
            # 选择最长的一句作为样本
            sample = max(character_lines[name], key=len)
        if not sample:
            sample = "你好"
        # 截取5-20字作为样本
        if len(sample) > 20:
            sample = sample[:20]
        role_list.append({
            "name": name,
            "instruct": profile.voice_description,
            "text": sample
        })

    juben_lines = []
    for chapter in project.chapters:
        for line in chapter.lines:
            if line.line_type == "narration":
                juben_lines.append(f"旁白:{line.content}")
            else:
                juben_lines.append(f"{line.character or '未知'}:{line.content}")

    data = {
        "role_list": role_list,
        "juben": "\n".join(juben_lines)
    }

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    novel_path = os.path.join(base_dir, "..", "第01章-红绳伞.md")

    with open(novel_path, 'r', encoding='utf-8') as f:
        text = f.read()

    chapter = parse_chapter(text, chapter_num=1, title="红绳伞")
    project = create_project(chapter)

    # 导出多种格式
    export_json(project, os.path.join(base_dir, "红绳_第01章_有声小说.json"))
    export_markdown(project, os.path.join(base_dir, "红绳_第01章_有声小说.md"))
    export_agent_prompt(project, os.path.join(base_dir, "红绳_第01章_代理提示词.txt"))
    export_voxcpm(project, os.path.join(base_dir, "红绳_第01章_VoxCPM指令.json"))
    export_qwen_tts(project, os.path.join(base_dir, "红绳_第01章_QwenTTS.json"))

    print(f"转换完成：{chapter.word_count}字，{len(chapter.lines)}行")
    print(f"输出目录：{base_dir}")


if __name__ == "__main__":
    main()
