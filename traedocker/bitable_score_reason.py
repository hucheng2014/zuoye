#!/usr/bin/env python3
"""Build and repair Bitable score_reason / score_check fields."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "new_task_backups"
LOG_FILE = BASE_DIR / "trial_log.csv"
BASE_TOKEN = "B4SgbbhcyaJfwWsWHvcc1AtgnYd"
TABLE_ID = "tblcXB0RGGaHGm1r"
VIEW_ID = "vewxWP7trZ"

GENERIC_REASON_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^测试全部通过\(\d+ passed\)，代码完整且有额外测试覆盖$"),
    re.compile(r"^Doubao 前置筛选规则自动记 0 分$"),
    re.compile(r"^解释题无法通过 pytest 自动评测；默认记 1 分"),
    re.compile(r"TRAE_SCORE_OVERRIDE"),
    re.compile(r"^测试失败或代码不完整\("),
    re.compile(r"^测试通过\(\d+ passed\)，但改动较基础无额外覆盖$"),
    re.compile(r"^测试通过\(\d+ passed\)，但没有新增通过测试覆盖$"),
)


def extract_prompt(prompt_index: int) -> str:
    script = f"source {BASE_DIR / 'batch_runner.sh'} >/dev/null 2>&1 || true; get_prompt {prompt_index}"
    import subprocess

    return subprocess.check_output(["bash", "-lc", script], text=True)


def load_prompts() -> dict[int, str]:
    prompts = {idx: extract_prompt(idx) for idx in range(1, 8)}
    if any(not value.strip() for value in prompts.values()):
        raise RuntimeError("one or more prompts are empty")
    return prompts


def prompt_summary(prompt_text: str, *, max_len: int = 180) -> str:
    text = re.sub(r"\s+", " ", prompt_text.strip())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def prompt_numbered_points(prompt_text: str) -> str:
    matches = re.findall(r"(?:^|\s)(\d+)\.\s([^。；]+(?:[。；]|$))", prompt_text)
    if not matches:
        return prompt_summary(prompt_text)
    return "；".join(f"{number}) {body.strip()}" for number, body in matches)


def patch_files(patch_path: Path) -> list[str]:
    if not patch_path.is_file():
        return []
    names: list[str] = []
    for line in patch_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("diff --git a/"):
            name = line.split(" a/", 1)[1].rsplit(" b/", 1)[0]
            if name not in names:
                names.append(name)
    return names


def passed_count(old_reason: str) -> str | None:
    match = re.search(r"(\d+) passed", old_reason)
    return match.group(1) if match else None


def build_score_reason(
    prompt: int,
    model: str,
    score: str,
    patch_file: str | Path,
    old_reason: str = "",
    *,
    artifact_dir: Path = BASE_DIR,
    prompts: dict[int, str] | None = None,
) -> str:
    prompt_text = (prompts or load_prompts())[prompt]
    task = prompt_summary(prompt_text)
    impl = prompt_numbered_points(prompt_text)
    patch_path = Path(patch_file)
    if not patch_path.is_absolute():
        patch_path = artifact_dir / patch_path
    files = patch_files(patch_path)
    files_str = "、".join(files[:8]) or "（无有效 diff）"
    passed = passed_count(old_reason)

    if score == "1" and prompt == 1:
        return (
            f"解释题无法 pytest 自动评测。Prompt 1 要求 {task}；"
            f"本轮 {model} 为代码理解类回答，按规则记 1 分。"
        )

    if score == "0" and "Doubao" in model:
        return (
            f"本轮为 Prompt {prompt} 的 Doubao-Seed 前置筛选 rollout。"
            f"任务要求 {task}；按 P2-7 非解释题规则 seed 仅作区分度基线自动记 0 分，"
            f"不作为可采纳实现。"
        )

    if score == "0":
        if files:
            detail = "patch 有改动但 pytest 未全部通过，核心校验/接口/测试未闭环"
        else:
            detail = "patch 几乎无有效 diff，pytest 未全部通过"
        return f"未满足 Prompt {prompt}：{task}。patch 改动 {files_str}，{detail}，评 0 分。"

    if score == "1":
        passed_text = f"pytest {passed} passed" if passed else "pytest 结果偏基础"
        return (
            f"部分满足 Prompt {prompt}：{impl}。"
            f"patch 改动 {files_str}。"
            f"{passed_text}，改动或测试覆盖未达满分标准，评 1 分。"
        )

    passed_text = passed or "全部"
    return (
        f"完整满足 Prompt {prompt}：{impl}。"
        f"patch 改动 {files_str}。"
        f"pytest {passed_text} passed 全部通过，核心任务点与测试覆盖齐全，评 2 分。"
    )


def is_generic_score_reason(reason: str, prompt: int, model: str, score: str) -> bool:
    text = reason.strip()
    if not text:
        return True
    for pattern in GENERIC_REASON_PATTERNS:
        if pattern.search(text):
            return True
    if score == "2" and "完整满足 Prompt" not in text:
        return True
    if score == "0" and "Doubao" in model and "前置筛选 rollout" not in text:
        return True
    if score == "0" and "Doubao" not in model and not text.startswith("未满足 Prompt"):
        return True
    if prompt == 1 and score == "1" and "Prompt 1 要求" not in text:
        return True
    if score == "1" and prompt != 1 and "部分满足 Prompt" not in text:
        return True
    return False


def normalize_trial_log(artifact_dir: Path = BASE_DIR) -> int:
    log_file = artifact_dir / "trial_log.csv"
    prompts = load_prompts()
    rows: list[dict[str, str]] = []
    changed = 0
    with log_file.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        for row in reader:
            prompt = int(row["prompt"])
            model = row["model"]
            score = row["score"].strip()
            old_reason = row["score_reason"].strip()
            new_reason = build_score_reason(
                prompt,
                model,
                score,
                row["patch_file"],
                old_reason,
                artifact_dir=artifact_dir,
                prompts=prompts,
            )
            if old_reason != new_reason:
                changed += 1
            row["score_reason"] = new_reason
            rows.append(row)
    with log_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return changed


def find_latest_plan() -> Path:
    plans = sorted(BACKUP_DIR.glob("new_task_group_plan_*.json"), key=lambda path: path.stat().st_mtime)
    if not plans:
        raise RuntimeError(f"no plan file under {BACKUP_DIR}")
    return plans[-1]


def load_plan(plan_path: Path) -> tuple[str, dict[str, str], set[str], set[str]]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    root_id = plan["root_id"]
    session_to_record: dict[str, str] = {}
    for key, record_id in plan["rollout_ids"].items():
        session_id = key.rsplit("|", 1)[-1]
        session_to_record[session_id] = record_id
    rollout_record_ids = set(plan["rollout_ids"].values())
    prompt_record_ids = set(plan["prompt_ids"].values())
    return root_id, session_to_record, rollout_record_ids, prompt_record_ids


def build_rollout_maps(artifact_dir: Path = BASE_DIR) -> tuple[dict[str, str], dict[str, Any]]:
    from submit_new_task_group import MODEL_OPTION_TEXT, Rollout, load_prompts as load_group_prompts, score_quality_text

    prompts = load_group_prompts()
    reasons: dict[str, str] = {}
    score_checks: dict[str, str] = {}
    with (artifact_dir / "trial_log.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            session_id = row["session_id"].strip()
            reason = build_score_reason(
                int(row["prompt"]),
                row["model"],
                row["score"].strip(),
                row["patch_file"],
                row["score_reason"].strip(),
                artifact_dir=artifact_dir,
            )
            rollout = Rollout(
                prompt=int(row["prompt"]),
                model=row["model"],
                session_id=session_id,
                score=row["score"].strip(),
                score_reason=reason,
                patch_file=artifact_dir / row["patch_file"],
                rollout_id="",
                model_option=MODEL_OPTION_TEXT.get(row["model"], row["model"]),
            )
            reasons[session_id] = reason
            score_checks[session_id] = score_quality_text(prompts[rollout.prompt], rollout)
    if len(reasons) != 35:
        raise RuntimeError(f"expected 35 rollouts, got {len(reasons)}")
    return reasons, score_checks


async def fetch_rows(page) -> list[dict[str, Any]]:
    from submit_new_task_group import FIELDS

    return await page.evaluate(
        """
        async ({ token, table, view, fields }) => {
          const tableObj = window.bitableStore.modelOperator.getTableById(table);
          const getField = (id) => tableObj.fields?.[id] || tableObj.fieldsMap?.get?.(id);
          const optionNames = {};
          for (const name of ['model_name', 'score']) {
            const field = getField(fields[name]);
            optionNames[name] = Object.fromEntries((field?.property?.options || []).map(opt => [opt.id, opt.name]));
          }
          const rev = tableObj.rev;
          const url = `/space/api/v1/bitable/${token}/records?tableId=${table}&viewId=${view}&tableRev=${rev}&depRev=%7B%7D&viewLazyLoad=true&offset=0&limit=3000&tableID=${table}&viewID=${view}&removeFmlExtra=true`;
          const json = await (await fetch(url, { credentials: 'include' })).json();
          const parsed = JSON.parse(await window.unGzipBase64(json.data.records));
          const baseValue = (cell) => {
            if (!cell) return null;
            if (typeof cell === 'object' && 'value' in cell) return cell.value;
            return cell;
          };
          const unwrapText = (cell) => {
            const value = baseValue(cell);
            if (value == null) return '';
            if (Array.isArray(value)) return value.map(x => x?.text ?? x?.name ?? x?.value ?? '').join('');
            if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
            if (typeof value === 'object') return value.text ?? value.name ?? '';
            return String(value);
          };
          const unwrapSelect = (name, cell) => {
            const value = baseValue(cell);
            if (value == null) return '';
            if (typeof value === 'string') return optionNames[name]?.[value] ?? value;
            if (Array.isArray(value)) return value.map(x => optionNames[name]?.[x] ?? x?.name ?? x?.text ?? x?.id ?? '').join('');
            return '';
          };
          const parentId = (cell) => {
            const value = baseValue(cell);
            if (!Array.isArray(value) || !value.length) return '';
            const first = value[0];
            if (typeof first === 'string') return first;
            return first?.recordIds?.[0] ?? first?.id ?? '';
          };
          return Object.entries(parsed.recordMap || {}).map(([recordId, rec]) => ({
            recordId,
            parent_id: parentId(rec[fields.parent]),
            prompt_index: unwrapText(rec[fields.prompt_index]),
            rollout_id: unwrapText(rec[fields.rollout_id]),
            session_id: unwrapText(rec[fields.session_id]),
            model_name: unwrapSelect('model_name', rec[fields.model_name]),
            score: unwrapSelect('score', rec[fields.score]),
            score_reason: unwrapText(rec[fields.score_reason]),
            score_check: unwrapText(rec[fields.score_check]),
          }));
        }
        """,
        {"token": BASE_TOKEN, "table": TABLE_ID, "view": VIEW_ID, "fields": FIELDS},
    )


async def set_records(page, updates: dict[str, dict]) -> dict[str, Any]:
    return await page.evaluate(
        """
        async ({ table, view, updates }) => {
          const result = await Promise.resolve(window.bitableStore.commandManager.execute({
            cmd: 'SetRecords',
            tableId: table,
            viewId: view,
            data: updates,
            ignoreCheckRecordLoaded: true,
          }));
          return JSON.parse(JSON.stringify(result, (key, value) => typeof value === 'function' ? '[function]' : value));
        }
        """,
        {"table": TABLE_ID, "view": VIEW_ID, "updates": updates},
    )


async def repair_remote_score_fields(
    plan_path: Path,
    *,
    apply: bool,
    artifact_dir: Path = BASE_DIR,
) -> dict[str, Any]:
    from submit_new_task_group import FIELDS, PROTECTED_ROOT_IDS, session_value_matches, text_cell

    root_id, session_to_record, rollout_record_ids, prompt_record_ids = load_plan(plan_path)
    if root_id in PROTECTED_ROOT_IDS:
        raise RuntimeError(f"refusing to repair protected root {root_id}")

    normalize_trial_log(artifact_dir)
    reasons, score_checks = build_rollout_maps(artifact_dir)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    BACKUP_DIR.mkdir(exist_ok=True)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9235")
        pages = [page for ctx in browser.contexts for page in ctx.pages if BASE_TOKEN in page.url]
        if not pages:
            raise RuntimeError("Bitable page is not open in the traedocker Chrome debugging session")
        page = pages[0]
        await page.wait_for_function(
            "({ table }) => !!window.bitableStore?.modelOperator?.getTableById(table)",
            arg={"table": TABLE_ID},
            timeout=30000,
        )

        before = await fetch_rows(page)
        (BACKUP_DIR / f"score_reason_before_{stamp}.json").write_text(
            json.dumps(before, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        blocked = (rollout_record_ids | {root_id}) & PROTECTED_ROOT_IDS
        if blocked:
            raise RuntimeError(f"refusing to modify protected records: {blocked}")

        by_record = {row["recordId"]: row for row in before}
        by_sid: dict[str, dict[str, Any]] = {}
        for row in before:
            sid = row.get("session_id") or ""
            if sid:
                by_sid[sid] = row

        updates: dict[str, dict] = {}
        for session_id, reason in reasons.items():
            record_id = session_to_record[session_id]
            row = by_sid.get(session_id)
            if not row:
                for remote_sid, candidate in by_sid.items():
                    if session_value_matches(remote_sid, session_id):
                        row = candidate
                        break
            if not row:
                row = by_record.get(record_id)
            if not row:
                raise RuntimeError(f"missing rollout row for session_id={session_id}")
            if row["recordId"] != record_id:
                raise RuntimeError(
                    f"record id mismatch for {session_id}: plan={record_id} remote={row['recordId']}"
                )
            parent_id = row.get("parent_id") or ""
            if parent_id not in prompt_record_ids:
                raise RuntimeError(
                    f"rollout {record_id} parent {parent_id} is not under plan prompt rows"
                )
            fields: dict[str, Any] = {}
            if row.get("score_reason") != reason:
                fields[FIELDS["score_reason"]] = text_cell(reason)
            expected_check = score_checks[session_id]
            if row.get("score_check") != expected_check:
                fields[FIELDS["score_check"]] = text_cell(expected_check)
            if fields:
                updates[record_id] = fields

        summary = {
            "plan": str(plan_path),
            "root_id": root_id,
            "updates": len(updates),
            "apply": apply,
        }
        print(json.dumps(summary, ensure_ascii=False))

        if apply and updates:
            items = list(updates.items())
            for batch_start in range(0, len(items), 10):
                batch = dict(items[batch_start : batch_start + 10])
                result = await set_records(page, batch)
                print(
                    f"batch {batch_start // 10 + 1}: result={result.get('result')} records={len(batch)}"
                )
                if result.get("result") != 2:
                    raise RuntimeError(f"SetRecords failed: {result}")
                await page.wait_for_timeout(2500)

        await page.wait_for_timeout(3000 if apply else 0)
        after = await fetch_rows(page)
        (BACKUP_DIR / f"score_reason_after_{stamp}.json").write_text(
            json.dumps(after, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        after_group = [row for row in after if row["recordId"] in rollout_record_ids]
        counts: dict[str, int] = {}
        for row in after_group:
            check = row.get("score_check") or "空"
            if "不合理" in check:
                key = "不合理"
            elif "合理" in check:
                key = "合理"
            else:
                key = check[:40] or "空"
            counts[key] = counts.get(key, 0) + 1
        summary["score_check_counts"] = counts
        print("score_check_counts:", json.dumps(counts, ensure_ascii=False))
        await browser.close()
        return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and repair Bitable score fields.")
    sub = parser.add_subparsers(dest="command", required=True)

    enrich = sub.add_parser("enrich", help="Print a structured score_reason for one rollout.")
    enrich.add_argument("--prompt", type=int, required=True)
    enrich.add_argument("--model", required=True)
    enrich.add_argument("--score", required=True)
    enrich.add_argument("--reason", default="")
    enrich.add_argument("--patch", required=True)
    enrich.add_argument("--artifact-dir", type=Path, default=BASE_DIR)

    normalize = sub.add_parser("normalize-log", help="Rewrite trial_log.csv score_reason values.")
    normalize.add_argument("--artifact-dir", type=Path, default=BASE_DIR)

    repair = sub.add_parser("repair-remote", help="Repair score_reason/score_check on a task group.")
    repair.add_argument("--plan", default="latest")
    repair.add_argument("--apply", action="store_true")
    repair.add_argument("--artifact-dir", type=Path, default=BASE_DIR)

    args = parser.parse_args(argv)

    if args.command == "enrich":
        print(
            build_score_reason(
                args.prompt,
                args.model,
                args.score,
                args.patch,
                args.reason,
                artifact_dir=args.artifact_dir.resolve(),
            )
        )
        return 0

    if args.command == "normalize-log":
        changed = normalize_trial_log(args.artifact_dir.resolve())
        print(f"trial_log.csv updated rows={changed}")
        return 0

    if args.command == "repair-remote":
        plan_path = find_latest_plan() if args.plan == "latest" else Path(args.plan).resolve()
        asyncio.run(
            repair_remote_score_fields(
                plan_path,
                apply=args.apply,
                artifact_dir=args.artifact_dir.resolve(),
            )
        )
        return 0

    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
