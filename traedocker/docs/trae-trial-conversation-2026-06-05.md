# Trae Trial Conversation Notes - 2026-06-05

## Context

User reported two recurring operational issues in the Trae python-timesheet trial workflow:

1. PPE environment settings must be treated as a pre-flight requirement.
2. Trae GUI/model often stalls or errors mid-task, requiring manual "继续" prompts.
3. Feishu/Lark Bitable submission via GUI took too long; future work should prefer SDK, CLI, MCP, or OpenAPI automation.

Working project root:

```text
/home/jianglei/zuoye/traedocker
```

## PPE Settings Mentioned

The user provided this Trae settings shape:

```json
{
  "git.openRepositoryInParentFolders": "always",
  "AI.toolcall.v2.command.allowList": "[\"sort\",\"tail\",\"cp\"]",
  "AI.toolcall.reviewMode.ide": "skip",
  "AI.toolcall.reviewMode.solo": "skip",
  "AI.toolcall.v2.ide.mcp.autoRun": "alwaysRun",
  "AI.toolcall.v2.ide.command.mode": "alwaysRun",
  "AI.toolcall.v2.solo.command.mode": "alwaysRun",
  "AI.rules.importClaudeMd": true,
  "AI.toolcall.v2.fileOp.allowPaths": "[\"kill\"]",
  "ai_assistant.request.env": "ppe",
  "ai_assistant.request.ppe": "ppe_data_label_trae"
}
```

Hard requirement for real runs:

```text
ai_assistant.request.env = ppe
ai_assistant.request.ppe = ppe_data_label_trae
```

## Implemented Changes

Updated `batch_runner.sh`:

- Added `TRAE_SETTINGS_JSON`, `TRAE_PPE_CHECK`, `TRAE_CONTINUE_TEXT`, `TRAE_CONTINUE_TIMES`, and `TRAE_CONTINUE_INTERVAL`.
- Added `TRAE_AUTO_CONTINUE_ON_TIMEOUT` and `TRAE_AUTO_CONTINUE_MAX`.
- Added `check_ppe_config`.
- Added `send_continue_cli`.
- `run_one` now checks PPE before model switching.
- `wait_for_completion` can optionally send bounded "继续" prompts after auto-wait timeout.
- Added CLI commands:
  - `bash batch_runner.sh ppe`
  - `bash batch_runner.sh continue [times] [text]`
- Help output now documents the timeout recovery mode:

```bash
TRAE_AUTO_CONTINUE_ON_TIMEOUT=on TRAE_AUTO_CONTINUE_MAX=3 TRAE_SUBMIT_MODE=cli TRAE_CONFIRM_MODE=auto bash batch_runner.sh run <prompt_num> <model_num>
```

Updated the `trae-trial-runner` skill:

- `/home/jianglei/.codex/skills/trae-trial-runner/SKILL.md`
- `/home/jianglei/.codex/skills/trae-trial-runner/references/workflow.md`

The skill now records:

- PPE check is a hard pre-flight requirement.
- "继续" should be a bounded recovery action, not an unbounded loop.
- Bitable submission should prefer OpenAPI, SDK, MCP, or CLI.
- Playwright/GUI automation is a fallback only when API credentials or attachment APIs are unavailable.

## Bitable Strategy

Existing OpenAPI skeleton:

```text
bitable-openapi-sync/
```

Preferred flow:

```bash
cd bitable-openapi-sync
python3 sync_bitable.py --config config.local.json --data records.local.json --offline-plan
python3 sync_bitable.py --config config.local.json --data records.local.json
python3 sync_bitable.py --config config.local.json --data records.local.json --apply
```

Credential handling:

```bash
export FEISHU_TENANT_ACCESS_TOKEN='...'
```

or:

```bash
export FEISHU_APP_ID='...'
export FEISHU_APP_SECRET='...'
```

Rules:

- Do not commit real tokens, app secrets, cookies, private app/table IDs, record IDs, raw API responses, or business data.
- Resolve field schema from the API.
- Map logical field names to field IDs at runtime.
- Use a stable unique key, usually `session_id`.
- Re-read server state after writing and compare missing rows, wrong fields, and missing attachments.

## Verification Performed

Commands run successfully:

```bash
bash -n batch_runner.sh
bash batch_runner.sh ppe
python3 -m py_compile trae_model_state.py bitable-openapi-sync/sync_bitable.py
python3 bitable-openapi-sync/sync_bitable.py --config bitable-openapi-sync/config.example.json --data bitable-openapi-sync/records.example.json --offline-plan
```

Observed PPE confirmation:

```text
Trae PPE: ppe / ppe_data_label_trae
```

OpenAPI offline plan confirmed:

```text
record_count: 2
unique_key: external_id
unique_key_present: true
unmapped_data_fields: []
```

## Important Follow-up Rule

For future trial work:

1. Run `bash batch_runner.sh ppe` before any real rollout batch.
2. If Trae stalls, use `bash batch_runner.sh continue` or bounded auto-continue.
3. For Feishu/Lark Bitable, start with `bitable-openapi-sync` or official SDK/CLI/MCP.
4. Use Playwright GUI automation only as a fallback, and always verify by server state.
