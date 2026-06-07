import re


def normalize_time(t_str: str) -> str:
    parts = t_str.strip().split(":")
    try:
        if len(parts) == 1:
            total_ms = int(round(float(parts[0]) * 1000))
        elif len(parts) == 2:
            total_ms = (int(parts[0]) * 60 * 1000) + int(round(float(parts[1]) * 1000))
        elif len(parts) == 3:
            last = parts[2]
            if "." not in last and (len(last) == 3 or int(last) >= 60):
                total_ms = (
                    int(parts[0]) * 60 * 1000
                    + int(parts[1]) * 1000
                    + int(last.ljust(3, "0")[:3])
                )
            else:
                total_ms = (
                    int(parts[0]) * 3600 * 1000
                    + int(parts[1]) * 60 * 1000
                    + int(round(float(last) * 1000))
                )
        else:
            return t_str
        total_seconds, ms = divmod(total_ms, 1000)
        h, remainder = divmod(total_seconds, 3600)
        m, s = divmod(remainder, 60)
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
    except ValueError:
        return t_str


def is_plain_none(value: str) -> bool:
    return value.strip().replace(" ", "").strip("。.") == "无"


def split_inline_recording_fields(value: str) -> dict[str, str]:
    text = value.strip()
    fields: dict[str, str] = {}
    if not text or is_plain_none(text):
        return fields

    for key in ("整体声音质量", "声学环境"):
        match = re.search(
            rf"{key}\s*[:：]\s*(.*?)(?=(?:整体声音质量|声学环境)\s*[:：]|$)",
            text,
        )
        if match:
            fields[key] = match.group(1).strip(" 。；;") + "。"
    if fields:
        return fields

    sentences = [part.strip() for part in re.split(r"(?<=[。；;])", text) if part.strip()]
    if not sentences:
        sentences = [text]

    quality_parts = []
    environment_parts = []
    environment_keywords = ("环境", "室内", "室外", "混响", "回声", "干声", "噪", "背景", "空间", "厨房", "街道", "车内")
    quality_keywords = ("清晰", "高保真", "失真", "音质", "录音", "人声突出", "音量", "响度", "可懂")
    for sentence in sentences:
        is_environment_sentence = sentence.startswith("声学环境") or any(word in sentence for word in environment_keywords)
        if is_environment_sentence:
            environment_parts.append(sentence)
        if not sentence.startswith("声学环境") and any(word in sentence for word in quality_keywords):
            quality_parts.append(sentence)

    if quality_parts:
        fields["整体声音质量"] = "".join(quality_parts).strip()
    if environment_parts:
        fields["声学环境"] = "".join(environment_parts).strip()
    if "整体声音质量" not in fields:
        fields["整体声音质量"] = text
    if "声学环境" not in fields:
        fields["声学环境"] = text
    return fields


def format_caption(text: str) -> str:
    lines = [line.strip() for line in text.split("\n")]
    filtered_lines = []
    for line in lines:
        if not line:
            continue
        if line.startswith("```") or line.startswith("语言种类"):
            continue
        filtered_lines.append(line)

    current_section = None
    current_subsection = None
    has_speaker = any(re.match(r"^(说话人|演唱者)\s*\d+", line) for line in filtered_lines)
    has_explicit_none = any(
        re.match(r"^1\.\s*人声\s*[:：]\s*无[。.]?\s*$", line) for line in filtered_lines
    )
    has_vocal = has_speaker and not has_explicit_none

    summary = ""
    vocal_1_1: dict[str, str] = {}
    vocal_1_2: list[dict[str, object]] = []
    vocal_1_3: list[str] = []
    effects_2_1 = ""
    effects_2_2_lines: list[str] = []
    bgm_fields: dict[str, str] = {}
    bgm_lines: list[str] = []
    bgm_none = False
    special_effects_lines: list[str] = []
    special_none = False

    for line in filtered_lines:
        line = line.replace("**", "")

        if re.match(r"^总体概述:", line):
            summary = line.split(":", 1)[1].strip()
            continue
        if re.match(r"^详细描述:", line):
            continue
        if re.match(r"^1\.\s*人声:", line):
            current_section = "vocal"
            current_subsection = None
            val = line.split(":", 1)[1].strip() if ":" in line else ""
            if is_plain_none(val):
                has_vocal = False
            continue
        if re.match(r"^1\.1", line):
            current_subsection = "1.1"
            val = ""
            if ":" in line:
                val = line.split(":", 1)[1].strip()
            elif "：" in line:
                val = line.split("：", 1)[1].strip()
            if is_plain_none(val):
                has_vocal = False
            elif val:
                vocal_1_1.update(split_inline_recording_fields(val))
            continue
        if re.match(r"^1\.2", line):
            current_subsection = "1.2"
            val = ""
            if ":" in line:
                val = line.split(":", 1)[1].strip()
            elif "：" in line:
                val = line.split("：", 1)[1].strip()
            if is_plain_none(val):
                has_vocal = False
            continue
        if re.match(r"^1\.3", line):
            current_subsection = "1.3"
            val = ""
            if ":" in line:
                val = line.split(":", 1)[1].strip()
            elif "：" in line:
                val = line.split("：", 1)[1].strip()
            if is_plain_none(val):
                has_vocal = False
            continue
        if re.match(r"^2\.\s*环境(音与|与)音效:", line):
            current_section = "effects"
            current_subsection = None
            continue
        if re.match(r"^2\.1", line):
            current_subsection = "2.1"
            val = ""
            if ":" in line:
                val = line.split(":", 1)[1].strip()
            elif "：" in line:
                val = line.split("：", 1)[1].strip()
            if val:
                effects_2_1 = val
            continue
        if re.match(r"^2\.2", line):
            current_subsection = "2.2"
            val = ""
            if ":" in line:
                val = line.split(":", 1)[1].strip()
            elif "：" in line:
                val = line.split("：", 1)[1].strip()
            if is_plain_none(val):
                effects_2_2_lines = ["无"]
            continue
        if re.match(r"^3\.\s*背景音乐:", line):
            current_section = "bgm"
            current_subsection = None
            val = line.split(":", 1)[1].strip() if ":" in line else ""
            if is_plain_none(val):
                bgm_none = True
            continue
        if re.match(r"^4\.\s*特殊合成音效:", line):
            current_section = "special"
            current_subsection = None
            val = line.split(":", 1)[1].strip() if ":" in line else ""
            if is_plain_none(val):
                special_none = True
            continue

        speaker_match = re.match(r"^(说话人|演唱者)\s*(\d+)\s*:", line)
        if speaker_match:
            name = f"{speaker_match.group(1)} {speaker_match.group(2)}"
            if current_subsection == "1.2":
                vocal_1_2.append({"name": name, "fields": {}})
            elif current_subsection == "1.3":
                vocal_1_3.append(name)
            continue

        ts_match = re.match(
            r"^\[\s*(\d{1,2}(?::\d{1,3}){1,2}(?:\.\d{1,3})?)\s*-\s*(\d{1,2}(?::\d{1,3}){1,2}(?:\.\d{1,3})?)\s*\]\s*(.*)",
            line,
        )
        if ts_match:
            start_t = normalize_time(ts_match.group(1))
            end_t = normalize_time(ts_match.group(2))
            text_val = ts_match.group(3).strip()
            if current_section == "effects":
                if not text_val.endswith("。") and not text_val.endswith("."):
                    text_val += "。"
                elif text_val.endswith("."):
                    text_val = text_val[:-1] + "。"
                effects_2_2_lines.append(f"[{start_t}-{end_t}] {text_val}")
            elif current_section == "vocal":
                if text_val.startswith('"') and len(text_val) > 1:
                    inner = text_val[1:]
                    if inner and inner[0].islower():
                        text_val = '"...' + inner
                vocal_1_3.append(f"[{start_t}-{end_t}] {text_val}")
            elif current_section == "bgm":
                bgm_lines.append(f"[{start_t}-{end_t}] {text_val}".strip())
            continue

        kv_match = re.match(
            r"^(整体声音质量|声学环境|视觉标识|年龄与性别|口音/方言|基本音色特征|基本响度与节奏|基本响度|演唱节奏|演唱风格|歌唱技巧与表现力|情感|音量|乐器|节奏与速度|录音质量与制作手法|旋律与和声|风格流派|风格/流派|氛围情绪|氛围/情绪|作用)\s*[:：]\s*(.*)",
            line,
        )
        if kv_match:
            key = kv_match.group(1).strip().replace("风格/流派", "风格流派").replace("氛围/情绪", "氛围情绪")
            val = kv_match.group(2).strip()
            if current_section == "bgm":
                if bgm_lines:
                    bgm_lines.append(f"{key}: {val}")
                else:
                    bgm_fields[key] = val
                if val != "无":
                    bgm_none = False
            elif current_section == "vocal":
                if current_subsection == "1.1":
                    vocal_1_1[key] = val
                elif current_subsection == "1.2" and vocal_1_2:
                    fields = vocal_1_2[-1]["fields"]
                    assert isinstance(fields, dict)
                    fields[key] = val
                elif current_subsection == "1.3":
                    vocal_1_3.append(f"{key}: {val}")
            continue

        opt_match = re.match(r"^[\[【](本段说话人动态属性|本段声学环境/质量|本段视觉信息补充)[\]】].*?[:：]\s*(.*)", line)
        if opt_match:
            vocal_1_3.append(f"【{opt_match.group(1)}】: {opt_match.group(2)}")
            continue

        if current_section == "effects":
            if current_subsection == "2.1":
                effects_2_1 = f"{effects_2_1} {line}".strip() if effects_2_1 else line
            elif current_subsection == "2.2":
                if is_plain_none(line):
                    effects_2_2_lines = ["无"]
                else:
                    effects_2_2_lines.append(line)
        elif current_section == "special":
            if is_plain_none(line):
                special_none = True
            else:
                special_effects_lines.append(line)
        elif current_section == "bgm" and is_plain_none(line):
            bgm_none = True
        elif current_section == "bgm":
            bgm_lines.append(line)

    if bgm_fields and all(v == "无" for v in bgm_fields.values()):
        bgm_none = True

    output_lines = [f"总体概述: {summary}", "详细描述:", "1. 人声:"]
    if not has_vocal:
        output_lines.extend([
            "1.1 通用录音环境与质量：无",
            "1.2 说话/演唱人档案：无",
            "1.3 说话/歌词内容：无",
        ])
    else:
        output_lines.append("    1.1 通用录音环境与质量:")
        for key in ("整体声音质量", "声学环境"):
            if key in vocal_1_1:
                output_lines.append(f"        {key}: {vocal_1_1[key]}")

        output_lines.append("    1.2 说话/演唱人档案:")
        for speaker in vocal_1_2:
            output_lines.append(f"        {speaker['name']}:")
            fields = speaker["fields"]
            assert isinstance(fields, dict)
            for key in ("视觉标识", "年龄与性别", "口音/方言", "基本音色特征", "基本响度与节奏", "基本响度", "演唱节奏", "演唱风格", "歌唱技巧与表现力"):
                if key in fields:
                    output_lines.append(f"            {key}: {fields[key]}")

        output_lines.append("    1.3 说话/歌词内容:")
        if vocal_1_3 and not (vocal_1_3[0].startswith("说话人") or vocal_1_3[0].startswith("演唱者")) and vocal_1_2:
            first_spk = vocal_1_2[0]["name"]
            vocal_1_3.insert(0, first_spk)
        for item in vocal_1_3:
            if item.startswith("说话人") or item.startswith("演唱者"):
                output_lines.append(f"        {item}:")
            elif item.startswith("["):
                output_lines.append(f"            {item}")
            else:
                output_lines.append(f"            {item}")

    output_lines.append("2. 环境音与音效:")
    output_lines.append(f" 2.1 环境背景声: {effects_2_1 or '无'}")
    if not effects_2_2_lines or effects_2_2_lines == ["无"]:
        output_lines.append(" 2.2 音效: 无")
    else:
        output_lines.append(" 2.2 音效:")
        for line in effects_2_2_lines:
            output_lines.append(f"  {line}")

    if bgm_none or (not bgm_fields and not bgm_lines):
        output_lines.append("3. 背景音乐: 无")
    elif bgm_lines:
        output_lines.append("3. 背景音乐:")
        output_lines.extend(f"   {line}" for line in bgm_lines)
    else:
        output_lines.append("3. 背景音乐:")
        for key in ("音量", "乐器", "节奏与速度", "录音质量与制作手法", "旋律与和声", "风格流派", "氛围情绪", "作用"):
            output_lines.append(f"   {key}: {bgm_fields.get(key, '无')}")

    if special_none or not special_effects_lines:
        output_lines.append("4. 特殊合成音效: 无")
    else:
        output_lines.append("4. 特殊合成音效:")
        output_lines.extend(f"   {line}" for line in special_effects_lines)

    return "\n".join(output_lines)
