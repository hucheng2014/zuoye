#!/usr/bin/env python3
"""Minimal CDP Runtime.evaluate helper for an open Bitable page."""

from __future__ import annotations

import json
import sys
import urllib.request
from typing import Any

import websocket

import submit_new_task_group as group

CDP_HTTP = "http://127.0.0.1:9235"


def bitable_page_ws() -> str:
    data = json.loads(urllib.request.urlopen(f"{CDP_HTTP}/json/list", timeout=5).read())
    for page in data:
        if group.BASE_TOKEN in page.get("url", ""):
            return page["webSocketDebuggerUrl"]
    raise RuntimeError("Bitable page is not open in traedocker browser")


def cdp_eval(ws_url: str, expression: str, await_promise: bool = True) -> Any:
    ws = websocket.create_connection(ws_url, timeout=30)
    msg_id = 0

    def send(method: str, params: dict | None = None) -> dict:
        nonlocal msg_id
        msg_id += 1
        ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        while True:
            payload = json.loads(ws.recv())
            if payload.get("id") == msg_id:
                if "error" in payload:
                    raise RuntimeError(json.dumps(payload["error"], ensure_ascii=False))
                return payload.get("result", {})

    send("Runtime.enable")
    result = send(
        "Runtime.evaluate",
        {
            "expression": expression,
            "awaitPromise": await_promise,
            "returnByValue": True,
        },
    )
    ws.close()
    if result.get("exceptionDetails"):
        raise RuntimeError(json.dumps(result["exceptionDetails"], ensure_ascii=False))
    return result.get("result", {}).get("value")


def set_records(updates: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ws_url = bitable_page_ws()
    expr = f"""
    (async () => {{
      const updates = {json.dumps(updates, ensure_ascii=False)};
      const result = await Promise.resolve(window.bitableStore.commandManager.execute({{
        cmd: 'SetRecords',
        tableId: {json.dumps(group.TABLE_ID)},
        viewId: {json.dumps(group.VIEW_ID)},
        data: updates,
        ignoreCheckRecordLoaded: true,
      }}));
      return JSON.parse(JSON.stringify(result));
    }})()
    """
    return cdp_eval(ws_url, expr)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: cdp_eval.py <expression>", file=sys.stderr)
        return 2
    value = cdp_eval(bitable_page_ws(), sys.argv[1])
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
