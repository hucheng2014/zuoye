import re
from typing import List, Optional, Tuple


TIMESTAMP_RE = re.compile(r"\[(\d{2}:\d{2}\.\d{3})-(\d{2}:\d{2}\.\d{3})\]")
NUMERIC_BRACKET_RE = re.compile(r"\[[^\]]+\]")
HUMAN_VOCAL_WORDS = ("呻吟", "喘息", "喘气", "呼吸声", "喊叫", "叫喊", "笑声", "咳嗽", "哭声", "感叹声", "叹息")


def _seconds(ts: str) -> float:
    minute, second = ts.split(":")
    return int(minute) * 60 + float(second)


def _ranges(caption: str) -> List[Tuple[float, float, str, str]]:
    ranges: List[Tuple[float, float, str, str]] = []
    for line in caption.splitlines():
        match = TIMESTAMP_RE.search(line)
        if not match:
            continue
        ranges.append((_seconds(match.group(1)), _seconds(match.group(2)), match.group(0), line.strip()))
    return ranges


def _block(caption: str, start_pattern: str, end_pattern: str) -> str:
    match = re.search(start_pattern + r"(.*?)(?=" + end_pattern + r"|\Z)", caption, re.S)
    return match.group(1) if match else ""


def _is_none_text(text: str) -> bool:
    return text.strip().replace(" ", "") in ("无", "")


def _effect_kind(line: str) -> str:
    has_cheer = any(word in line for word in ("欢呼", "喝彩"))
    has_applause = any(word in line for word in ("掌声", "鼓掌"))
    if has_cheer and has_applause:
        return "cheer+applause"
    if has_cheer:
        return "cheer"
    if has_applause:
        return "applause"
    return "other"


def preflight_caption(caption: str, video_duration: Optional[float] = None) -> List[str]:
    """Hard pre-submit checks for LabelX audio caption tasks."""
    errors: List[str] = []
    text = caption.strip()
    if text and not text.startswith("总体概述:"):
        errors.append("caption must start with 总体概述:")

    required = [
        "总体概述:",
        "详细描述:",
        "1. 人声:",
        "1.1 通用录音环境与质量",
        "1.2 说话/演唱人档案",
        "1.3 说话/歌词内容",
        "2. 环境音与音效:",
        "2.1 环境背景声",
        "2.2 音效",
        "3. 背景音乐",
        "4. 特殊合成音效",
    ]
    for item in required:
        if item not in text:
            errors.append(f"missing required section: {item}")

    forbidden = [
        "<顺序分析结果>",
        "<总结精炼结果>",
        "```",
        "语言种类：",
        "语言种类:",
        "风格/流派",
        "氛围/情绪",
        "2. 环境与音效",
        "1. 人声: 无",
        "视觉特征:",
    ]
    for item in forbidden:
        if item in text:
            errors.append(f"forbidden leftover text: {item}")
    for none_with_period in ("2.1 环境背景声: 无。", "2.2 音效: 无。", "4. 特殊合成音效: 无。"):
        if none_with_period in text:
            errors.append(f"use 无 without Chinese period: {none_with_period}")

    for token in NUMERIC_BRACKET_RE.findall(text):
        if re.match(r"\[\d", token) and not re.match(r"^\[\d{2}:\d{2}\.\d{3}-\d{2}:\d{2}\.\d{3}\]$", token):
            errors.append(f"bad timestamp format: {token}")

    ranges = _ranges(text)
    for start, end, token, _line in ranges:
        if start >= end:
            errors.append(f"non-positive timestamp range: {token}")
        if video_duration and end > video_duration + 0.5:
            errors.append(f"timestamp exceeds video duration {video_duration:.1f}s: {token}")
    no_vocal = re.search(r"1\.1\s*通用录音环境与质量\s*[:：]\s*无", text) is not None
    summary = text.split("详细描述:", 1)[0]
    if no_vocal and any(word in summary for word in HUMAN_VOCAL_WORDS):
        errors.append("summary mentions human vocal sounds but vocal section is marked 无")
    if no_vocal:
        for label in ("1.1 通用录音环境与质量", "1.2 说话/演唱人档案", "1.3 说话/歌词内容"):
            if not re.search(re.escape(label) + r"\s*[:：]\s*无", text):
                errors.append(f"missing no-vocal item: {label}: 无")
    else:
        vocal_block = _block(text, r"1\.\s*人声\s*[:：]", r"\n\s*2\.\s*环境音与音效\s*[:：]")
        if not re.search(r"(说话人|演唱者)\s*\d+\s*[:：]", vocal_block):
            errors.append("vocal section has no speaker/singer profile")
        if "说话人" in vocal_block:
            for item in ("视觉标识:", "年龄与性别:", "口音/方言:", "基本音色特征:", "基本响度与节奏:"):
                if item not in vocal_block:
                    errors.append(f"missing speaker field: {item}")
        if "演唱者" in vocal_block:
            for item in ("视觉标识:", "年龄与性别:", "基本音色特征:", "基本响度:", "演唱节奏:", "演唱风格:", "歌唱技巧与表现力:"):
                if item not in vocal_block:
                    errors.append(f"missing singer field: {item}")
        for item in ("整体声音质量:", "声学环境:"):
            if item not in vocal_block:
                errors.append(f"missing vocal recording field: {item}")
        vocal_content = _block(text, r"1\.3\s*说话/歌词内容\s*[:：]", r"\n\s*2\.\s*环境音与音效\s*[:：]")
        vocal_ranges = _ranges(vocal_content)
        if not vocal_ranges:
            errors.append("vocal content needs at least one timestamped speech/singing line")
        pending_timestamp = ""
        for line in [line.strip() for line in vocal_content.splitlines() if line.strip()]:
            if TIMESTAMP_RE.search(line):
                if pending_timestamp:
                    errors.append(f"vocal timestamp line missing following 情感: {pending_timestamp}")
                pending_timestamp = line
                continue
            if line.startswith("情感:"):
                if not pending_timestamp:
                    errors.append(f"orphan 情感 line without preceding timestamp: {line}")
                pending_timestamp = ""
        if pending_timestamp:
            errors.append(f"vocal timestamp line missing following 情感: {pending_timestamp}")
        for left, right in zip(vocal_ranges, vocal_ranges[1:]):
            if right[0] < left[0] - 0.05:
                errors.append(f"vocal timestamps are out of chronological order: {left[2]} before {right[2]}")

    bgm_match = re.search(r"3\.\s*背景音乐\s*[:：](.*?)(?=\n\s*4\.\s*特殊合成音效\s*[:：]|\Z)", text, re.S)
    if bgm_match:
        bgm_text = bgm_match.group(1).strip()
        if not bgm_text:
            errors.append("BGM section is empty")
        if bgm_text and bgm_text != "无":
            for item in ("音量:", "乐器:", "节奏与速度:", "录音质量与制作手法:", "旋律与和声:", "风格流派:", "氛围情绪:", "作用:"):
                field = re.search(re.escape(item) + r"\s*(.*)", bgm_text)
                value = field.group(1).strip() if field else ""
                if not value:
                    errors.append(f"missing BGM field: {item}")
                elif value in ("无", "...", "待补充", "未知"):
                    errors.append(f"BGM field has placeholder value: {item}")

    effect_match = re.search(r"2\.2\s*音效\s*[:：](.*?)(?=\n\s*3\.\s*背景音乐\s*[:：]|\Z)", text, re.S)
    if effect_match:
        effect_text = effect_match.group(1)
        compact_effect = effect_text.replace(" ", "")
        merged_patterns = [
            r"欢呼声?(和|与|及|、|并伴有|伴随)掌声",
            r"掌声(和|与|及|、|并伴有|伴随)欢呼声?",
            r"鼓掌声?(和|与|及|、|并伴有|伴随)欢呼声?",
            r"欢呼声?(和|与|及|、|并伴有|伴随)鼓掌声?",
        ]
        for pattern in merged_patterns:
            if re.search(pattern, compact_effect):
                errors.append("merged applause/cheering phrase in 2.2")
                break

        effect_lines = [line.strip() for line in effect_text.splitlines() if line.strip()]
        inline_effect = effect_text.strip()
        if inline_effect and inline_effect != "无" and not TIMESTAMP_RE.search(effect_text):
            errors.append("2.2 sound effects need timestamped lines or explicit 无")

        parsed_effects: List[Tuple[float, float, str, str]] = []
        for line in effect_lines:
            if line == "无":
                continue
            match = TIMESTAMP_RE.search(line)
            if not match:
                errors.append(f"effect line missing timestamp: {line}")
                continue
            if not line.endswith("。"):
                errors.append(f"effect line must end with Chinese period: {line}")
            if any(word in line for word in HUMAN_VOCAL_WORDS):
                errors.append(f"human vocal sound should be in 1.3, not 2.2: {line}")
            kind = _effect_kind(line)
            if kind == "cheer+applause":
                errors.append(f"applause and cheering must be separate lines: {line}")
            parsed_effects.append((_seconds(match.group(1)), _seconds(match.group(2)), kind, line))

        for i, left in enumerate(parsed_effects):
            for right in parsed_effects[i + 1:]:
                ls, le, lk, ll = left
                rs, re_, rk, rl = right
                if lk not in ("cheer", "applause") or rk not in ("cheer", "applause"):
                    continue
                overlap = min(le, re_) - max(ls, rs)
                same_range = abs(ls - rs) < 0.05 and abs(le - re_) < 0.05
                if overlap > 0 and not same_range:
                    errors.append(f"overlapping applause/cheering should use full independent ranges: {ll} | {rl}")
                    break

    return errors


def print_preflight_report(errors: List[str]) -> None:
    print("===== 提交前硬校验 =====")
    if errors:
        for error in errors:
            print(f"  [FAIL] {error}")
    else:
        print("  [OK] hard checks passed")
    print("======================")
