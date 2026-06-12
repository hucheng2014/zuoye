from __future__ import annotations

import argparse
import asyncio
import contextlib
import io
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

from playwright.async_api import async_playwright


CDP_URL = "http://127.0.0.1:9333"
MAX_SUCCESS = 40
LOG_PATH = Path(r"C:\Users\BERN7P\AppData\Local\Temp\appen_batch_log.jsonl")
STABLE_STREAK_TO_STOP = 20
PUNC_MODEL_NAME = os.getenv("APPEN_PUNC_MODEL", "ct-punc")
ASCII_TO_FULLWIDTH = str.maketrans(
    {
        ".": "\u3002",
        "?": "\uFF1F",
        "!": "\uFF01",
        ",": "\uFF0C",
        ";": "\uFF1B",
        ":": "\uFF1A",
    }
)

BREAK_BEFORE_PATTERNS = [
    "\u5A18\u5FC3\u91CC",
    "\u6211\u5FC3\u91CC",
    "\u4FFA\u5FC3\u91CC",
    "\u4F60\u5FC3\u91CC",
    "\u6068\u5FC3\u91CC",
    "\u54B1\u5FC3\u91CC",
    "\u5979\u5FC3\u91CC",
    "\u4ED6\u5FC3\u91CC",
    "\u4ED6\u5A18",
    "\u4F60\u5A18",
]

QUESTION_CUES = [
    "\uFF1F",
    "\u561B",
    "\u5417",
    "\u5565",
    "\u5565\u65F6\u5019",
    "\u4EC0\u4E48",
    "\u4EC0\u4E48\u65F6\u5019",
    "\u8C01",
    "\u54EA",
    "\u600E\u4E48",
    "\u600E\u6837",
    "\u51E0",
    "\u591A\u5C11",
    "\u6709\u6CA1\u6709",
    "\u662F\u4E0D\u662F",
    "\u80FD\u4E0D\u80FD",
    "\u4E2D\u4E0D\u4E2D",
    "\u884C\u4E0D\u884C",
    "\u6210\u4E0D\u6210",
    "\u597D\u4E0D\u597D",
    "\u5BF9\u4E0D\u5BF9",
]
TERMINAL_QUESTION_RE = re.compile(
    r"(中不中|行不行|成不成|好不好|对不对|有没有|是不是|能不能)[。！？]?$"
)

ERHUA_CANDIDATES = [
    "\u91CC\u5934",
    "\u5FC3\u91CC\u5934",
    "\u624B\u91CC\u5934",
    "\u5BB6\u91CC\u5934",
    "\u5916\u5934",
    "\u524D\u5934",
    "\u540E\u5934",
    "\u90A3\u5934",
    "\u8FD9\u5934",
    "\u65E9\u70B9",
    "\u5FEB\u70B9",
    "\u665A\u70B9",
    "\u6162\u70B9",
    "\u4E00\u70B9",
    "\u6709\u70B9",
    "\u8FD9\u8FB9",
    "\u90A3\u8FB9",
    "\u54EA\u8FB9",
    "\u5916\u8FB9",
    "\u4E00\u5757",
    "\u8FD9\u5757",
    "\u90A3\u5757",
    "\u8FD9\u4F1A",
    "\u90A3\u4F1A",
]
DE_RESULT_PREFIXES = (
    "\u70ED|\u51B7|\u7D2F|\u4E50|\u5FD9|\u6025|\u6C14|\u70E6|\u614C|\u75BC|\u75D2|"
    "\u6696\u548C|\u51C9\u5FEB|\u9AD8\u5174|\u4F24\u5FC3|\u4E2D\u610F|\u5F97\u52B2|"
    "\u96BE\u53D7|\u8212\u670D|\u4E0D\u5F97\u52B2\u513F"
)
DE_RESULT_SUFFIXES = (
    "\u5192\u6C57|\u6D41\u6C57|\u6D41\u6CEA|\u4E0D\u5F97\u52B2\u513F|\u76F4\u8E66\u8DF6|"
    "\u53D1\u614C|\u5FC3\u614C|\u96BE\u53D7|\u8981\u547D|\u5389\u5BB3|\u7761\u4E0D\u7740|"
    "\u76F4\u6253\u8F6C|\u76F4\u60F3\u54ED|\u5F88"
)
DE_ADVERBIAL_PREFIXES = (
    "\u6162\u6162|\u6084\u6084|\u597D\u597D|\u8BA4\u771F|\u4ED4\u7EC6|\u7A33\u7A33|"
    "\u8F7B\u8F7B|\u5FEB\u5FEB|\u6E10\u6E10"
)
DE_VERBS = (
    "\u8D70|\u8BF4|\u8BB2|\u5199|\u770B|\u542C|\u5403|\u559D|\u5E72|\u5B66|\u6765|"
    "\u53BB|\u8DD1|\u804A|\u5531|\u641E|\u529E"
)
DE_AUTO_FIX_RULES = [
    (
        re.compile(rf"({DE_RESULT_PREFIXES})(的|地)({DE_RESULT_SUFFIXES})"),
        r"\1得\3",
        "结果补语前改为“得”",
    ),
    (
        re.compile(rf"({DE_ADVERBIAL_PREFIXES})(的|得)({DE_VERBS})"),
        r"\1地\3",
        "状语前改为“地”",
    ),
]
DE_WARNING_RULES = [
    (
        re.compile(rf"(的|地)({DE_RESULT_SUFFIXES})"),
        "疑似结果补语前应使用“得”",
    ),
    (
        re.compile(rf"({DE_ADVERBIAL_PREFIXES})(得|的)({DE_VERBS})"),
        "疑似状语前应使用“地”",
    ),
]

TIME_CLAUSE_RE = re.compile(
    r"^(.{1,10}?[\u4E86\u54A7\u561E\u5570\u554A\u5462])([\u4F60\u6068\u6211\u4FFA\u54B1\u5A18\u4ED6\u5979])"
)
LEAD_IN_RE = re.compile(
    r"^(俺|我|咱|咱们|你|您)(觉得|寻思|想着)(只要|如果|要是|因为|虽说|虽然|哪怕)"
)
CONDITIONAL_SPLIT_RULES = [
    (
        re.compile(r"(只要[^，。！？]{2,20}?)(啥时候|什么时候|都能|就能|都|就)"),
        r"\1，\2",
    ),
    (re.compile(r"(月饼)(中秋团圆)"), r"\1，\2"),
    (re.compile(r"(中秋团圆)(你|您)"), r"\1，\2"),
    (re.compile(r"(节儿)(你|您)"), r"\1，\2"),
    (re.compile(r"(咋样)(中不中)"), r"\1，\2"),
    (re.compile(r"(不得劲儿)(赶明儿|改明儿|明儿)"), r"\1，\2"),
    (re.compile(r"(这顿饺子)(恁|你|您)"), r"\1，\2"),
    (re.compile(r"(啥馅的)(俺|我|咱|咱们)"), r"\1？\2"),
    (re.compile(r"(请客)(中不中|行不行|成不成)"), r"\1，\2"),
    (re.compile(r"(逛大集)(俺|我|咱|咱们)"), r"\1，\2"),
    (re.compile(r"(挂起)(真得劲|怪得劲|可得劲)"), r"\1，\2"),
    (re.compile(r"(都过咧)(恁|你|您)"), r"\1，\2"),
    (re.compile(r"(天冷)(恁|你|您)"), r"\1，\2"),
    (re.compile(r"(咋样)[，,](俺|我|咱|咱们)"), r"\1？\2"),
    (re.compile(r"(今儿个)(俺|我|咱|咱们|你|您|恁)"), r"\1，\2"),
    (re.compile(r"(咋还[^，。！？]{0,20}?)(莫不是)"), r"\1？\2"),
    (re.compile(r"^(元旦|元宵|中秋|十月|六月|凌晨)(你|您|恁|俺|我|咱|咱们)"), r"\1，\2"),
    (re.compile(r"(早点儿?回来)(俺|我|咱|咱们|一个人)"), r"\1，\2"),
    (re.compile(r"(忙活一天)(累得|忙得|困得|难受得|不得劲儿)"), r"\1，\2"),
    (re.compile(r"(啥汤)(中不中|行不行|成不成|好不好|对不对)"), r"\1，\2"),
]

@dataclass
class TaskInfo:
    record_id: int
    content: str
    audio_url: str


_PUNC_MODEL = None
_PUNC_MODEL_BACKEND = "rules-only"


def get_punc_model():
    global _PUNC_MODEL, _PUNC_MODEL_BACKEND
    if _PUNC_MODEL is False:
        return None
    if _PUNC_MODEL is not None:
        return _PUNC_MODEL

    if os.getenv("APPEN_DISABLE_FUNASR_PUNC") == "1":
        _PUNC_MODEL = False
        _PUNC_MODEL_BACKEND = "rules-only"
        return None

    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            from funasr import AutoModel
            _PUNC_MODEL = AutoModel(model=PUNC_MODEL_NAME, disable_update=True)
        _PUNC_MODEL_BACKEND = f"funasr:{PUNC_MODEL_NAME}+rules"
        return _PUNC_MODEL
    except Exception:
        _PUNC_MODEL = False
        _PUNC_MODEL_BACKEND = "rules-only"
        return None


def get_formatter_backend() -> str:
    get_punc_model()
    return _PUNC_MODEL_BACKEND


def apply_punc_model(text: str) -> str:
    model = get_punc_model()
    if model is None:
        return text

    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = model.generate(input=text)
        if result and isinstance(result, list):
            output = str(result[0].get("text", "")).strip()
            if output and re.search(r"[\u4e00-\u9fff]", output):
                return output.translate(ASCII_TO_FULLWIDTH)
    except Exception:
        pass
    return text


def cleanup_punctuation(text: str) -> str:
    current = text
    current = re.sub(r"(天儿)，(凉|冷|热)", r"\1\2", current)
    current = re.sub(r"(天儿凉|天儿冷|天凉|天冷)(您|你|恁)", r"\1，\2", current)
    current = re.sub(r"(心里头)，(美滋滋|热乎着呢|乐得|怪得劲|直蹦跶)", r"\1\2", current)
    current = re.sub(r"(咧)(真中|真得劲|真好|真美|真带劲)", r"\1，\2", current)
    current = re.sub(r"(凉)(办事利索)", r"\1，\2", current)
    current = re.sub(r"(不说)，(早点儿?回来)", r"\1\2", current)
    current = re.sub(r"((?:你|您|恁)?说)，(咱|咱们|俺|我|今儿)", r"\1\2", current)
    current = re.sub(
        r"(喝点啥[^，。！？]{0,6}?)(中不中|行不行|成不成|好不好|对不对)([。！？]?)$",
        r"\1，\2\3",
        current,
    )
    current = re.sub(
        r"([^，。！？])((中不中|行不行|成不成|好不好|对不对))([。！？]?)$",
        r"\1，\2\4",
        current,
    )
    current = re.sub(r"[\uFF0C]{2,}", "\uFF0C", current)
    current = re.sub(r"[\u3002]{2,}", "\u3002", current)
    current = re.sub(r"[\uFF01]{2,}", "\uFF01", current)
    current = re.sub(r"[\uFF1F]{2,}", "\uFF1F", current)
    if TERMINAL_QUESTION_RE.search(current):
        current = re.sub(r"[。！]$", "\uFF1F", current)
        if not current.endswith("\uFF1F"):
            current += "\uFF1F"
    return current


def audit_de_particles(text: str) -> tuple[str, list[str], list[str]]:
    current = text
    auto_fixes: list[str] = []
    warnings: list[str] = []

    for pattern, repl, reason in DE_AUTO_FIX_RULES:
        updated, count = pattern.subn(repl, current)
        if count:
            current = updated
            if reason not in auto_fixes:
                auto_fixes.append(reason)

    for pattern, reason in DE_WARNING_RULES:
        if pattern.search(current) and reason not in warnings:
            warnings.append(reason)

    return current, auto_fixes, warnings


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def is_question(text: str) -> bool:
    if text.endswith("\uFF1F"):
        return True
    tail = re.split(r"[\uFF0C\u3002\uFF01\uFF1F\uFF1B\uFF1A]", text)[-1]
    return any(tail.endswith(cue) or cue in tail[-8:] for cue in QUESTION_CUES[1:])


def insert_internal_punctuation(text: str) -> str:
    current = text

    for pat in BREAK_BEFORE_PATTERNS:
        idx = current.find(pat)
        if idx > 0:
            current = current[:idx] + "\uFF0C" + current[idx:]
            break

    match = TIME_CLAUSE_RE.match(current)
    if match:
        current = match.group(1) + "\uFF0C" + match.group(2) + current[match.end() :]

    lead = LEAD_IN_RE.match(current)
    if lead:
        current = lead.group(1) + lead.group(2) + "\uFF0C" + current[lead.end(2) :]

    for pattern, repl in CONDITIONAL_SPLIT_RULES:
        current = pattern.sub(repl, current, count=1)

    return current


def format_text(text: str) -> str:
    current = normalize_spaces(text).translate(ASCII_TO_FULLWIDTH)
    current = re.sub(r"[\uFF0C]{2,}", "\uFF0C", current)
    current = re.sub(r"[\u3002]{2,}", "\u3002", current)
    current = re.sub(r"[\uFF01]{2,}", "\uFF01", current)
    current = re.sub(r"[\uFF1F]{2,}", "\uFF1F", current)
    current = apply_punc_model(current)
    current = insert_internal_punctuation(current)
    current = cleanup_punctuation(current)
    current = re.sub(r"[\uFF0C]{2,}", "\uFF0C", current)
    current = re.sub(r"[\u3002]{2,}", "\u3002", current)
    current = re.sub(r"[\uFF01]{2,}", "\uFF01", current)
    current = re.sub(r"[\uFF1F]{2,}", "\uFF1F", current)
    if not current.endswith(("\u3002", "\uFF01", "\uFF1F")):
        current += "\uFF1F" if is_question(current) else "\u3002"
    return current


def detect_erhua_candidates(text: str) -> list[str]:
    found: list[str] = []
    plain = normalize_spaces(text)
    for candidate in ERHUA_CANDIDATES:
        if re.search(re.escape(candidate) + r"(?!儿)", plain) and candidate not in found:
            found.append(candidate)
    return found


def classify_level(source_text: str, de_warnings: list[str]) -> tuple[str, list[str]]:
    suspects = detect_erhua_candidates(source_text)
    if suspects or de_warnings:
        return "warning", suspects
    return "ok", []


async def ensure_task_page_ready(page) -> None:
    await page.evaluate(
        """
        () => {
          const labels = new Set(['继续工作', '关闭重试']);
          const node = [...document.querySelectorAll('button, div, span')]
            .find(el => labels.has((el.innerText || '').trim()));
          if (node) node.click();
        }
        """
    )


async def find_editor_owner(page):
    for frame in page.frames:
        try:
            locator = frame.locator("textarea.ant-input")
            if await locator.count():
                return frame
        except Exception:
            continue

    locator = page.locator("textarea.ant-input")
    if await locator.count():
        return page
    raise RuntimeError("Transcription textarea not found in any frame.")


async def inject_banner(page, kind: str, title: str, lines: list[str]) -> None:
    colors = {
        "warning": ("#7f1d1d", "#fecaca"),
        "error": ("#78350f", "#fde68a"),
        "ok": ("#14532d", "#bbf7d0"),
        "info": ("#1e3a8a", "#bfdbfe"),
    }
    bg, fg = colors.get(kind, colors["info"])
    await page.evaluate(
        """
        ([kind, title, lines, bg, fg]) => {
          let box = document.getElementById('codex-batch-banner');
          if (!box) {
            box = document.createElement('div');
            box.id = 'codex-batch-banner';
            box.style.position = 'fixed';
            box.style.top = '52px';
            box.style.right = '16px';
            box.style.width = '420px';
            box.style.zIndex = '2147483647';
            box.style.borderRadius = '10px';
            box.style.padding = '12px 14px';
            box.style.boxShadow = '0 12px 30px rgba(0,0,0,.35)';
            box.style.fontFamily = 'Segoe UI, Microsoft YaHei, sans-serif';
            box.style.whiteSpace = 'pre-wrap';
            document.body.appendChild(box);
          }
          box.style.background = bg;
          box.style.color = fg;
          box.innerHTML = '';
          const h = document.createElement('div');
          h.style.fontSize = '14px';
          h.style.fontWeight = '700';
          h.style.marginBottom = '8px';
          h.textContent = title;
          box.appendChild(h);
          for (const line of lines) {
            const p = document.createElement('div');
            p.style.fontSize = '12px';
            p.style.lineHeight = '1.5';
            p.textContent = line;
            box.appendChild(p);
          }
        }
        """,
        [kind, title, lines, bg, fg],
    )


async def clear_banner(page) -> None:
    await page.evaluate(
        """
        () => {
          const box = document.getElementById('codex-batch-banner');
          if (box) box.remove();
        }
        """
    )


async def get_task(page) -> TaskInfo:
    data = await page.evaluate(
        """
        () => ({
          recordId: window.__INITIAL_DATA__.taskMessage.taskRows[0].recordId,
          content: window.__INITIAL_DATA__.taskMessage.source.content,
          audioUrl: window.__INITIAL_DATA__.taskMessage.source.audio_url
        })
        """
    )
    return TaskInfo(
        record_id=data["recordId"],
        content=data["content"],
        audio_url=data["audioUrl"],
    )


async def select_and_fill(page, text: str) -> bool:
    await ensure_task_page_ready(page)
    owner = await find_editor_owner(page)
    await owner.wait_for_selector("textarea.ant-input", timeout=10000)
    return await owner.evaluate(
        """
        (value) => {
          const ta = document.querySelector('textarea.ant-input');
          if (!ta) return false;
          const setter = Object.getOwnPropertyDescriptor(
            window.HTMLTextAreaElement.prototype,
            'value'
          ).set;
          setter.call(ta, value);
          ta.dispatchEvent(new InputEvent('input', { bubbles: true, data: value, inputType: 'insertText' }));
          ta.dispatchEvent(new Event('change', { bubbles: true }));
          return ta.value === value;
        }
        """,
        text,
    )


async def current_text(page) -> str:
    owner = await find_editor_owner(page)
    return await owner.evaluate(
        """
        () => {
          const ta = document.querySelector('textarea.ant-input');
          return ta ? ta.value : '';
        }
        """
    )


async def current_hidden_annotation(page) -> str:
    locator = page.locator('input[name*="[annotation]"]').first
    return await locator.input_value()


async def wait_for_hidden_annotation_change(
    page, before_value: str, timeout_ms: int = 6000
) -> str:
    start = time.time()
    while (time.time() - start) * 1000 < timeout_ms:
        current = await current_hidden_annotation(page)
        if current and current != before_value:
            return current
        await page.wait_for_timeout(250)
    return before_value


async def click_submit_and_wait(page, before_id: int, timeout_ms: int = 12000) -> int:
    button = page.locator("button.ant-btn.ant-btn-default.ant-btn-block").first
    await button.click()
    return await wait_for_record_change(page, before_id, timeout_ms)


async def wait_for_record_change(page, before_id: int, timeout_ms: int = 12000) -> int:
    start = time.time()
    while (time.time() - start) * 1000 < timeout_ms:
        try:
            current = await page.evaluate("window.__INITIAL_DATA__.taskMessage.taskRows[0].recordId")
            if current != before_id:
                return current
        except Exception:
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=1500)
            except Exception:
                pass
        await page.wait_for_timeout(500)
    return before_id


async def wait_for_user_submit(page, before_id: int, draft: str, timeout_ms: int = 900000) -> tuple[int, str, bool]:
    start = time.time()
    last_text = draft
    user_edited = False
    while (time.time() - start) * 1000 < timeout_ms:
        try:
            current = await page.evaluate("window.__INITIAL_DATA__.taskMessage.taskRows[0].recordId")
            if current != before_id:
                return current, last_text, user_edited
            visible = await current_text(page)
            if visible:
                last_text = visible
                if visible != draft:
                    user_edited = True
        except Exception:
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=1500)
            except Exception:
                pass
        await page.wait_for_timeout(250)
    return before_id, last_text, user_edited


def append_log(item: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False) + "\n")


async def find_task_page(browser):
    for context in browser.contexts:
        for page in context.pages:
            if "annotation-task-start" in page.url:
                return page
    raise RuntimeError("Task page not found.")


async def run_batch(max_success: int, auto_submit: bool) -> None:
    success = 0
    stable_streak = 0
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        page = await find_task_page(browser)
        await ensure_task_page_ready(page)
        await clear_banner(page)
        await inject_banner(
            page,
            "info",
            "Codex Semi-Auto Running",
            [
                f"Target successful submissions: {max_success}",
                f"Auto-submit enabled: {'YES' if auto_submit else 'NO'}",
                "Suspicious erhua items will stop and wait for manual review.",
            ],
        )
        try:
            while success < max_success:
                await ensure_task_page_ready(page)
                task = await get_task(page)
                formatted = format_text(task.content)
                formatted, de_auto_fixes, de_warnings = audit_de_particles(formatted)
                level, suspects = classify_level(task.content, de_warnings)
                hidden_before = await current_hidden_annotation(page)

                if level == "warning":
                    lines = [
                        f"recordId: {task.record_id}",
                        f"raw: {task.content}",
                        f"draft: {formatted}",
                    ]
                    if suspects:
                        lines.append("suspected optional erhua: " + " / ".join(suspects))
                    if de_warnings:
                        lines.append("de-particle review: " + " / ".join(de_warnings))
                    if de_auto_fixes:
                        lines.append("auto-fixed: " + " / ".join(de_auto_fixes))
                    lines.append("Review carefully, then click the LEFT submit button manually if correct.")
                    await select_and_fill(page, formatted)
                    await inject_banner(page, "warning", "Manual Review Required", lines)
                    entry = {
                        "recordId": task.record_id,
                        "status": "manual_review_required",
                        "raw": task.content,
                        "draft": formatted,
                        "formatterBackend": get_formatter_backend(),
                        "deAutoFixes": de_auto_fixes,
                        "deWarnings": de_warnings,
                        "suspects": suspects,
                        "audioUrl": task.audio_url,
                    }
                    append_log(entry)
                    print(json.dumps(entry, ensure_ascii=False), flush=True)
                    next_id, final_text, user_edited = await wait_for_user_submit(
                        page, task.record_id, formatted, timeout_ms=900000
                    )
                    if next_id == task.record_id:
                        timeout_entry = {
                            "recordId": task.record_id,
                            "status": "manual_review_timeout",
                            "raw": task.content,
                            "draft": formatted,
                            "formatterBackend": get_formatter_backend(),
                            "deAutoFixes": de_auto_fixes,
                            "deWarnings": de_warnings,
                            "finalText": final_text,
                            "userEdited": user_edited,
                            "audioUrl": task.audio_url,
                        }
                        append_log(timeout_entry)
                        await inject_banner(
                            page,
                            "warning",
                            "Manual Review Timed Out",
                            [
                                f"recordId: {task.record_id}",
                                "No next item was loaded within 15 minutes.",
                                "Script stopped without any automatic submission.",
                            ],
                        )
                        print(json.dumps(timeout_entry, ensure_ascii=False), flush=True)
                        return
                    success += 1
                    submitted_entry = {
                        "recordId": task.record_id,
                        "status": "submitted_by_user_after_manual_review",
                        "raw": task.content,
                        "draft": formatted,
                        "formatterBackend": get_formatter_backend(),
                        "deAutoFixes": de_auto_fixes,
                        "deWarnings": de_warnings,
                        "finalText": final_text,
                        "userEdited": user_edited,
                        "suspects": suspects,
                        "audioUrl": task.audio_url,
                        "nextRecordId": next_id,
                        "successCount": success,
                    }
                    append_log(submitted_entry)
                    print(json.dumps(submitted_entry, ensure_ascii=False), flush=True)
                    stable_streak = stable_streak + 1 if not user_edited else 0
                    if stable_streak >= STABLE_STREAK_TO_STOP:
                        stable_entry = {
                            "recordId": task.record_id,
                            "status": "accuracy_stable_stop",
                            "reason": f"{stable_streak} consecutive submissions without user edits",
                            "successCount": success,
                        }
                        append_log(stable_entry)
                        await inject_banner(
                            page,
                            "ok",
                            "Accuracy Stable",
                            [
                                f"Consecutive no-edit submissions: {stable_streak}",
                                "Watcher stopped so rules can be reviewed before further changes.",
                            ],
                        )
                        print(json.dumps(stable_entry, ensure_ascii=False), flush=True)
                        return
                    await inject_banner(
                        page,
                        "ok",
                        "Manual Review Accepted",
                        [
                            f"Successful submissions: {success}/{max_success}",
                            f"Last recordId: {task.record_id}",
                            f"Consecutive no-edit submissions: {stable_streak}",
                        ],
                    )
                    await page.wait_for_timeout(1200)
                    continue

                filled = await select_and_fill(page, formatted)
                if not filled:
                    entry = {
                        "recordId": task.record_id,
                        "status": "fill_failed",
                        "raw": task.content,
                        "draft": formatted,
                        "formatterBackend": get_formatter_backend(),
                        "deAutoFixes": de_auto_fixes,
                        "deWarnings": de_warnings,
                        "audioUrl": task.audio_url,
                    }
                    append_log(entry)
                    await inject_banner(page, "error", "Fill Failed", [json.dumps(entry, ensure_ascii=False)])
                    print(json.dumps(entry, ensure_ascii=False), flush=True)
                    return

                visible = await current_text(page)
                if visible != formatted:
                    entry = {
                        "recordId": task.record_id,
                        "status": "verify_failed",
                        "raw": task.content,
                        "draft": formatted,
                        "formatterBackend": get_formatter_backend(),
                        "deAutoFixes": de_auto_fixes,
                        "deWarnings": de_warnings,
                        "visible": visible,
                        "audioUrl": task.audio_url,
                    }
                    append_log(entry)
                    await inject_banner(page, "error", "Verification Failed", [json.dumps(entry, ensure_ascii=False)])
                    print(json.dumps(entry, ensure_ascii=False), flush=True)
                    return

                if not auto_submit:
                    entry = {
                        "recordId": task.record_id,
                        "status": "filled_waiting_user_submit",
                        "raw": task.content,
                        "draft": formatted,
                        "formatterBackend": get_formatter_backend(),
                        "deAutoFixes": de_auto_fixes,
                        "deWarnings": de_warnings,
                        "audioUrl": task.audio_url,
                    }
                    append_log(entry)
                    info_lines = [
                        f"recordId: {task.record_id}",
                        "Text was filled into the visible transcription box.",
                    ]
                    if de_auto_fixes:
                        info_lines.append("auto-fixed: " + " / ".join(de_auto_fixes))
                    info_lines.append("Review it, then click the LEFT submit button manually to load the next item.")
                    await inject_banner(
                        page,
                        "info",
                        "Filled And Waiting",
                        info_lines,
                    )
                    print(json.dumps(entry, ensure_ascii=False), flush=True)
                    next_id, final_text, user_edited = await wait_for_user_submit(
                        page, task.record_id, formatted, timeout_ms=900000
                    )
                    if next_id == task.record_id:
                        timeout_entry = {
                            "recordId": task.record_id,
                            "status": "user_submit_timeout",
                            "raw": task.content,
                            "draft": formatted,
                            "formatterBackend": get_formatter_backend(),
                            "deAutoFixes": de_auto_fixes,
                            "deWarnings": de_warnings,
                            "finalText": final_text,
                            "userEdited": user_edited,
                            "audioUrl": task.audio_url,
                        }
                        append_log(timeout_entry)
                        await inject_banner(
                            page,
                            "warning",
                            "Waiting For User Submit Timed Out",
                            [
                                f"recordId: {task.record_id}",
                                "No next item was loaded within 15 minutes.",
                                "Script stopped without any automatic submission.",
                            ],
                        )
                        print(json.dumps(timeout_entry, ensure_ascii=False), flush=True)
                        return
                    success += 1
                    submitted_entry = {
                        "recordId": task.record_id,
                        "status": "submitted_by_user",
                        "raw": task.content,
                        "draft": formatted,
                        "formatterBackend": get_formatter_backend(),
                        "deAutoFixes": de_auto_fixes,
                        "deWarnings": de_warnings,
                        "finalText": final_text,
                        "userEdited": user_edited,
                        "audioUrl": task.audio_url,
                        "nextRecordId": next_id,
                        "successCount": success,
                    }
                    append_log(submitted_entry)
                    print(json.dumps(submitted_entry, ensure_ascii=False), flush=True)
                    stable_streak = stable_streak + 1 if not user_edited else 0
                    if stable_streak >= STABLE_STREAK_TO_STOP:
                        stable_entry = {
                            "recordId": task.record_id,
                            "status": "accuracy_stable_stop",
                            "reason": f"{stable_streak} consecutive submissions without user edits",
                            "successCount": success,
                        }
                        append_log(stable_entry)
                        await inject_banner(
                            page,
                            "ok",
                            "Accuracy Stable",
                            [
                                f"Consecutive no-edit submissions: {stable_streak}",
                                "Watcher stopped so rules can be reviewed before further changes.",
                            ],
                        )
                        print(json.dumps(stable_entry, ensure_ascii=False), flush=True)
                        return
                    await inject_banner(
                        page,
                        "ok",
                        "User Submitted",
                        [
                            f"Successful submissions: {success}/{max_success}",
                            f"Last recordId: {task.record_id}",
                            f"Consecutive no-edit submissions: {stable_streak}",
                        ],
                    )
                    await page.wait_for_timeout(1200)
                    continue

                hidden_after = await wait_for_hidden_annotation_change(page, hidden_before)
                if not hidden_after or hidden_after == hidden_before:
                    entry = {
                        "recordId": task.record_id,
                        "status": "annotation_sync_failed",
                        "raw": task.content,
                        "draft": formatted,
                        "formatterBackend": get_formatter_backend(),
                        "deAutoFixes": de_auto_fixes,
                        "deWarnings": de_warnings,
                        "audioUrl": task.audio_url,
                        "hiddenBefore": hidden_before,
                        "hiddenAfter": hidden_after,
                    }
                    append_log(entry)
                    await inject_banner(
                        page,
                        "error",
                        "Annotation Sync Failed",
                        [
                            f"recordId: {task.record_id}",
                            "The visible text changed, but the parent annotation URI did not change.",
                            "This item was NOT submitted.",
                        ],
                    )
                    print(json.dumps(entry, ensure_ascii=False), flush=True)
                    return

                next_id = await click_submit_and_wait(page, task.record_id)
                if next_id == task.record_id:
                    entry = {
                        "recordId": task.record_id,
                        "status": "submit_failed",
                        "raw": task.content,
                        "draft": formatted,
                        "audioUrl": task.audio_url,
                    }
                    append_log(entry)
                    await inject_banner(page, "error", "Submit Failed", [json.dumps(entry, ensure_ascii=False)])
                    print(json.dumps(entry, ensure_ascii=False), flush=True)
                    return

                success += 1
                entry = {
                    "recordId": task.record_id,
                    "status": "ok",
                    "raw": task.content,
                    "draft": formatted,
                    "formatterBackend": get_formatter_backend(),
                    "deAutoFixes": de_auto_fixes,
                    "deWarnings": de_warnings,
                    "audioUrl": task.audio_url,
                    "hiddenAnnotation": hidden_after,
                    "nextRecordId": next_id,
                    "successCount": success,
                }
                append_log(entry)
                print(json.dumps(entry, ensure_ascii=False), flush=True)
                await inject_banner(
                    page,
                    "ok",
                    "Codex Semi-Auto Running",
                    [f"Successful submissions: {success}/{max_success}", f"Last recordId: {task.record_id}"],
                )
                await page.wait_for_timeout(1200)

            await inject_banner(
                page,
                "ok",
                "Batch Complete",
                [f"Successful submissions: {success}", "Stopped because the configured batch size was reached."],
            )
        finally:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--submit", action="store_true", help="Allow clicking submit buttons.")
    parser.add_argument("--max-success", type=int, default=MAX_SUCCESS, help="Maximum successful submissions before stopping.")
    args = parser.parse_args()
    asyncio.run(run_batch(args.max_success, args.submit))
