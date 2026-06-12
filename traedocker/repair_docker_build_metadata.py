#!/usr/bin/env python3
"""Generate/upload Docker build metadata for a fresh task root record."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

import submit_new_task_attachments as attachments
import submit_new_task_group as group


BASE_DIR = Path(__file__).resolve().parent


def text_cell(value: str) -> dict[str, Any]:
    return {"type": 1, "value": [{"type": "text", "text": value}]}


def number_cell(value: int) -> dict[str, Any]:
    return {"type": 2, "value": value}


def select_cell(field_name: str, label: str) -> dict[str, Any]:
    return {"type": 3, "value": group.OPT[field_name][label]}


def build_key(artifact_dir: Path) -> str:
    digest = hashlib.sha256()
    for rel in ["Dockerfile", "repo.zip"]:
        path = artifact_dir / rel
        if path.exists():
            digest.update(path.read_bytes())
    return digest.hexdigest()[:24]


def prepare_build_context(artifact_dir: Path) -> tempfile.TemporaryDirectory[str]:
    """Return a clean Docker build context matching the submitted repo.zip."""
    repo_zip = artifact_dir / "repo.zip"
    if not repo_zip.exists():
        raise FileNotFoundError(repo_zip)

    temp_dir = tempfile.TemporaryDirectory(prefix="trae-docker-build-")
    temp_path = Path(temp_dir.name)
    with zipfile.ZipFile(repo_zip) as archive:
        archive.extractall(temp_path)

    if not (temp_path / "Dockerfile").exists():
        dockerfile = artifact_dir / "Dockerfile"
        if not dockerfile.exists():
            temp_dir.cleanup()
            raise FileNotFoundError(dockerfile)
        (temp_path / "Dockerfile").write_bytes(dockerfile.read_bytes())

    repo_dir = temp_path / "repo"
    if not repo_dir.exists():
        temp_dir.cleanup()
        raise RuntimeError(f"{repo_zip} does not extract to a repo/ directory")
    if (repo_dir / ".git").exists():
        temp_dir.cleanup()
        raise RuntimeError(f"{repo_zip} unexpectedly contains repo/.git")

    return temp_dir


def run_docker_build(artifact_dir: Path, root_id: str, key: str, *, rebuild: bool) -> tuple[Path, str]:
    log_dir = artifact_dir / "build_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    attempt = 1
    while True:
        log_path = log_dir / f"{root_id.lower()}__{key}__attempt_{attempt}.log"
        if not log_path.exists():
            break
        attempt += 1
    tag = f"studentsystem-trial:metadata-{key}"
    with prepare_build_context(artifact_dir) as build_context:
        context_path = Path(build_context)
        command = [
            "docker",
            "build",
            "-f",
            str(context_path / "Dockerfile"),
            "-t",
            tag,
            str(context_path),
        ]
        if rebuild:
            command.insert(2, "--no-cache")

        started = datetime.now().isoformat(timespec="seconds")
        with log_path.open("w", encoding="utf-8") as handle:
            handle.write(f"$ {' '.join(command)}\n")
            handle.write(f"build_context={context_path}\n")
            handle.write(f"source_repo_zip={artifact_dir / 'repo.zip'}\n")
            handle.write(f"started_at={started}\n\n")
            handle.flush()
            result = subprocess.run(command, cwd=context_path, stdout=handle, stderr=subprocess.STDOUT, text=True)
            handle.write(f"\nexit_code={result.returncode}\n")
    if result.returncode != 0:
        raise RuntimeError(f"docker build failed; see {log_path}")
    subprocess.run(["docker", "image", "rm", tag], cwd=artifact_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    return log_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def apply_metadata(plan_path: Path, artifact_dir: Path, log_path: Path, built_at: str, key: str) -> int:
    plan = attachments.load_plan(plan_path)
    root_id = str(plan["root_id"])
    summary = (
        f"构建成功；retry_count=0；final_log={log_path.name}；"
        f"日志已上传：{log_path.name}"
    )

    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp(attachments.CDP_URL)
        pages = [page for ctx in browser.contexts for page in ctx.pages if group.BASE_TOKEN in page.url]
        if not pages:
            await browser.close()
            raise RuntimeError("target Bitable page is not open in the logged-in browser")
        page = pages[0]
        await page.bring_to_front()
        await page.wait_for_function(
            "({ table }) => !!window.bitableStore?.modelOperator?.getTableById(table)",
            arg={"table": group.TABLE_ID},
            timeout=30000,
        )

        payload = await attachments.fetch_payload(page)
        backup = group.write_backup(payload, "before_docker_build_metadata")
        record_map = attachments.summarize_by_id(payload)
        if root_id in group.PROTECTED_ROOT_IDS:
            raise RuntimeError("refusing to update old root record")
        if root_id not in record_map:
            raise RuntimeError(f"fresh root record missing: {root_id}")

        upload = await attachments.upload_drive_file(page, log_path)
        log_cell = attachments.attachment_cell(upload, log_path)
        updates = {
            group.FIELDS["docker_build_success"]: select_cell("docker_build_success", "true"),
            group.FIELDS["docker_build_status"]: select_cell("docker_build_status", "成功"),
            group.FIELDS["docker_build_log"]: log_cell,
            group.FIELDS["docker_build_error"]: text_cell(summary),
            group.FIELDS["docker_build_at"]: text_cell(built_at),
            group.FIELDS["docker_build_key"]: text_cell(key),
            group.FIELDS["docker_build_retry_count"]: number_cell(0),
        }
        result = await page.evaluate(
            """
            ({ table, view, rootId, updates }) => {
              const result = window.bitableStore.commandManager.execute({
                cmd: 'SetRecords',
                tableId: table,
                viewId: view,
                data: { [rootId]: updates },
                ignoreCheckRecordLoaded: true,
              });
              return JSON.parse(JSON.stringify(result, (key, value) => {
                if (typeof value === 'function') return '[function]';
                return value;
              }));
            }
            """,
            {"table": group.TABLE_ID, "view": group.VIEW_ID, "rootId": root_id, "updates": updates},
        )
        if result.get("result") != 2:
            raise RuntimeError(f"SetRecords failed: {result}")
        await page.wait_for_timeout(3000)

        after_payload = await attachments.fetch_payload(page)
        after_backup = group.write_backup(after_payload, "after_docker_build_metadata")
        after_root = attachments.summarize_by_id(after_payload)[root_id]
        errors: list[str] = []
        if log_path.name not in attachments.cell_files(after_root, "docker_build_log"):
            errors.append("docker_build_log attachment did not verify")
        for field_key in ["docker_build_error", "docker_build_at", "docker_build_key"]:
            if not group.unwrap_text(after_root.get(group.FIELDS[field_key])).strip():
                errors.append(f"{field_key} is still empty")

        print(f"before_backup={backup}")
        print(f"after_backup={after_backup}")
        print(f"root_id={root_id}")
        print(f"log_file={log_path}")
        print(f"log_token={upload['token']}")
        print(f"build_key={key}")
        print(f"build_at={built_at}")
        print(f"errors={len(errors)}")
        for error in errors:
            print(f"ERROR: {error}")
        await browser.close()
        return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair Docker build metadata on a fresh task root.")
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--artifact-dir", type=Path, default=BASE_DIR)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--rebuild", action="store_true", help="Use docker build --no-cache")
    args = parser.parse_args()

    artifact_dir = args.artifact_dir.resolve()
    plan_path = (args.plan or attachments.latest_plan_path()).resolve()
    key = build_key(artifact_dir)
    plan = attachments.load_plan(plan_path)
    root_id = str(plan["root_id"])
    print(f"plan={plan_path}")
    print(f"artifact_dir={artifact_dir}")
    print(f"root_id={root_id}")
    print(f"build_key={key}")
    if not args.apply:
        print("dry run only; pass --apply to build, upload log, and update fields")
        return 0

    log_path, built_at = run_docker_build(artifact_dir, root_id, key, rebuild=args.rebuild)
    return asyncio.run(apply_metadata(plan_path, artifact_dir, log_path, built_at, key))


if __name__ == "__main__":
    raise SystemExit(main())
