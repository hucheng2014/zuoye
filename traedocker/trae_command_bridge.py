#!/usr/bin/env python3
"""Invoke Trae workbench chat commands through a local URI-handler extension."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from urllib.parse import quote
import uuid


BASE_DIR = Path(__file__).resolve().parent
EXTENSION_ID = "local.trae-trial-bridge"
EXTENSION_VERSION = "0.0.3"
EXTENSION_SOURCE = BASE_DIR / "trae-trial-bridge"
USER_DATA_DIR = Path(os.environ.get("TRAE_USER_DATA_DIR", "~/.config/Trae CN")).expanduser()
EXTENSIONS_DIR = Path(os.environ.get("TRAE_EXTENSIONS_DIR", "~/.trae-cn/extensions")).expanduser()
INSTALLED_EXTENSION_DIR = EXTENSIONS_DIR / f"{EXTENSION_ID}-{EXTENSION_VERSION}-universal"
TRAE_CLI = os.environ.get("TRAE_CLI_BIN", "/usr/share/trae-cn/bin/trae-cn")

MODEL_NAMES = {
    "doubao": "Doubao-Seed-2.0-Code",
    "doubao-seed-2.0-code": "Doubao-Seed-2.0-Code",
    "gpt5": "gpt-5.4",
    "gpt-5.4": "gpt-5.4",
    "gemini": "gemini-3.1-p",
    "gemini-3.1-pro": "gemini-3.1-p",
    "gemini-3.1-p": "gemini-3.1-p",
    "deepseek": "DeepSeek-V4-Pro",
    "deepseek-v4": "DeepSeek-V4-Pro",
    "deepseek-v4-pro": "DeepSeek-V4-Pro",
    "minmax": "minimax-m2.7",
    "minmax-m2.7": "minimax-m2.7",
    "minimax": "minimax-m2.7",
    "minimax-m2.7": "minimax-m2.7",
    "glm": "glm-5.1",
    "glm-5.1": "glm-5.1",
    "qwen": "qwen-3.6-plus",
    "qwen3.6-plus": "qwen-3.6-plus",
    "qwen-3.6-plus": "qwen-3.6-plus",
}


def normalize_model_name(model: str) -> str:
    raw = model.strip()
    if raw in MODEL_NAMES.values():
        return raw
    key = raw.lower().replace(" ", "-").replace("_", "-")
    if key in MODEL_NAMES:
        return MODEL_NAMES[key]
    raise SystemExit(f"Unknown model for bridge command: {model}")


def load_settings() -> dict:
    settings_path = USER_DATA_DIR / "User" / "settings.json"
    if not settings_path.exists():
        return {}
    try:
        return json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Could not read Trae settings: {settings_path}: {exc}") from exc


def save_settings(settings: dict) -> None:
    settings_path = USER_DATA_DIR / "User" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")


def trust_extension_uri_handler() -> None:
    settings = load_settings()
    key = "extensions.confirmedUriHandlerExtensionIds"
    values = settings.get(key)
    if not isinstance(values, list):
        values = []
    lowered = {str(item).lower() for item in values}
    if EXTENSION_ID.lower() not in lowered:
        values.append(EXTENSION_ID)
        settings[key] = values
        save_settings(settings)


def update_extensions_json() -> None:
    EXTENSIONS_DIR.mkdir(parents=True, exist_ok=True)
    metadata_path = EXTENSIONS_DIR / "extensions.json"
    try:
        entries = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else []
    except Exception:
        entries = []
    if not isinstance(entries, list):
        entries = []

    entries = [
        entry
        for entry in entries
        if str(entry.get("identifier", {}).get("id", "")).lower() != EXTENSION_ID.lower()
    ]
    entries.append(
        {
            "identifier": {"id": EXTENSION_ID},
            "version": EXTENSION_VERSION,
            "location": {
                "$mid": 1,
                "path": str(INSTALLED_EXTENSION_DIR),
                "scheme": "file",
            },
            "relativeLocation": INSTALLED_EXTENSION_DIR.name,
            "metadata": {
                "installedTimestamp": int(time.time() * 1000),
                "pinned": True,
                "source": "vsix",
                "targetPlatform": "universal",
            },
        }
    )
    metadata_path.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")


def install_extension() -> None:
    if not EXTENSION_SOURCE.exists():
        raise SystemExit(f"Bridge extension source is missing: {EXTENSION_SOURCE}")
    if INSTALLED_EXTENSION_DIR.exists():
        shutil.rmtree(INSTALLED_EXTENSION_DIR)
    shutil.copytree(EXTENSION_SOURCE, INSTALLED_EXTENSION_DIR)
    update_extensions_json()
    trust_extension_uri_handler()
    print(f"installed {EXTENSION_ID} at {INSTALLED_EXTENSION_DIR}", file=sys.stderr)


def result_from_file(result_file: Path, request_id: str) -> dict:
    try:
        data = json.loads(result_file.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Could not read bridge result file: {result_file}: {exc}") from exc
    if data.get("requestId") != request_id:
        raise RuntimeError(f"Bridge result requestId mismatch: {data.get('requestId')} != {request_id}")
    return data


def invoke(payload: dict, timeout: int, trae_bin: str) -> dict:
    request_id = payload.setdefault("requestId", uuid.uuid4().hex)
    with tempfile.TemporaryDirectory(prefix="trae-trial-bridge-") as tmp:
        tmp_path = Path(tmp)
        payload_file = tmp_path / "payload.json"
        result_file = tmp_path / "result.json"
        payload["resultFile"] = str(result_file)
        payload_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        url = f"trae-cn://{EXTENSION_ID}/{payload['action']}?payloadFile={quote(str(payload_file), safe='')}"
        cmd = [trae_bin, "--reuse-window", "--open-url", url]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

        deadline = time.time() + timeout
        while time.time() < deadline:
            if result_file.exists():
                return result_from_file(result_file, request_id)
            time.sleep(0.25)
    raise TimeoutError(
        f"Timed out waiting for Trae bridge result. If this is the first install, reload Trae once. extension={EXTENSION_ID}"
    )


def ensure_installed() -> None:
    if not INSTALLED_EXTENSION_DIR.exists():
        install_extension()
    else:
        trust_extension_uri_handler()


def cmd_install(args: argparse.Namespace) -> int:
    install_extension()
    return 0


def cmd_ping(args: argparse.Namespace) -> int:
    if not args.no_install:
        ensure_installed()
    data = invoke({"action": "ping"}, args.timeout, args.trae_bin)
    print(json.dumps(data, ensure_ascii=False))
    return 0 if data.get("ok") else 1


def cmd_current_session(args: argparse.Namespace) -> int:
    if not args.no_install:
        ensure_installed()
    data = invoke({"action": "currentSession"}, args.timeout, args.trae_bin)
    if not data.get("ok"):
        print(data.get("error") or "bridge currentSession failed", file=sys.stderr)
        return 1
    print(data.get("sessionId") or "NOT_FOUND")
    return 0


def cmd_send(args: argparse.Namespace) -> int:
    if not args.no_install:
        ensure_installed()
    prompt = sys.stdin.read() if args.prompt == "-" else args.prompt
    model_name = normalize_model_name(args.model)
    options = {
        "newSession": args.new_session,
        "modelName": model_name,
    }
    if args.agent_name:
        options["agentName"] = args.agent_name
    if args.workspace:
        options["workspaceFolder"] = args.workspace
    payload = {
        "action": "sendInternal" if args.internal else "send",
        "inputs": [prompt],
        "options": options,
    }
    data = invoke(payload, args.timeout, args.trae_bin)
    if not data.get("ok"):
        print(data.get("error") or "bridge send failed", file=sys.stderr)
        return 1
    sid = data.get("sessionId") or data.get("result", {}).get("sessionId")
    if not sid:
        print(json.dumps(data, ensure_ascii=False), file=sys.stderr)
        return 1
    print(sid)
    return 0


def cmd_execute_command(args: argparse.Namespace) -> int:
    if not args.no_install:
        ensure_installed()
    try:
        arguments = json.loads(args.arguments)
    except Exception as exc:
        raise SystemExit(f"--arguments must be JSON: {exc}") from exc
    if not isinstance(arguments, list):
        raise SystemExit("--arguments must be a JSON list.")
    payload = {
        "action": "executeCommand",
        "command": args.command_id,
        "arguments": arguments,
        "attempts": args.attempts,
    }
    data = invoke(payload, args.timeout, args.trae_bin)
    print(json.dumps(data, ensure_ascii=False))
    return 0 if data.get("ok") else 1


def cmd_list_commands(args: argparse.Namespace) -> int:
    if not args.no_install:
        ensure_installed()
    payload = {
        "action": "listCommands",
        "includeInternal": args.include_internal,
        "pattern": args.pattern,
    }
    data = invoke(payload, args.timeout, args.trae_bin)
    print(json.dumps(data, ensure_ascii=False))
    return 0 if data.get("ok") else 1


def cmd_list_language_models(args: argparse.Namespace) -> int:
    if not args.no_install:
        ensure_installed()
    payload = {"action": "listLanguageModels"}
    data = invoke(payload, args.timeout, args.trae_bin)
    print(json.dumps(data, ensure_ascii=False))
    return 0 if data.get("ok") else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trae-bin", default=TRAE_CLI)
    sub = parser.add_subparsers(dest="command", required=True)

    install_parser = sub.add_parser("install", help="Install and trust the local bridge extension.")
    install_parser.set_defaults(func=cmd_install)

    ping_parser = sub.add_parser("ping", help="Ping the bridge URI handler.")
    ping_parser.add_argument("--timeout", type=int, default=20)
    ping_parser.add_argument("--no-install", action="store_true")
    ping_parser.set_defaults(func=cmd_ping)

    current_parser = sub.add_parser("current-session", help="Read Trae's in-memory current chat session id.")
    current_parser.add_argument("--timeout", type=int, default=20)
    current_parser.add_argument("--no-install", action="store_true")
    current_parser.set_defaults(func=cmd_current_session)

    send_parser = sub.add_parser("send", help="Send a prompt through Trae internal workbench command.")
    send_parser.add_argument("--model", required=True, help="Model alias or Trae UI model name.")
    send_parser.add_argument("--prompt", default="-", help="Prompt text, or '-' for stdin.")
    send_parser.add_argument("--workspace", default="")
    send_parser.add_argument("--agent-name", default="")
    send_parser.add_argument("--new-session", action="store_true")
    send_parser.add_argument("--internal", action="store_true", help="Use Trae's blocking internal send command.")
    send_parser.add_argument("--timeout", type=int, default=30)
    send_parser.add_argument("--no-install", action="store_true")
    send_parser.set_defaults(func=cmd_send)

    command_parser = sub.add_parser("execute-command", help="Execute a Trae/VS Code command through the bridge.")
    command_parser.add_argument("command_id")
    command_parser.add_argument("--arguments", default="[]", help="JSON list of command arguments.")
    command_parser.add_argument("--attempts", type=int, default=6)
    command_parser.add_argument("--timeout", type=int, default=20)
    command_parser.add_argument("--no-install", action="store_true")
    command_parser.set_defaults(func=cmd_execute_command)

    list_commands_parser = sub.add_parser("list-commands", help="List registered Trae/VS Code commands.")
    list_commands_parser.add_argument("--pattern", default="", help="Optional regex filter.")
    list_commands_parser.add_argument("--include-internal", action="store_true")
    list_commands_parser.add_argument("--timeout", type=int, default=20)
    list_commands_parser.add_argument("--no-install", action="store_true")
    list_commands_parser.set_defaults(func=cmd_list_commands)

    list_lm_parser = sub.add_parser("list-language-models", help="List registered VS Code language models.")
    list_lm_parser.add_argument("--timeout", type=int, default=20)
    list_lm_parser.add_argument("--no-install", action="store_true")
    list_lm_parser.set_defaults(func=cmd_list_language_models)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
