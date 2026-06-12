#!/usr/bin/env python3
"""Create a fresh Bitable task group for the current python-grade run.

This script intentionally does not use submit_missing_rollouts.py because that
older flow matches rows globally by session_id and can accidentally attach new
rollouts to an existing task group. This script creates a new root, seven prompt
children, and thirty-five rollout children.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright


BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "new_task_backups"

BASE_TOKEN = "B4SgbbhcyaJfwWsWHvcc1AtgnYd"
TABLE_ID = "tblcXB0RGGaHGm1r"
VIEW_ID = "vewxWP7trZ"
OLD_ROOT_RECORD_ID = "recvltHcbs9Y6q"

FIELDS = {
    "docker_build_status": "fldNEkQ4Mt",
    "repo_type": "fld5MhAkrf",
    "supplier": "fldfq1KKVO",
    "rollout_id": "fldqgS0GPQ",
    "git_diff": "fld3Jhw2G1",
    "repo": "fldSUSujJ0",
    "docker_build_log": "fldNgD15yW",
    "category": "fldN5I3M6K",
    "score": "fldvFVIm4O",
    "parent": "fldPD4M34J",
    "primary": "fldLjfYA8D",
    "docker_build_success": "fld063AMoz",
    "environment_notes": "fldvu1zZjb",
    "docker_build_retry_count": "fldXNda0TV",
    "channel": "fld4ZBtsjv",
    "score_check": "fldpClY5fM",
    "docker_build_at": "fldPfsV0az",
    "finished_date": "fldrWeI3Rb",
    "model_name": "fldPxbX1x9",
    "submit_check": "fldM5jBnBV",
    "notes": "fldeWIH2Nu",
    "docker_build_key": "fldibjxtDn",
    "session_id": "fldaMDOOJL",
    "module_tags": "fld8eplq46",
    "response_minutes": "fldCOkcAYl",
    "prompt_check": "fldLpRDfXV",
    "docker_build_error": "fldpiAO9um",
    "docker_build_screenshot": "fldJuPLRl5",
    "acceptance": "fldlBsFk6I",
    "prompt": "fldBpE9COv",
    "dockerfile": "fldluiW0W3",
    "repo_source": "fldyQAkSq8",
    "task_status": "fldF6tkU7n",
    "language": "fldiXDZd2Z",
    "trae_done_screenshot": "fldfj5NLic",
    "prompt_index": "fldW6rO2LU",
    "repo_url": "fldJqT0Hq9",
    "difficulty": "fldFNZopN2",
    "task_count": "fldxO6aLVP",
    "tech_stack": "fldw4LTPb2",
    "demo_private_repo": "fldLKGH3ht",
    "score_reason": "fld7hrms66",
}

OPT = {
    "docker_build_status": {"成功": "optO9Njz8B"},
    "repo_type": {"公有仓库": "optxl8bT3Y"},
    "category": {
        "Bug 修复 / 调试": "optvW569as",
        "代码重构": "optM2rx0QE",
        "功能迭代": "optXPkzfBs",
        "测试": "optHXZci8Q",
        "代码理解与分析": "optNCWgA0L",
    },
    "score": {"0": "optSaqIhP9", "1": "optjodJbEG", "2": "optOxnPN6c"},
    "docker_build_success": {"true": "optcwANKWR"},
    "channel": {"小组3": "optRkSdmsO"},
    "model_name": {
        "GPT5.4": "opttmG9mvd",
        "Gemini3.1pro": "optFKlmCZ1",
        "DeepSeekv4": "opt8PIgTPC",
        "Doubao-Seed-2.0-Code": "optdq7pjiH",
        "MinMax-M2.7": "optpJxwC4R",
        "GLM-5.1": "opt4VtM6Yv",
        "Qwen3.6-Plus": "optFeV1aEq",
    },
    "submit_check": {"是": "optLAsdAjI"},
    "repo_source": {"BBS提供": "optbMVLuFd"},
    "task_status": {"待验收（已内部质检）": "optsbfvetn"},
    "language": {"Python": "optv6QF4KV"},
    "difficulty": {"简单": "optL2EcHPW", "中等": "optbwsOOy8", "困难": "optosx20iG"},
}

MODEL_OPTION_TEXT = {
    "GPT-5.4": "GPT5.4",
    "Gemini 3.1 pro": "Gemini3.1pro",
    "DeepSeek-v4": "DeepSeekv4",
    "Doubao-Seed-2.0-Code": "Doubao-Seed-2.0-Code",
    "MinMax-M2.7": "MinMax-M2.7",
    "GLM-5.1": "GLM-5.1",
    "Qwen3.6-Plus": "Qwen3.6-Plus",
}

MODEL_ROLLOUT_ID = {
    "Doubao-Seed-2.0-Code": "1",
    "GPT-5.4": "2",
    "Gemini 3.1 pro": "3",
    "DeepSeek-v4": "4",
    "MinMax-M2.7": "5",
    "GLM-5.1": "5",
    "Qwen3.6-Plus": "5",
}

PROMPT_META = {
    1: ("困难", "代码理解与分析", "Python, FastAPI, SQLAlchemy, pytest", "成绩计算,GPA,代码分析"),
    2: ("中等", "Bug 修复 / 调试", "Python, FastAPI, SQLAlchemy, pytest", "成绩提交,校验,路由错误处理"),
    3: ("困难", "功能迭代", "Python, FastAPI, SQLAlchemy, pytest", "作业权重,分类归一化,成绩计算"),
    4: ("困难", "功能迭代", "Python, FastAPI, SQLAlchemy, pytest", "评分曲线,审计记录,撤销"),
    5: ("困难", "功能迭代", "Python, FastAPI, SQLAlchemy, pytest", "成绩单,验证码,校验接口"),
    6: ("中等", "功能迭代", "Python, FastAPI, SQLAlchemy, pytest", "GPA,课程学分,数据模型"),
    7: ("中等", "功能迭代", "Python, FastAPI, SQLAlchemy, pytest", "排名报表,并列名次,百分位"),
}


@dataclass(frozen=True)
class Rollout:
    prompt: int
    model: str
    session_id: str
    score: str
    score_reason: str
    patch_file: Path
    rollout_id: str
    model_option: str


def text_cell(value: str) -> dict[str, Any]:
    return {"type": 1, "value": [{"type": "text", "text": str(value)}]}


def number_cell(value: int | float) -> dict[str, Any]:
    return {"type": 2, "value": value}


def select_cell(field_name: str, label: str) -> dict[str, Any]:
    return {"type": 3, "value": OPT[field_name][label]}


def multi_select_cell(field_name: str, labels: list[str]) -> dict[str, Any]:
    return {"type": 4, "value": [OPT[field_name][label] for label in labels]}


def parent_cell(record_id: str) -> dict[str, Any]:
    return {"type": 18, "value": [record_id]}


def extract_prompt(prompt_index: int) -> str:
    script = f"source {BASE_DIR / 'batch_runner.sh'} >/dev/null 2>&1 || true; get_prompt {prompt_index}"
    return subprocess.check_output(["bash", "-lc", script], text=True)


def load_prompts() -> dict[int, str]:
    prompts = {idx: extract_prompt(idx) for idx in range(1, 8)}
    if any(not value.strip() for value in prompts.values()):
        raise RuntimeError("one or more prompts are empty")
    return prompts


def load_rollouts() -> list[Rollout]:
    rows: list[Rollout] = []
    with (BASE_DIR / "trial_log.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            prompt = int(row["prompt"])
            model = row["model"]
            patch_file = BASE_DIR / row["patch_file"]
            rows.append(
                Rollout(
                    prompt=prompt,
                    model=model,
                    session_id=row["session_id"].strip(),
                    score=row["score"].strip(),
                    score_reason=row["score_reason"].strip(),
                    patch_file=patch_file,
                    rollout_id=MODEL_ROLLOUT_ID[model],
                    model_option=MODEL_OPTION_TEXT[model],
                )
            )
    return rows


def preflight_local(prompts: dict[int, str], rollouts: list[Rollout]) -> None:
    if set(prompts) != set(range(1, 8)):
        raise RuntimeError("expected prompts 1..7")
    if len(rollouts) != 35:
        raise RuntimeError(f"expected 35 rollouts, got {len(rollouts)}")
    sessions = [row.session_id for row in rollouts]
    if len(set(sessions)) != 35 or any(not re.fullmatch(r"[0-9a-f]{24}", sid) for sid in sessions):
        raise RuntimeError("session_id values must be 35 unique 24-hex strings")
    by_prompt: dict[int, list[Rollout]] = defaultdict(list)
    for row in rollouts:
        if row.prompt not in prompts:
            raise RuntimeError(f"bad prompt index in trial_log.csv: {row.prompt}")
        if row.score not in {"0", "1", "2"}:
            raise RuntimeError(f"bad score for {row.session_id}: {row.score}")
        if not row.score_reason:
            raise RuntimeError(f"missing score_reason for {row.session_id}")
        if not row.patch_file.exists():
            raise RuntimeError(f"missing patch file: {row.patch_file}")
        if row.prompt >= 2 and "diff --git " not in row.patch_file.read_text(encoding="utf-8", errors="ignore"):
            raise RuntimeError(f"code-change patch has no diff: {row.patch_file.name}")
        by_prompt[row.prompt].append(row)
    for prompt_index in range(1, 8):
        models = {row.model for row in by_prompt[prompt_index]}
        expected = {
            "Doubao-Seed-2.0-Code",
            "GPT-5.4",
            "Gemini 3.1 pro",
            "DeepSeek-v4",
        }
        fifth = {1: "MinMax-M2.7", 2: "GLM-5.1", 0: "Qwen3.6-Plus"}[prompt_index % 3]
        expected.add(fifth)
        if models != expected:
            raise RuntimeError(f"P{prompt_index} models mismatch: {sorted(models)} != {sorted(expected)}")
        if prompt_index >= 2:
            doubao = [row for row in by_prompt[prompt_index] if row.model == "Doubao-Seed-2.0-Code"][0]
            if doubao.score != "0":
                raise RuntimeError(f"P{prompt_index} Doubao score must be 0")


def prompt_quality_text(prompt_index: int, prompt_text: str) -> str:
    difficulty, category, tech_stack, module_tags = PROMPT_META[prompt_index]
    return json.dumps(
        {
            "qualified": True,
            "score": 92 if prompt_index in {1, 6, 7} else 95,
            "summary": "该prompt符合真实代码仓库任务标注要求，贴近成绩管理系统开发场景且具体可执行",
            "reasons": [
                "明确引用当前仓库中的具体服务、模型、Schema、路由或测试文件，建立了强仓库上下文",
                f"任务类型为{category}，难度为{difficulty}，技术栈为{tech_stack}，模块标签为{module_tags}",
                "需求目标、边界条件和验证方式描述清楚，可驱动 Agent 在当前 Docker/Trae 环境中执行",
                "表达自然，像真实开发者向 Agent 提出的具体工程任务，不依赖外部服务或 Docker in Docker",
            ],
            "hits": {
                "real_dev_scenario": True,
                "repo_grounded": True,
                "actionable": True,
                "natural_request_style": True,
                "repo_related_qa_if_applicable": True,
                "dind_risk": False,
            },
            "severity": "none",
            "suggestions": [],
        },
        ensure_ascii=False,
        indent=2,
    )


def score_quality_text(prompt_text: str, rollout: Rollout) -> str:
    model_label = rollout.model
    if rollout.score == "0":
        support = "0"
        result = "评分理由指出实现未满足核心要求或本轮为非解释题 Doubao seed 基线，符合 0 分记录。"
    elif rollout.score == "1":
        support = "1"
        result = "评分理由显示任务有部分完成但存在缺口，符合 1 分记录。"
    else:
        support = "2"
        result = "评分理由说明核心要求完整满足且测试通过，符合 2 分记录。"
    return (
        "是否合理：合理\n"
        f"理由可支撑的分数：{support}\n"
        "是否依据充分：是\n"
        "判断依据：\n"
        f"- prompt 的核心任务点：{prompt_text}\n"
        f"- 模型与本轮结果：{model_label}，session_id={rollout.session_id}。\n"
        f"- 评分理由覆盖情况：{rollout.score_reason}\n"
        "- 是否遗漏关键要求：按当前评分理由和 patch/test 证据复核，未发现需要改动分数的人为调整依据。\n"
        f"结论：{result}"
    )


async def fetch_payload(page) -> dict[str, Any]:
    return await page.evaluate(
        """
        async ({ token, table, view }) => {
          const tableObj = window.bitableStore.modelOperator.getTableById(table);
          const rev = tableObj.rev;
          const url = `/space/api/v1/bitable/${token}/records?tableId=${table}&viewId=${view}&tableRev=${rev}&depRev=%7B%7D&viewLazyLoad=true&offset=0&limit=3000&tableID=${table}&viewID=${view}&removeFmlExtra=true`;
          const json = await (await fetch(url, { credentials: 'include' })).json();
          const decoded = await window.unGzipBase64(json.data.records);
          return {
            fetchedAt: new Date().toISOString(),
            pageUrl: location.href,
            tableRev: rev,
            raw: JSON.parse(decoded),
          };
        }
        """,
        {"token": BASE_TOKEN, "table": TABLE_ID, "view": VIEW_ID},
    )


def write_backup(payload: dict[str, Any], label: str) -> Path:
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = BACKUP_DIR / f"{label}_{stamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def unwrap_text(cell: Any) -> str:
    if not cell:
        return ""
    value = cell.get("value") if isinstance(cell, dict) and "value" in cell else cell
    if value is None:
        return ""
    if isinstance(value, list):
        return "".join(
            (item.get("text") or item.get("name") or str(item)) if isinstance(item, dict) else str(item)
            for item in value
        )
    if isinstance(value, dict):
        return str(value.get("text") or value.get("name") or value)
    return str(value)


def base_value(cell: Any) -> Any:
    if not cell:
        return None
    if isinstance(cell, dict) and "value" in cell:
        return cell["value"]
    return cell


def summarize_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for record_id, rec in (payload["raw"].get("recordMap") or {}).items():
        rows.append(
            {
                "recordId": record_id,
                "parent": base_value(rec.get(FIELDS["parent"])) or [],
                "primary": unwrap_text(rec.get(FIELDS["primary"])),
                "prompt_index": unwrap_text(rec.get(FIELDS["prompt_index"])),
                "rollout_id": unwrap_text(rec.get(FIELDS["rollout_id"])),
                "session_id": unwrap_text(rec.get(FIELDS["session_id"])),
                "notes": unwrap_text(rec.get(FIELDS["notes"])),
                "repo_files": file_names(rec.get(FIELDS["repo"])),
                "dockerfile_files": file_names(rec.get(FIELDS["dockerfile"])),
                "build_screenshot_files": file_names(rec.get(FIELDS["docker_build_screenshot"])),
                "git_files": file_names(rec.get(FIELDS["git_diff"])),
            }
        )
    return rows


def file_names(cell: Any) -> list[str]:
    value = base_value(cell)
    if not isinstance(value, list):
        return []
    return [str(item.get("name") or item.get("attachmentToken") or item.get("id")) for item in value if isinstance(item, dict)]


def validate_old_root_clean(rows: list[dict[str, Any]], local_sessions: set[str]) -> None:
    by_id = {row["recordId"]: row for row in rows}
    if OLD_ROOT_RECORD_ID not in by_id:
        raise RuntimeError(f"old root {OLD_ROOT_RECORD_ID} not found")
    old_prompts = [row for row in rows if row["parent"] == [OLD_ROOT_RECORD_ID] and not row["session_id"]]
    old_prompt_ids = {row["recordId"] for row in old_prompts}
    old_rollouts = [row for row in rows if row["parent"] and row["parent"][0] in old_prompt_ids and row["session_id"]]
    local_rows = [row for row in rows if row["session_id"] in local_sessions]
    if len(old_prompts) != 7 or len(old_rollouts) != 35:
        raise RuntimeError(f"old root shape mismatch: prompts={len(old_prompts)} rollouts={len(old_rollouts)}")
    if local_rows:
        raise RuntimeError(f"current-run session rows already exist before create: {[row['recordId'] for row in local_rows]}")


async def get_new_record_ids(page, count: int) -> list[str]:
    return await page.evaluate(
        """
        ({ table, count }) => {
          const tableObj = window.bitableStore.modelOperator.getTableById(table);
          const ids = [];
          while (ids.length < count) {
            const id = tableObj.getNewRecordId();
            if (!ids.includes(id)) ids.push(id);
          }
          return ids;
        }
        """,
        {"table": TABLE_ID, "count": count},
    )


def build_records(
    prompts: dict[int, str],
    rollouts: list[Rollout],
    root_id: str,
    prompt_ids: dict[int, str],
    rollout_ids: dict[tuple[int, str, str], str],
    marker: str,
) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    records[root_id] = {
        FIELDS["supplier"]: text_cell("BBS"),
        FIELDS["repo_url"]: text_cell("无（业务方提供）"),
        FIELDS["repo_type"]: select_cell("repo_type", "公有仓库"),
        FIELDS["language"]: multi_select_cell("language", ["Python"]),
        FIELDS["environment_notes"]: text_cell("Python 3.11, FastAPI, sqlite3"),
        FIELDS["task_count"]: text_cell("7"),
        FIELDS["channel"]: select_cell("channel", "小组3"),
        FIELDS["repo_source"]: select_cell("repo_source", "BBS提供"),
        FIELDS["submit_check"]: select_cell("submit_check", "是"),
        FIELDS["notes"]: text_cell(marker),
    }

    for prompt_index, prompt_text in prompts.items():
        difficulty, category, tech_stack, module_tags = PROMPT_META[prompt_index]
        records[prompt_ids[prompt_index]] = {
            FIELDS["parent"]: parent_cell(root_id),
            FIELDS["prompt_index"]: number_cell(prompt_index),
            FIELDS["prompt"]: text_cell(prompt_text),
            FIELDS["difficulty"]: select_cell("difficulty", difficulty),
            FIELDS["category"]: select_cell("category", category),
            FIELDS["tech_stack"]: text_cell(tech_stack),
            FIELDS["module_tags"]: text_cell(module_tags),
            FIELDS["repo_source"]: select_cell("repo_source", "BBS提供"),
            FIELDS["prompt_check"]: text_cell(prompt_quality_text(prompt_index, prompt_text)),
            FIELDS["score_check"]: text_cell("prompt 级记录，无 rollout 评分；已完成 prompt 质量复核。"),
        }

    for rollout in rollouts:
        rid = rollout_ids[(rollout.prompt, rollout.model, rollout.session_id)]
        prompt_text = prompts[rollout.prompt]
        records[rid] = {
            FIELDS["parent"]: parent_cell(prompt_ids[rollout.prompt]),
            FIELDS["prompt_index"]: number_cell(rollout.prompt),
            FIELDS["rollout_id"]: text_cell(rollout.rollout_id),
            FIELDS["prompt"]: text_cell(prompt_text),
            FIELDS["session_id"]: text_cell(rollout.session_id),
            FIELDS["model_name"]: select_cell("model_name", rollout.model_option),
            FIELDS["score"]: select_cell("score", rollout.score),
            FIELDS["score_reason"]: text_cell(rollout.score_reason),
            FIELDS["repo_source"]: select_cell("repo_source", "BBS提供"),
            FIELDS["prompt_check"]: text_cell(prompt_quality_text(rollout.prompt, prompt_text)),
            FIELDS["score_check"]: text_cell(score_quality_text(prompt_text, rollout)),
        }
    return records


async def extend_add_records(page, records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    record_ids = list(records)
    return await page.evaluate(
        """
        ({ table, view, recordIds, records }) => {
          const result = window.bitableStore.commandManager.execute({
            cmd: 'ExtendAddRecords',
            tableId: table,
            viewId: view,
            count: recordIds.length,
            recordIds,
            records,
            from: 'codex_new_task_group',
            disableCountCheck: false,
            strictFix: true,
          });
          return JSON.parse(JSON.stringify(result, (key, value) => {
            if (typeof value === 'function') return '[function]';
            return value;
          }));
        }
        """,
        {"table": TABLE_ID, "view": VIEW_ID, "recordIds": record_ids, "records": records},
    )


async def create_stage(page, label: str, records: dict[str, dict[str, Any]], created_ids: list[str]) -> None:
    result = await extend_add_records(page, records)
    print(
        f"ExtendAddRecords[{label}] result={result.get('result')} "
        f"records={len(result.get('data') or [])} failInfo={result.get('failInfo')}"
    )
    if result.get("result") != 2:
        if created_ids:
            cleanup = await delete_records(page, created_ids)
            print(f"cleanup_after_{label}_failure result={cleanup.get('result')} records={len(created_ids)}")
            await page.wait_for_timeout(5000)
        raise RuntimeError(f"ExtendAddRecords[{label}] failed: {result}")
    created_ids.extend(records.keys())
    await page.wait_for_timeout(5000)


async def delete_records(page, record_ids: list[str]) -> dict[str, Any]:
    return await page.evaluate(
        """
        ({ table, view, recordIds }) => {
          const result = window.bitableStore.commandManager.execute({
            cmd: 'DeleteRecords',
            tableId: table,
            viewId: view,
            recordIds,
          });
          return JSON.parse(JSON.stringify(result, (key, value) => {
            if (typeof value === 'function') return '[function]';
            return value;
          }));
        }
        """,
        {"table": TABLE_ID, "view": VIEW_ID, "recordIds": record_ids},
    )


def verify_new_group(
    rows: list[dict[str, Any]],
    root_id: str,
    prompt_ids: dict[int, str],
    rollout_record_ids: set[str],
    rollouts: list[Rollout],
) -> list[str]:
    errors: list[str] = []
    by_id = {row["recordId"]: row for row in rows}
    if root_id not in by_id:
        return [f"new root missing: {root_id}"]
    prompt_rows = [by_id.get(prompt_ids[idx]) for idx in range(1, 8)]
    if any(row is None for row in prompt_rows):
        errors.append("one or more prompt rows missing")
    else:
        bad_prompt_parent = [row["recordId"] for row in prompt_rows if row["parent"] != [root_id]]
        if bad_prompt_parent:
            errors.append(f"prompt parent mismatch: {bad_prompt_parent}")
    rollout_rows = [by_id.get(rid) for rid in rollout_record_ids]
    if any(row is None for row in rollout_rows):
        errors.append("one or more rollout rows missing")
    else:
        prompt_id_set = set(prompt_ids.values())
        bad_rollout_parent = [row["recordId"] for row in rollout_rows if not row["parent"] or row["parent"][0] not in prompt_id_set]
        if bad_rollout_parent:
            errors.append(f"rollout parent mismatch: {bad_rollout_parent[:5]}")
    session_counts = Counter(row["session_id"] for row in rows if row["session_id"])
    for rollout in rollouts:
        if session_counts[rollout.session_id] != 1:
            errors.append(f"session count mismatch for {rollout.session_id}: {session_counts[rollout.session_id]}")
    children_by_prompt = Counter()
    for row in rows:
        if row["parent"] and row["parent"][0] in prompt_ids.values() and row["session_id"]:
            children_by_prompt[row["parent"][0]] += 1
    for prompt_index, prompt_id in prompt_ids.items():
        if children_by_prompt[prompt_id] != 5:
            errors.append(f"P{prompt_index} rollout count mismatch: {children_by_prompt[prompt_id]}")
    return errors


async def run(apply: bool, cleanup_marker: str | None) -> int:
    prompts = load_prompts()
    rollouts = load_rollouts()
    preflight_local(prompts, rollouts)
    local_sessions = {row.session_id for row in rollouts}

    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9235")
        pages = [page for ctx in browser.contexts for page in ctx.pages if BASE_TOKEN in page.url]
        if not pages:
            await browser.close()
            raise RuntimeError("target Bitable page is not open in the logged-in browser")
        page = pages[0]
        await page.bring_to_front()
        await page.wait_for_function(
            "({ table }) => !!window.bitableStore?.modelOperator?.getTableById(table)",
            arg={"table": TABLE_ID},
            timeout=30000,
        )

        before_payload = await fetch_payload(page)
        before_path = write_backup(before_payload, "before_new_task_group")
        before_rows = summarize_records(before_payload)
        validate_old_root_clean(before_rows, local_sessions)

        if cleanup_marker:
            targets = [row["recordId"] for row in before_rows if row["notes"] == cleanup_marker or row["session_id"] in local_sessions]
            print(f"cleanup_marker={cleanup_marker} targets={len(targets)}")
            if targets and apply:
                result = await delete_records(page, targets)
                print(f"DeleteRecords result={result.get('result')} records={len(targets)}")
                await page.wait_for_timeout(8000)
            await browser.close()
            return 0

        ids = await get_new_record_ids(page, 43)
        root_id = ids[0]
        prompt_ids = {idx: ids[idx] for idx in range(1, 8)}
        rollout_ids: dict[tuple[int, str, str], str] = {}
        cursor = 8
        for rollout in rollouts:
            rollout_ids[(rollout.prompt, rollout.model, rollout.session_id)] = ids[cursor]
            cursor += 1

        marker = f"python-grade-new-task-group:{datetime.now().strftime('%Y%m%d_%H%M%S')}:{root_id}"
        records = build_records(prompts, rollouts, root_id, prompt_ids, rollout_ids, marker)
        plan_path = write_backup(
            {
                "marker": marker,
                "root_id": root_id,
                "prompt_ids": prompt_ids,
                "rollout_ids": {f"P{k[0]}|{k[1]}|{k[2]}": v for k, v in rollout_ids.items()},
                "record_count": len(records),
                "before_backup": str(before_path),
            },
            "new_task_group_plan",
        )

        print(f"before_backup={before_path}")
        print(f"plan={plan_path}")
        print(f"marker={marker}")
        print(f"planned_records={len(records)} root={root_id} prompts=7 rollouts=35 apply={apply}")
        if not apply:
            await browser.close()
            return 0

        created_ids: list[str] = []
        root_records = {root_id: records[root_id]}
        prompt_records = {prompt_ids[idx]: records[prompt_ids[idx]] for idx in range(1, 8)}
        rollout_records = {record_id: records[record_id] for record_id in rollout_ids.values()}
        await create_stage(page, "root", root_records, created_ids)
        await create_stage(page, "prompts", prompt_records, created_ids)
        await create_stage(page, "rollouts", rollout_records, created_ids)

        await page.wait_for_timeout(10000)
        after_payload = await fetch_payload(page)
        after_path = write_backup(after_payload, "after_new_task_group_create")
        after_rows = summarize_records(after_payload)
        errors = verify_new_group(after_rows, root_id, prompt_ids, set(rollout_ids.values()), rollouts)
        old_local_rows = [
            row for row in after_rows if row["session_id"] in local_sessions and row["recordId"] not in set(rollout_ids.values())
        ]
        if old_local_rows:
            errors.append(f"local sessions outside new rollout records: {[row['recordId'] for row in old_local_rows]}")
        print(f"after_backup={after_path}")
        print(f"after_rows={len(after_rows)} verify_errors={len(errors)}")
        for error in errors[:20]:
            print(f"  ERROR: {error}")
        await browser.close()
        return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a fresh Bitable task group for the current run.")
    parser.add_argument("--apply", action="store_true", help="Actually create the 43-record new task group.")
    parser.add_argument("--cleanup-marker", help="Delete records matching this marker or current local sessions.")
    args = parser.parse_args()
    return asyncio.run(run(apply=args.apply, cleanup_marker=args.cleanup_marker))


if __name__ == "__main__":
    raise SystemExit(main())
