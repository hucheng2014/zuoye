#!/usr/bin/env python3
"""Read or set Trae CN chat model state in VS Code-style storage."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import sys
import time
from urllib.parse import unquote, urlparse


MODEL_IDS = {
    "doubao": "1_-_Doubao-Seed-2.0-Code",
    "doubao-seed-2.0-code": "1_-_Doubao-Seed-2.0-Code",
    "gpt5": "1_-_gpt-5.4",
    "gpt-5.4": "1_-_gpt-5.4",
    "gemini": "1_-_gemini-3.1-p",
    "gemini-3.1-pro": "1_-_gemini-3.1-p",
    "gemini-3.1-p": "1_-_gemini-3.1-p",
    "deepseek": "1_-_DeepSeek-V4-Pro",
    "deepseek-v4": "1_-_DeepSeek-V4-Pro",
    "deepseek-v4-pro": "1_-_DeepSeek-V4-Pro",
    "minmax": "1_-_minimax-m2.7",
    "minmax-m2.7": "1_-_minimax-m2.7",
    "minimax": "1_-_minimax-m2.7",
    "minimax-m2.7": "1_-_minimax-m2.7",
    "glm": "1_-_glm-5.1",
    "glm-5.1": "1_-_glm-5.1",
    "qwen": "1_-_qwen-3.6-plus",
    "qwen3.6-plus": "1_-_qwen-3.6-plus",
    "qwen-3.6-plus": "1_-_qwen-3.6-plus",
}


def default_user_data_dir() -> Path:
    return Path(os.environ.get("TRAE_USER_DATA_DIR", "~/.config/Trae CN")).expanduser()


def to_uri(workspace: str) -> str:
    if "://" in workspace:
        return workspace
    return Path(workspace).expanduser().resolve().as_uri()


def uri_to_path(uri: str) -> Path | None:
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        return None
    return Path(unquote(parsed.path)).resolve()


def normalize_model(model: str) -> str:
    raw = model.strip()
    if raw in MODEL_IDS.values():
        return raw
    key = raw.lower().replace(" ", "-").replace("_", "-")
    if key in MODEL_IDS:
        return MODEL_IDS[key]
    raise SystemExit(
        "Unknown model. Use one of: "
        + ", ".join(sorted(MODEL_IDS))
        + " or pass the exact Trae model id."
    )


def workspace_dbs(user_data_dir: Path) -> list[tuple[Path, str]]:
    result: list[tuple[Path, str]] = []
    for workspace_json in sorted((user_data_dir / "User" / "workspaceStorage").glob("*/workspace.json")):
        try:
            data = json.loads(workspace_json.read_text())
        except Exception:
            continue
        folder = data.get("folder")
        db_path = workspace_json.parent / "state.vscdb"
        if folder and db_path.exists():
            result.append((db_path, folder))
    return result


def select_workspace_dbs(user_data_dir: Path, workspace: str | None, all_workspaces: bool) -> list[tuple[Path, str]]:
    all_dbs = workspace_dbs(user_data_dir)
    if all_workspaces:
        return all_dbs
    if not workspace:
        raise SystemExit("Pass --workspace or --all-workspaces.")

    wanted_uri = to_uri(workspace)
    wanted_path = uri_to_path(wanted_uri)
    matches: list[tuple[Path, str]] = []
    for db_path, folder_uri in all_dbs:
        folder_path = uri_to_path(folder_uri)
        if folder_uri == wanted_uri or (wanted_path and folder_path and folder_path == wanted_path):
            matches.append((db_path, folder_uri))

    if not matches:
        known = "\n  ".join(folder for _, folder in all_dbs) or "(none)"
        raise SystemExit(f"No Trae workspace state matched {wanted_uri}. Known workspaces:\n  {known}")
    return matches


def open_db(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path), timeout=10)
    con.execute("pragma busy_timeout=10000")
    return con


def item_keys(con: sqlite3.Connection) -> list[str]:
    return [row[0] for row in con.execute("select key from ItemTable")]


def find_user_id(db_paths: list[Path], user_id: str | None) -> str:
    if user_id:
        return user_id
    patterns = [
        re.compile(r"^(\d+)_ai-chat:sessionRelation:globalModelMap$"),
        re.compile(r"^(\d+)_AI\.agent\.model\.model_list_map$"),
    ]
    for db_path in db_paths:
        try:
            with open_db(db_path) as con:
                for key in item_keys(con):
                    for pattern in patterns:
                        match = pattern.match(key)
                        if match:
                            return match.group(1)
        except sqlite3.Error:
            continue
    raise SystemExit("Could not detect Trae user id. Pass --user-id.")


def global_db(user_data_dir: Path) -> Path:
    return user_data_dir / "User" / "globalStorage" / "state.vscdb"


def read_model(db_path: Path, user_id: str) -> str | None:
    key = f"{user_id}_ai-chat:sessionRelation:globalModelMap"
    try:
        with open_db(db_path) as con:
            row = con.execute("select value from ItemTable where key = ?", (key,)).fetchone()
    except sqlite3.Error:
        return None
    if not row:
        return None
    try:
        return json.loads(row[0]).get("dev_builder")
    except Exception:
        return str(row[0])


def decode_item_value(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return str(value)


def read_json_item(con: sqlite3.Connection, key: str, default: object) -> object:
    row = con.execute("select value from ItemTable where key = ?", (key,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(decode_item_value(row[0]))
    except Exception:
        return default


def write_json_item(con: sqlite3.Connection, key: str, value: object) -> None:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    con.execute(
        "insert into ItemTable(key, value) values(?, ?) "
        "on conflict(key) do update set value = excluded.value",
        (key, text),
    )


def write_model(db_path: Path, user_id: str, model_id: str) -> None:
    model_key = f"{user_id}_ai-chat:sessionRelation:globalModelMap"
    mode_key = f"{user_id}_ai-chat:sessionRelation:globalModeMap"
    with open_db(db_path) as con:
        write_json_item(con, model_key, {"dev_builder": model_id})
        write_json_item(con, mode_key, {"dev_builder": 0})
        con.commit()


def force_manual_mode(db_path: Path, user_id: str) -> int:
    mode_map_key = f"{user_id}_ai-chat:sessionRelation:modeMap"
    global_mode_key = f"{user_id}_ai-chat:sessionRelation:globalModeMap"
    memento_key = "memento/icube-ai-agent-storage"

    with open_db(db_path) as con:
        mode_map = read_json_item(con, mode_map_key, {})
        if not isinstance(mode_map, dict):
            mode_map = {}

        session_ids = set(mode_map)
        memento = read_json_item(con, memento_key, {})
        if isinstance(memento, dict):
            current = memento.get("currentSessionId")
            if isinstance(current, str) and re.fullmatch(r"[0-9a-f]{24}", current):
                session_ids.add(current)
            sessions = memento.get("list")
            if isinstance(sessions, list):
                for item in sessions:
                    if isinstance(item, dict) and isinstance(item.get("sessionId"), str):
                        session_ids.add(item["sessionId"])

        for sid in session_ids:
            if re.fullmatch(r"[0-9a-f]{24}", sid):
                mode_map[sid] = {"dev_builder": 0}

        write_json_item(con, mode_map_key, mode_map)
        write_json_item(con, global_mode_key, {"dev_builder": 0})
        con.commit()

    return len(session_ids)


def current_session_id(db_path: Path) -> str | None:
    with open_db(db_path) as con:
        memento = read_json_item(con, "memento/icube-ai-agent-storage", {})
    if not isinstance(memento, dict):
        return None
    current = memento.get("currentSessionId")
    if isinstance(current, str) and re.fullmatch(r"[0-9a-f]{24}", current):
        return current
    sessions = memento.get("list")
    if isinstance(sessions, list):
        for item in sessions:
            if isinstance(item, dict) and item.get("isCurrent") and isinstance(item.get("sessionId"), str):
                return item["sessionId"]
    return None


def generate_session_id(existing: set[str]) -> str:
    for _ in range(100):
        sid = f"{int(time.time()):08x}{secrets.token_hex(8)}"
        if sid not in existing:
            return sid
    raise SystemExit("Could not generate a unique session id.")


def create_new_session(
    db_path: Path,
    user_id: str,
    model_id: str,
    session_id: str | None,
    agent: str,
    max_sessions: int,
) -> str:
    model_map_key = f"{user_id}_ai-chat:sessionRelation:modelMap"
    mode_map_key = f"{user_id}_ai-chat:sessionRelation:modeMap"
    global_model_key = f"{user_id}_ai-chat:sessionRelation:globalModelMap"
    global_mode_key = f"{user_id}_ai-chat:sessionRelation:globalModeMap"
    memento_key = "memento/icube-ai-agent-storage"
    agent_map_key = "icube_session_agent_map"

    with open_db(db_path) as con:
        memento = read_json_item(con, memento_key, {})
        if not isinstance(memento, dict):
            memento = {}
        sessions = memento.get("list")
        if not isinstance(sessions, list):
            sessions = []

        existing = {
            item.get("sessionId")
            for item in sessions
            if isinstance(item, dict) and isinstance(item.get("sessionId"), str)
        }
        agent_map = read_json_item(con, agent_map_key, {})
        if isinstance(agent_map, dict):
            existing.update(k for k in agent_map if isinstance(k, str))
        model_map = read_json_item(con, model_map_key, {})
        if isinstance(model_map, dict):
            existing.update(k for k in model_map if isinstance(k, str))
        else:
            model_map = {}
        mode_map = read_json_item(con, mode_map_key, {})
        if not isinstance(mode_map, dict):
            mode_map = {}

        sid = session_id or generate_session_id(existing)
        if not re.fullmatch(r"[0-9a-f]{24}", sid):
            raise SystemExit("--session-id must be 24 lowercase hex characters.")
        if sid in existing:
            raise SystemExit(f"Session id already exists: {sid}")

        new_sessions = []
        for item in sessions:
            if not isinstance(item, dict):
                continue
            if item.get("sessionId") == sid:
                continue
            if item.get("isCurrent"):
                item = dict(item)
                item["isCurrent"] = False
            new_sessions.append(item)

        new_sessions.insert(0, {"isCurrent": True, "sessionId": sid, "messages": []})
        if max_sessions > 0:
            new_sessions = new_sessions[:max_sessions]
        memento["list"] = new_sessions
        memento["currentSessionId"] = sid

        if not isinstance(agent_map, dict):
            agent_map = {}
        agent_map[sid] = agent

        model_map[sid] = {"dev_builder": model_id}
        mode_map[sid] = {"dev_builder": 0}

        write_json_item(con, memento_key, memento)
        write_json_item(con, agent_map_key, agent_map)
        write_json_item(con, model_map_key, model_map)
        write_json_item(con, mode_map_key, mode_map)
        write_json_item(con, global_model_key, {"dev_builder": model_id})
        write_json_item(con, global_mode_key, {"dev_builder": 0})
        con.commit()

    return sid


def cmd_list(args: argparse.Namespace) -> int:
    user_data_dir = Path(args.user_data_dir).expanduser()
    dbs = workspace_dbs(user_data_dir)
    all_state_dbs = [global_db(user_data_dir)] + [db for db, _ in dbs]
    user_id = find_user_id([db for db in all_state_dbs if db.exists()], args.user_id)
    gdb = global_db(user_data_dir)
    if gdb.exists():
        print(f"global\t{read_model(gdb, user_id) or '-'}\t{gdb}")
    for db_path, folder in dbs:
        print(f"{folder}\t{read_model(db_path, user_id) or '-'}\t{db_path}")
    return 0


def cmd_current_session(args: argparse.Namespace) -> int:
    user_data_dir = Path(args.user_data_dir).expanduser()
    targets = select_workspace_dbs(user_data_dir, args.workspace, False)
    sid = current_session_id(targets[0][0])
    if not sid:
        print("NOT_FOUND")
        return 1
    print(sid)
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    user_data_dir = Path(args.user_data_dir).expanduser()
    model_id = normalize_model(args.model)
    targets = select_workspace_dbs(user_data_dir, args.workspace, args.all_workspaces)
    target_dbs = [db for db, _ in targets]
    gdb = global_db(user_data_dir)
    if gdb.exists():
        target_dbs.insert(0, gdb)
    user_id = find_user_id(target_dbs, args.user_id)

    seen: set[Path] = set()
    for db_path in target_dbs:
        if db_path in seen:
            continue
        seen.add(db_path)
        write_model(db_path, user_id, model_id)

    print(f"set {model_id}")
    for db_path, folder in targets:
        print(f"{folder}\t{read_model(db_path, user_id)}\t{db_path}")
    if gdb.exists():
        print(f"global\t{read_model(gdb, user_id)}\t{gdb}")
    return 0


def cmd_new_session(args: argparse.Namespace) -> int:
    user_data_dir = Path(args.user_data_dir).expanduser()
    model_id = normalize_model(args.model)
    targets = select_workspace_dbs(user_data_dir, args.workspace, False)
    target_dbs = [db for db, _ in targets]
    gdb = global_db(user_data_dir)
    user_id = find_user_id(target_dbs + ([gdb] if gdb.exists() else []), args.user_id)

    sid = args.session_id
    for db_path, _ in targets:
        sid = create_new_session(
            db_path=db_path,
            user_id=user_id,
            model_id=model_id,
            session_id=sid,
            agent=args.agent,
            max_sessions=args.max_sessions,
        )

    if gdb.exists():
        write_model(gdb, user_id, model_id)

    print(sid)
    return 0


def cmd_manual_mode(args: argparse.Namespace) -> int:
    user_data_dir = Path(args.user_data_dir).expanduser()
    targets = select_workspace_dbs(user_data_dir, args.workspace, args.all_workspaces)
    target_dbs = [db for db, _ in targets]
    gdb = global_db(user_data_dir)
    if gdb.exists():
        target_dbs.insert(0, gdb)
    user_id = find_user_id(target_dbs, args.user_id)

    seen: set[Path] = set()
    for db_path in target_dbs:
        if db_path in seen:
            continue
        seen.add(db_path)
        count = force_manual_mode(db_path, user_id)
        print(f"manual-mode\t{count}\t{db_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-data-dir", default=str(default_user_data_dir()))
    parser.add_argument("--user-id", default=os.environ.get("TRAE_USER_ID"))
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="List current Trae model state.")
    list_parser.set_defaults(func=cmd_list)

    current_parser = sub.add_parser("current-session", help="Print the current chat session id for a workspace.")
    current_parser.add_argument("--workspace", required=True, help="Workspace path or URI to inspect.")
    current_parser.set_defaults(func=cmd_current_session)

    set_parser = sub.add_parser("set", help="Set Trae model state.")
    set_parser.add_argument("model", help="Model alias or exact Trae model id.")
    group = set_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--workspace", help="Workspace path or URI to update.")
    group.add_argument("--all-workspaces", action="store_true", help="Update every known workspace state.")
    set_parser.set_defaults(func=cmd_set)

    new_parser = sub.add_parser("new-session", help="Create and select a new chat session for a workspace.")
    new_parser.add_argument("model", help="Model alias or exact Trae model id.")
    new_parser.add_argument("--workspace", required=True, help="Workspace path or URI to update.")
    new_parser.add_argument("--agent", default="dev_agent", help="Agent id to bind to the session.")
    new_parser.add_argument("--session-id", help="Optional explicit 24-hex session id.")
    new_parser.add_argument("--max-sessions", type=int, default=30, help="Maximum sessions kept in the visible session list.")
    new_parser.set_defaults(func=cmd_new_session)

    manual_parser = sub.add_parser("manual-mode", help="Force Trae chat mode state to manual.")
    group = manual_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--workspace", help="Workspace path or URI to update.")
    group.add_argument("--all-workspaces", action="store_true", help="Update every known workspace state.")
    manual_parser.set_defaults(func=cmd_manual_mode)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
