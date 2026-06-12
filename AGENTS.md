# Platform: macOS

This workspace has been migrated from Ubuntu Linux (192.168.50.97) to macOS. Key differences:

- **Home directory**: `/Users/xaa` replaces `/home/jianglei`
- **Project root**: `/Users/xaa/zuoye`
- **Docker**: Use Docker Desktop for Mac
- **Shell**: zsh is the default (bash scripts still work via `#!/usr/bin/env bash`)
- **Package managers**: Use `brew` instead of `apt`

## Key platform notes

- **FireRedASR**: Runs in **CPU mode** (`firered-use-gpu=0`), not triton_tensorrt. The triton_tensorrt deployment in `putonghuaasr/third_party/FireRedASR/runtime/triton_tensorrt/` is NOT used — it requires nvidia GPU. The actual ASR uses `local_segment_dual_asr.py` with Qwen3-ASR + FireRedASR-AED on CPU.
- **mihomo (代理)**: Runs on **192.168.5.64** (Ubuntu, `wlp2s0`, `stack: mixed`), NOT on this machine. The `mihomo-full.yaml` in this repo is a copy of that remote config. Do not change it for local macOS use.
- **Scripts referencing systemctl, /dev/nvme\***: These are Linux-only and won't work on macOS.

# Workspace Browser Automation Rules

This workspace uses two browser-control layers:

- Production automation stays in code: Playwright/CDP scripts, task-specific validators, model calls, submit guards, logs, and retry logic.
- `agent-browser` is available as an interactive inspection tool for AI agents: snapshots, screenshots, quick clicks, selector discovery, text extraction, and debugging.

## Required Split

- Use existing production scripts for any repeatable task workflow or anything that can submit, advance, delete, upload, or mutate business data.
- Use `agent-browser` for temporary observation and debugging before writing new throwaway Playwright scripts.
- Do not replace safe submit scripts with ad hoc `agent-browser click` commands.
- Do not run `agent-browser close --all` against user-prepared work browsers.
- If a page requires login, captcha, payment, or account recovery, stop and ask the user to handle it through noVNC.

## Unified agent-browser Entry

Use the root helper so browser IDs, sessions, and CDP ports stay consistent:

```bash
/Users/xaa/zuoye/tools/agent-browser.sh list
/Users/xaa/zuoye/tools/agent-browser.sh asr snapshot -i
/Users/xaa/zuoye/tools/agent-browser.sh alibaba screenshot /tmp/alibaba.png
/Users/xaa/zuoye/tools/agent-browser.sh work-a get url
```

Common targets:

- `asr` / `putonghuaasr`: ASR browser, CDP proxy `127.0.0.1:9221`, noVNC `127.0.0.1:6080`.
- `oneform`: Oneform monitor browser, CDP proxy `127.0.0.1:9225`, noVNC `127.0.0.1:6081`.
- `work-a` / `controlled`: primary work browser, CDP proxy `127.0.0.1:9233`, noVNC `127.0.0.1:6082`.
- `work-b` / `trae` / `traedocker`: secondary work browser, CDP proxy `127.0.0.1:9235`, noVNC `127.0.0.1:6083`.
- `alibaba` / `alibabaxiangmu`: Alibaba task browser, CDP proxy `127.0.0.1:9237`, noVNC `127.0.0.1:6084`.
- `duomotai`: Duomotai browser, CDP proxy `127.0.0.1:9239`, noVNC `127.0.0.1:6085`.

## Safe Workflow Pattern

1. Inspect with `agent-browser`:

```bash
/Users/xaa/zuoye/tools/agent-browser.sh <target> snapshot -i
/Users/xaa/zuoye/tools/agent-browser.sh <target> screenshot /tmp/current.png
```

2. Implement durable logic in a project script when the action must be repeated.

3. Submit only through the project-specific safe script or a code path with equivalent verification.

See `/Users/xaa/zuoye/docs/agent-browser-integration.md` for details.
