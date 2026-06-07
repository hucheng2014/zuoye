#!/usr/bin/env python3
"""Sanitized Feishu/Lark Bitable OpenAPI sync skeleton.

Default mode is dry-run: it reads schema and records, computes creates/updates,
and prints a plan. Use --apply to write changes. Use --offline-plan to validate
local files without any network calls.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


JsonObject = dict[str, Any]


class SyncError(RuntimeError):
    """Raised for expected sync/configuration failures."""


@dataclass(frozen=True)
class SyncConfig:
    api_base_url: str
    auth: JsonObject
    bitable: JsonObject
    sync: JsonObject

    @property
    def app_token(self) -> str:
        return require_non_placeholder(self.bitable.get("app_token"), "bitable.app_token")

    @property
    def table_id(self) -> str:
        return require_non_placeholder(self.bitable.get("table_id"), "bitable.table_id")

    @property
    def view_id(self) -> str:
        return str(self.bitable.get("view_id") or "")

    @property
    def unique_key(self) -> str:
        value = self.sync.get("unique_key")
        if not isinstance(value, str) or not value:
            raise SyncError("sync.unique_key must be a non-empty string")
        return value

    @property
    def batch_size(self) -> int:
        value = int(self.sync.get("batch_size", 100))
        if value < 1:
            raise SyncError("sync.batch_size must be positive")
        return min(value, 500)

    @property
    def field_mapping(self) -> JsonObject:
        value = self.sync.get("field_mapping")
        if not isinstance(value, dict) or not value:
            raise SyncError("sync.field_mapping must be a non-empty object")
        return value

    @property
    def compare_fields(self) -> list[str]:
        configured = self.sync.get("compare_fields")
        if configured is None:
            return list(self.field_mapping.keys())
        if not isinstance(configured, list) or not all(isinstance(item, str) for item in configured):
            raise SyncError("sync.compare_fields must be a list of strings")
        return configured


class FeishuClient:
    def __init__(self, config: SyncConfig) -> None:
        self.config = config
        self.base_url = config.api_base_url.rstrip("/")
        self._tenant_access_token: str | None = None

    def tenant_access_token(self) -> str:
        if self._tenant_access_token:
            return self._tenant_access_token

        token_env = self.config.auth.get("tenant_access_token_env")
        if token_env:
            token = os.getenv(str(token_env))
            if token:
                self._tenant_access_token = token
                return token

        app_id_env = self.config.auth.get("app_id_env")
        app_secret_env = self.config.auth.get("app_secret_env")
        app_id = os.getenv(str(app_id_env)) if app_id_env else None
        app_secret = os.getenv(str(app_secret_env)) if app_secret_env else None
        if not app_id or not app_secret:
            raise SyncError(
                "missing credentials: set the configured tenant token env var "
                "or both app_id/app_secret env vars"
            )

        response = self.request(
            "POST",
            "/open-apis/auth/v3/tenant_access_token/internal",
            json_body={"app_id": app_id, "app_secret": app_secret},
            authenticated=False,
        )
        token = response.get("tenant_access_token")
        if not isinstance(token, str) or not token:
            raise SyncError("tenant token response did not contain tenant_access_token")
        self._tenant_access_token = token
        return token

    def request(
        self,
        method: str,
        path: str,
        *,
        query: JsonObject | None = None,
        json_body: JsonObject | None = None,
        authenticated: bool = True,
        retry: int = 2,
    ) -> JsonObject:
        url = f"{self.base_url}{path}"
        if query:
            clean_query = {key: value for key, value in query.items() if value not in (None, "")}
            if clean_query:
                url = f"{url}?{urllib.parse.urlencode(clean_query)}"

        headers = {"Content-Type": "application/json; charset=utf-8"}
        if authenticated:
            headers["Authorization"] = f"Bearer {self.tenant_access_token()}"

        data = None
        if json_body is not None:
            data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")

        for attempt in range(retry + 1):
            request = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                if exc.code in (429, 500, 502, 503, 504) and attempt < retry:
                    time.sleep(1 + attempt)
                    continue
                raise SyncError(f"HTTP {exc.code} for {method} {path}: {body}") from exc
            except urllib.error.URLError as exc:
                if attempt < retry:
                    time.sleep(1 + attempt)
                    continue
                raise SyncError(f"request failed for {method} {path}: {exc}") from exc

            code = payload.get("code", 0)
            if code != 0:
                raise SyncError(f"OpenAPI error for {method} {path}: code={code} msg={payload.get('msg')}")
            data_payload = payload.get("data")
            return data_payload if isinstance(data_payload, dict) else payload

        raise SyncError(f"request failed for {method} {path}")

    def list_fields(self) -> list[JsonObject]:
        fields: list[JsonObject] = []
        page_token = ""
        while True:
            data = self.request(
                "GET",
                f"/open-apis/bitable/v1/apps/{self.config.app_token}/tables/{self.config.table_id}/fields",
                query={"page_size": 100, "page_token": page_token, "view_id": self.config.view_id},
            )
            fields.extend(data.get("items", []))
            if not data.get("has_more"):
                return fields
            page_token = str(data.get("page_token") or "")

    def list_records(self) -> list[JsonObject]:
        records: list[JsonObject] = []
        page_token = ""
        while True:
            data = self.request(
                "GET",
                f"/open-apis/bitable/v1/apps/{self.config.app_token}/tables/{self.config.table_id}/records",
                query={
                    "page_size": 500,
                    "page_token": page_token,
                    "view_id": self.config.view_id,
                    "field_names": "false",
                },
            )
            records.extend(data.get("items", []))
            if not data.get("has_more"):
                return records
            page_token = str(data.get("page_token") or "")

    def batch_create(self, records: list[JsonObject]) -> None:
        for chunk in chunks(records, self.config.batch_size):
            self.request(
                "POST",
                f"/open-apis/bitable/v1/apps/{self.config.app_token}/tables/{self.config.table_id}/records/batch_create",
                query={"field_names": "false"},
                json_body={"records": chunk},
            )

    def batch_update(self, records: list[JsonObject]) -> None:
        for chunk in chunks(records, self.config.batch_size):
            self.request(
                "POST",
                f"/open-apis/bitable/v1/apps/{self.config.app_token}/tables/{self.config.table_id}/records/batch_update",
                query={"field_names": "false"},
                json_body={"records": chunk},
            )


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_config(path: str) -> SyncConfig:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise SyncError("config file must contain a JSON object")
    return SyncConfig(
        api_base_url=str(payload.get("api_base_url") or "https://open.feishu.cn"),
        auth=expect_object(payload.get("auth"), "auth"),
        bitable=expect_object(payload.get("bitable"), "bitable"),
        sync=expect_object(payload.get("sync"), "sync"),
    )


def load_records(path: str) -> list[JsonObject]:
    payload = load_json(path)
    records = payload.get("records") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise SyncError("data file must contain a records list")
    for index, record in enumerate(records):
        if not isinstance(record, dict) or not isinstance(record.get("fields"), dict):
            raise SyncError(f"records[{index}] must contain a fields object")
    return records


def expect_object(value: Any, path: str) -> JsonObject:
    if not isinstance(value, dict):
        raise SyncError(f"{path} must be an object")
    return value


def require_non_placeholder(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SyncError(f"{path} must be a non-empty string")
    if "PLACEHOLDER" in value:
        raise SyncError(f"{path} still contains a placeholder")
    return value


def resolve_field_ids(config: SyncConfig, remote_fields: list[JsonObject]) -> dict[str, str]:
    by_name: dict[str, JsonObject] = {}
    by_id: dict[str, JsonObject] = {}
    for field in remote_fields:
        field_id = field.get("field_id")
        field_name = field.get("field_name") or field.get("name")
        if isinstance(field_id, str):
            by_id[field_id] = field
        if isinstance(field_name, str):
            by_name[field_name] = field

    resolved: dict[str, str] = {}
    for logical_name, spec in config.field_mapping.items():
        if isinstance(spec, str):
            spec = {"field_name": spec}
        if not isinstance(spec, dict):
            raise SyncError(f"sync.field_mapping.{logical_name} must be an object or string")

        field_id = spec.get("field_id")
        field_id_env = spec.get("field_id_env")
        field_name = spec.get("field_name")
        if field_id_env:
            field_id = os.getenv(str(field_id_env))

        if isinstance(field_id, str) and field_id:
            if field_id not in by_id:
                print(f"warning: configured field_id for {logical_name} was not returned by schema", file=sys.stderr)
            resolved[logical_name] = field_id
            continue

        if not isinstance(field_name, str) or not field_name:
            if spec.get("required", False):
                raise SyncError(f"sync.field_mapping.{logical_name} is required but has no field_name/field_id")
            continue

        field = by_name.get(field_name)
        if not field:
            if spec.get("required", False):
                raise SyncError(f"required field not found in remote schema: {field_name}")
            print(f"warning: optional field not found in remote schema: {field_name}", file=sys.stderr)
            continue
        resolved_id = field.get("field_id")
        if not isinstance(resolved_id, str) or not resolved_id:
            raise SyncError(f"remote field has no field_id: {field_name}")
        resolved[logical_name] = resolved_id

    if config.unique_key not in resolved:
        raise SyncError(f"sync.unique_key is not mapped to a field ID: {config.unique_key}")
    return resolved


def convert_local_records(records: list[JsonObject], field_ids: dict[str, str]) -> list[JsonObject]:
    converted: list[JsonObject] = []
    for index, record in enumerate(records):
        source_fields = expect_object(record.get("fields"), f"records[{index}].fields")
        output_fields: JsonObject = {}
        unknown = sorted(set(source_fields) - set(field_ids))
        if unknown:
            raise SyncError(f"records[{index}] contains unmapped fields: {', '.join(unknown)}")
        for logical_name, value in source_fields.items():
            output_fields[field_ids[logical_name]] = value
        converted.append({"fields": output_fields, "source_index": index})
    return converted


def build_plan(
    config: SyncConfig,
    local_records: list[JsonObject],
    remote_records: list[JsonObject],
    field_ids: dict[str, str],
) -> JsonObject:
    unique_field_id = field_ids[config.unique_key]
    compare_field_ids = [field_ids[name] for name in config.compare_fields if name in field_ids]

    remote_by_key: dict[str, JsonObject] = {}
    duplicates: dict[str, int] = {}
    for remote in remote_records:
        fields = expect_object(remote.get("fields", {}), "remote.fields")
        key = normalize_key(fields.get(unique_field_id))
        if not key:
            continue
        if key in remote_by_key:
            duplicates[key] = duplicates.get(key, 1) + 1
            continue
        remote_by_key[key] = remote

    creates: list[JsonObject] = []
    updates: list[JsonObject] = []
    unchanged = 0
    for local in local_records:
        local_fields = expect_object(local.get("fields"), "local.fields")
        key = normalize_key(local_fields.get(unique_field_id))
        if not key:
            raise SyncError(f"local record source_index={local.get('source_index')} has empty unique key")
        remote = remote_by_key.get(key)
        if not remote:
            creates.append({"fields": strip_internal_fields(local_fields)})
            continue

        remote_fields = expect_object(remote.get("fields", {}), "remote.fields")
        changed_fields: JsonObject = {}
        for field_id in compare_field_ids:
            if not cells_equal(local_fields.get(field_id), remote_fields.get(field_id)):
                changed_fields[field_id] = local_fields.get(field_id)
        if changed_fields:
            updates.append({"record_id": remote.get("record_id"), "fields": changed_fields})
        else:
            unchanged += 1

    return {
        "create_count": len(creates),
        "update_count": len(updates),
        "unchanged_count": unchanged,
        "duplicate_remote_keys": duplicates,
        "creates": creates,
        "updates": updates,
    }


def strip_internal_fields(fields: JsonObject) -> JsonObject:
    return {key: value for key, value in fields.items() if not key.startswith("_")}


def normalize_key(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    if isinstance(value, dict):
        for key in ("text", "value", "name"):
            if key in value:
                return str(value[key]).strip()
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return str(value).strip()


def cells_equal(left: Any, right: Any) -> bool:
    return canonical_cell(left) == canonical_cell(right)


def canonical_cell(value: Any) -> Any:
    if isinstance(value, list):
        return [canonical_cell(item) for item in value]
    if isinstance(value, dict):
        return {key: canonical_cell(value[key]) for key in sorted(value)}
    return value


def chunks(values: list[JsonObject], size: int) -> list[list[JsonObject]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def print_plan(plan: JsonObject, *, include_payloads: bool) -> None:
    summary = {
        "create_count": plan["create_count"],
        "update_count": plan["update_count"],
        "unchanged_count": plan["unchanged_count"],
        "duplicate_remote_keys": plan["duplicate_remote_keys"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if include_payloads:
        print(json.dumps({"creates": plan["creates"], "updates": plan["updates"]}, ensure_ascii=False, indent=2))


def offline_plan(config: SyncConfig, records: list[JsonObject]) -> None:
    configured_fields = sorted(config.field_mapping)
    data_fields = sorted({field for record in records for field in record["fields"]})
    missing_mapping = sorted(set(data_fields) - set(configured_fields))
    missing_unique = config.unique_key not in data_fields
    payload = {
        "mode": "offline-plan",
        "record_count": len(records),
        "configured_fields": configured_fields,
        "data_fields": data_fields,
        "unmapped_data_fields": missing_mapping,
        "unique_key": config.unique_key,
        "unique_key_present": not missing_unique,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    if missing_mapping:
        raise SyncError("data contains fields missing from sync.field_mapping")
    if missing_unique:
        raise SyncError("data does not contain sync.unique_key")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run or apply a Bitable OpenAPI record sync.")
    parser.add_argument("--config", required=True, help="Path to config JSON.")
    parser.add_argument("--data", required=True, help="Path to records JSON.")
    parser.add_argument("--apply", action="store_true", help="Write creates/updates to Bitable.")
    parser.add_argument("--offline-plan", action="store_true", help="Validate local files without network calls.")
    parser.add_argument("--show-payloads", action="store_true", help="Print create/update payloads in dry-run output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config)
        records = load_records(args.data)

        if args.offline_plan:
            offline_plan(config, records)
            return 0

        client = FeishuClient(config)
        remote_fields = client.list_fields()
        field_ids = resolve_field_ids(config, remote_fields)
        local_records = convert_local_records(records, field_ids)
        remote_records = client.list_records()
        plan = build_plan(config, local_records, remote_records, field_ids)

        print_plan(plan, include_payloads=args.show_payloads or not args.apply)
        if plan["duplicate_remote_keys"]:
            raise SyncError("remote table contains duplicate unique keys; fix before writing")

        if not args.apply:
            print("dry-run only; add --apply to write changes")
            return 0

        if plan["creates"]:
            client.batch_create(plan["creates"])
        if plan["updates"]:
            client.batch_update(plan["updates"])

        print("apply complete; re-run without --apply to verify the table is unchanged")
        return 0
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
