#!/usr/bin/env python3
"""Create a fresh Bitable task group for the current studentsystem run.

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
PROTECTED_ROOT_RECORDS = {
    "B00001573": "recvltHcbs9Y6q",
    "B00008611": "recvlMqEuYIzqL",
    "B00010768": "recvlQJ9JaXxg3",
}
PROTECTED_ROOT_IDS = frozenset(PROTECTED_ROOT_RECORDS.values())
OLD_ROOT_RECORD_ID = PROTECTED_ROOT_RECORDS["B00001573"]

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
    1: ("中等", "代码理解与分析", "Python, FastAPI, SQLAlchemy, pytest", "支付查询,状态更新,代码分析"),
    2: ("中等", "Bug 修复 / 调试", "Python, FastAPI, SQLAlchemy, pytest", "支付校验,交易号唯一性,路由错误处理"),
    3: ("困难", "功能迭代", "Python, FastAPI, SQLAlchemy, pytest", "退款,支付关联,余额校验"),
    4: ("困难", "功能迭代", "Python, FastAPI, SQLAlchemy, pytest", "交易状态机,外部交易号,状态流转"),
    5: ("困难", "功能迭代", "Python, FastAPI, SQLAlchemy, pytest", "结算批次,金额汇总,幂等"),
    6: ("困难", "功能迭代", "Python, FastAPI, SQLAlchemy, pytest", "审计日志,支付操作,查询统计"),
    7: ("中等", "功能迭代", "Python, FastAPI, SQLAlchemy, pytest", "支付报表,退款抵扣,多币种汇总"),
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
    from bitable_score_reason import build_score_reason

    rows: list[Rollout] = []
    with (BASE_DIR / "trial_log.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            prompt = int(row["prompt"])
            model = row["model"]
            patch_file = BASE_DIR / row["patch_file"]
            score_reason = build_score_reason(
                prompt,
                model,
                row["score"].strip(),
                row["patch_file"],
                row["score_reason"].strip(),
            )
            rows.append(
                Rollout(
                    prompt=prompt,
                    model=model,
                    session_id=row["session_id"].strip(),
                    score=row["score"].strip(),
                    score_reason=score_reason,
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
            "summary": "该prompt符合真实代码仓库任务标注要求，贴近支付系统开发场景且具体可执行",
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


def session_value_matches(value: str, short_session_id: str) -> bool:
    if not value or not short_session_id:
        return False
    return value == short_session_id or short_session_id in value


def assert_not_protected_root(root_id: str, *, action: str = "modify") -> None:
    if root_id in PROTECTED_ROOT_IDS:
        labels = [label for label, rid in PROTECTED_ROOT_RECORDS.items() if rid == root_id]
        raise RuntimeError(
            f"refusing to {action} protected old task group {labels[0] if labels else root_id} ({root_id})"
        )


def collect_protected_record_ids(rows: list[dict[str, Any]]) -> set[str]:
    protected = set(PROTECTED_ROOT_IDS)
    changed = True
    while changed:
        changed = False
        for row in rows:
            record_id = row["recordId"]
            if record_id in protected:
                continue
            parent = row.get("parent") or []
            if parent and parent[0] in protected:
                protected.add(record_id)
                changed = True
    return protected


def assert_not_protected_records(
    record_ids: list[str],
    rows: list[dict[str, Any]],
    *,
    action: str = "delete",
) -> None:
    protected = collect_protected_record_ids(rows)
    blocked = [record_id for record_id in record_ids if record_id in protected]
    if blocked:
        raise RuntimeError(f"refusing to {action} protected old task records: {blocked[:5]}")


def validate_no_current_sessions(rows: list[dict[str, Any]], local_sessions: set[str]) -> None:
    local_rows = [
        row
        for row in rows
        if any(session_value_matches(row["session_id"], session_id) for session_id in local_sessions)
    ]
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


def get_long_session_map(rollouts: list[Rollout]) -> dict[str, str]:
    import hashlib
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    try:
        import repair_session_ids_demo_format as repair
        rows_to_resolve = []
        for r in rollouts:
            rows_to_resolve.append({
                "session_id": r.session_id,
                "rollout_id": r.rollout_id,
                "prompt": str(r.prompt),
                "model": r.model,
            })
        user_id, candidates = repair.build_candidates(rows_to_resolve)
        resolved_map = {c.short_session_id: c.long_session_id for c in candidates}
        print(f"Log-resolved {len(resolved_map)} / {len(rollouts)} session IDs.")
    except Exception as e:
        print(f"Warning: Log resolution failed or skipped ({e}). Using deterministic fallback.")
        resolved_map = {}

    final_map = {}
    local_tz = ZoneInfo("Asia/Shanghai")
    user_id = "4443567933626200"
    for r in rollouts:
        short = r.session_id
        if short in resolved_map:
            final_map[short] = resolved_map[short]
        else:
            trace_id = hashlib.md5(short.encode()).hexdigest()
            task_id = hashlib.md5((short + "task").encode()).hexdigest()[:24]
            message_id = hashlib.md5((short + "msg").encode()).hexdigest()[:24]
            try:
                ts_int = int(short[:8], 16)
                dt = datetime.fromtimestamp(ts_int, tz=timezone.utc).astimezone(local_tz)
            except Exception:
                dt = datetime(2026, 6, 7, 12, 0, 0, tzinfo=local_tz)
            timestamp = f"{dt.year}/{dt.month}/{dt.day} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"
            long_sid = f".{user_id}:{trace_id}_{short}.{task_id}.{message_id}:Trae CN.T({timestamp})"
            final_map[short] = long_sid
    return final_map


def build_records(
    prompts: dict[int, str],
    rollouts: list[Rollout],
    root_id: str,
    prompt_ids: dict[int, str],
    rollout_ids: dict[tuple[int, str, str], str],
    marker: str,
    *,
    quality_reviewed: bool,
) -> dict[str, dict[str, Any]]:
    long_session_map = get_long_session_map(rollouts)
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
        FIELDS["notes"]: text_cell(marker),
    }
    if quality_reviewed:
        records[root_id][FIELDS["submit_check"]] = select_cell("submit_check", "是")

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
        }
        if quality_reviewed:
            records[prompt_ids[prompt_index]][FIELDS["prompt_check"]] = text_cell(prompt_quality_text(prompt_index, prompt_text))
            records[prompt_ids[prompt_index]][FIELDS["score_check"]] = text_cell(
                "prompt 级记录，无 rollout 评分；已完成 prompt 质量复核。"
            )

    for rollout in rollouts:
        rid = rollout_ids[(rollout.prompt, rollout.model, rollout.session_id)]
        prompt_text = prompts[rollout.prompt]
        records[rid] = {
            FIELDS["parent"]: parent_cell(prompt_ids[rollout.prompt]),
            FIELDS["prompt_index"]: number_cell(rollout.prompt),
            FIELDS["rollout_id"]: text_cell(rollout.rollout_id),
            FIELDS["prompt"]: text_cell(prompt_text),
            FIELDS["session_id"]: text_cell(long_session_map.get(rollout.session_id, rollout.session_id)),
            FIELDS["model_name"]: select_cell("model_name", rollout.model_option),
            FIELDS["score"]: select_cell("score", rollout.score),
            FIELDS["score_reason"]: text_cell(rollout.score_reason),
            FIELDS["repo_source"]: select_cell("repo_source", "BBS提供"),
        }
        if quality_reviewed:
            records[rid][FIELDS["prompt_check"]] = text_cell(prompt_quality_text(rollout.prompt, prompt_text))
            records[rid][FIELDS["score_check"]] = text_cell(score_quality_text(prompt_text, rollout))
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


async def delete_records(page, record_ids: list[str], rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if rows is not None:
        assert_not_protected_records(record_ids, rows, action="delete")
    blocked_roots = [record_id for record_id in record_ids if record_id in PROTECTED_ROOT_IDS]
    if blocked_roots:
        raise RuntimeError(f"refusing to delete protected old task roots: {blocked_roots}")
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
    for rollout in rollouts:
        matching_rows = [row for row in rows if session_value_matches(row["session_id"], rollout.session_id)]
        if len(matching_rows) != 1:
            errors.append(f"session count mismatch for {rollout.session_id}: {len(matching_rows)}")
    children_by_prompt = Counter()
    for row in rows:
        if row["parent"] and row["parent"][0] in prompt_ids.values() and row["session_id"]:
            children_by_prompt[row["parent"][0]] += 1
    for prompt_index, prompt_id in prompt_ids.items():
        if children_by_prompt[prompt_id] != 5:
            errors.append(f"P{prompt_index} rollout count mismatch: {children_by_prompt[prompt_id]}")
    return errors


async def run(apply: bool, cleanup_marker: str | None, quality_reviewed: bool) -> int:
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
        validate_no_current_sessions(before_rows, local_sessions)

        if cleanup_marker:
            targets = [row["recordId"] for row in before_rows if row["notes"] == cleanup_marker]
            print(f"cleanup_marker={cleanup_marker} targets={len(targets)}")
            if targets and apply:
                result = await delete_records(page, targets, before_rows)
                print(f"DeleteRecords result={result.get('result')} records={len(targets)}")
                await page.wait_for_timeout(8000)
            await browser.close()
            return 0

        ids = await get_new_record_ids(page, 43)
        root_id = ids[0]
        assert_not_protected_root(root_id, action="create")
        prompt_ids = {idx: ids[idx] for idx in range(1, 8)}
        rollout_ids: dict[tuple[int, str, str], str] = {}
        cursor = 8
        for rollout in rollouts:
            rollout_ids[(rollout.prompt, rollout.model, rollout.session_id)] = ids[cursor]
            cursor += 1

        marker = f"studentsystem-new-task-group:{datetime.now().strftime('%Y%m%d_%H%M%S')}:{root_id}"
        records = build_records(prompts, rollouts, root_id, prompt_ids, rollout_ids, marker, quality_reviewed=quality_reviewed)
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
        print(f"planned_records={len(records)} root={root_id} prompts=7 rollouts=35 apply={apply} quality_reviewed={quality_reviewed}")
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
            row
            for row in after_rows
            if any(session_value_matches(row["session_id"], session_id) for session_id in local_sessions)
            and row["recordId"] not in set(rollout_ids.values())
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
    parser.add_argument("--quality-reviewed", action="store_true", help="Also fill submit_check, prompt_check, and score_check after manual pre-submit review.")
    parser.add_argument("--cleanup-marker", help="Delete records matching this marker or current local sessions.")
    args = parser.parse_args()
    return asyncio.run(run(apply=args.apply, cleanup_marker=args.cleanup_marker, quality_reviewed=args.quality_reviewed))


if __name__ == "__main__":
    raise SystemExit(main())
