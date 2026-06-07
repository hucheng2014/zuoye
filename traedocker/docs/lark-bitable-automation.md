# Lark/Feishu Bitable Automation Notes

This note records a sanitized workflow for filling Lark/Feishu Bitable tables when
the grid is rendered with canvas/virtualized UI. It intentionally omits real base
tokens, table IDs, field IDs, user IDs, cookies, session IDs, record IDs, file
tokens, and business data.

## Problem

Canvas-rendered Bitable grids are hard to automate with browser agents:

- Grid cells may not exist as normal DOM nodes.
- Row coordinates shift with virtualization, scrolling, grouping, and hierarchy.
- Dropdown menus are rendered in portals and often contain non-leaf wrapper nodes.
- Attachment inputs may only appear after a real file chooser click.
- Text fields may use rich `contenteditable` editors plus hidden read-only inputs.
- UI success is not enough. Values can look filled locally but fail to save.

The reliable strategy is to avoid the canvas grid whenever possible. Use an API,
SDK, MCP server, or an already authenticated browser page to read and write
records, then verify from server state.

## Preferred Approach

Use official OpenAPI-style operations instead of UI coordinates:

1. Resolve the target app/base, table, view, and field schema.
2. Convert human field names to field IDs at runtime.
3. Build typed cell values:
   - Text: rich text segments, for example `[{ "type": "text", "text": "..." }]`
   - Number: numeric value
   - Single select: option ID, not display text
   - Attachment: uploaded file token/object accepted by the field
4. Use batch create or batch update records.
5. Re-read records from the server and compare expected values.
6. Treat verification as part of the write operation, not a separate manual check.

Useful official/API-oriented starting points:

- Lark OpenAPI SDKs: <https://github.com/larksuite/oapi-sdk-python>
- Lark OpenAPI MCP server: <https://github.com/larksuite/lark-openapi-mcp>
- Lark/Feishu CLI: <https://github.com/larksuite/cli>
- Lark CLI issue with attachment upload details for Bitable attachment fields:
  <https://github.com/larksuite/cli/issues/143>
- Feishu/Lark OpenAPI docs: <https://open.feishu.cn/document/>

Community examples that may be useful for quick prototypes:

- `dungeer619/feishu-bitable-python-tool`:
  <https://github.com/dungeer619/feishu-bitable-python-tool>
- `BlueSkyXN/Feishu-Bitable-Python-API`:
  <https://github.com/BlueSkyXN/Feishu-Bitable-Python-API>
  This project says it is no longer maintained, so treat it as a reference only.

## Browser Fallback

When OpenAPI credentials are unavailable but a browser is already logged in, use
browser automation only as a fallback. Prefer the record drawer/card over the
canvas grid.

Recommended rules:

- Open the "Add Record" drawer, not an arbitrary grid cell.
- Locate fields by visible label, then operate inside that field row.
- For text/rich-text fields, click the visible `contenteditable` editor and use
  `keyboard.insert_text()`. Do not type into hidden read-only inputs.
- For select fields, click only the exact visible leaf option whose text equals
  the expected label. Ignore wrapper elements that contain multiple options.
- For attachments, use Playwright's `expect_file_chooser()` around the real click
  on the attachment button, then set the file chooser files.
- Handle unsaved-change dialogs explicitly and only click visible dialog buttons.
- After each submit, re-read server state and verify by stable keys such as
  `session_id` or another unique business key.

Sketch:

```python
async def fill_text_field(page, field_label, value):
    row = await find_field_row(page, field_label)
    box = await row.evaluate("""
      el => {
        const target = el.querySelector('[contenteditable="true"], textarea, input:not([readonly])');
        const r = (target || el).getBoundingClientRect();
        return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
      }
    """)
    await page.mouse.click(box["x"], box["y"])
    await page.keyboard.press("Control+A")
    await page.keyboard.press("Backspace")
    await page.keyboard.insert_text(str(value))
```

```python
async def upload_attachment(page, field_label, file_path):
    row = await find_field_row(page, field_label)
    button_box = await locate_visible_attachment_button(row)
    async with page.expect_file_chooser(timeout=10_000) as chooser_info:
        await page.mouse.click(button_box["x"], button_box["y"])
    chooser = await chooser_info.value
    await chooser.set_files(file_path)
```

## Verification Pattern

Verification should compare the server's saved values, not the currently visible
UI state.

Minimum checks:

- Expected unique key exists exactly once.
- Required fields match expected normalized values.
- Single-select option IDs resolve to expected display labels.
- Attachment field contains the expected file name or token.
- No stale partial records were created after failed attempts.

Use idempotent repair:

1. Read all server records.
2. Compute `missing`, `wrong_attachment`, and `wrong_fields`.
3. Create only `missing`.
4. Batch update only `wrong_fields`.
5. Repeat verification until all three sets are empty.

For hierarchical Bitable tasks, verify the tree shape and field distribution in
addition to row values. When a successful sample tab exists, read it from server
state and compare counts by level:

- Total rows by role, for example repo/topic, prompt, rollout, and stray.
- Parent-child counts, for example each prompt should own the expected number of
  rollout rows.
- Field ownership by level, because some fields are intentionally repo-level
  only while others are copied down to child rows.
- Required attachment distribution, for example environment files on the repo
  row and patches on rollout rows.

Do not assume every field should be propagated to every level. In the BBS trial
tables, a successful sample showed this shape:

```text
repo/topic row:
  channel/vendor/submission/status fields and environment attachments

prompt rows:
  prompt metadata only, plus inherited source fields when required

rollout rows:
  prompt text, rollout id, session id, model, score, reason, git_diff
```

When repairing hierarchy, build a canonical keep set from stable identifiers
before deleting:

1. Keep the repo/topic row with `repo.zip` and `Dockerfile`.
2. Keep one complete prompt row per `prompt_index`.
3. Keep rollout rows whose `session_id` appears in the local rollout log.
4. Delete only empty, duplicate, or fake/partial rows outside that keep set.

For browser-page internal writes through `window.bitableStore`, inspect the
command result. A mixed `SetRecords` batch may fail entirely if one field is
blocked or has a bad cell shape. Split writes by field or by small chunks and
re-read after each batch. Some fields can be controlled by table automation or
permissions; report those as blocked instead of claiming success.

If the table has built-in AI/quality-check columns, treat those checks as part
of completion. For trial labeling tables, prompt rows may need a prompt quality
check to become valid before full rollout, and rollout rows may need a score
quality check to become reasonable after score, reason, and patch attachments
are filled. Do not mark the table complete just because required cells are
non-empty.

## Lessons Learned

- Canvas automation should be treated as a last resort.
- Coordinate clicks are useful for exploration, not production writes.
- A partial success can be worse than a hard failure, because wrong select values
  or empty text fields may look plausible in the UI.
- Sample-based comparison is valuable, but preserve task-specific business
  values instead of copying sample values blindly.
- Keep repair scripts idempotent. Always recompute missing/wrong records from
  the server before writing.
- Never commit app tokens, cookies, bearer tokens, base/table IDs from private
  tasks, screenshots with private data, or raw trial logs to a public repository.

## Public-Repo Checklist

Before publishing automation notes or scripts:

- Replace real IDs with placeholders.
- Remove cookies, CSRF tokens, PATs, and internal API responses.
- Remove screenshots unless they are fully redacted.
- Keep field names generic if they reveal private task structure.
- Prefer references to official SDKs/docs over copied private payloads.
- Add a secret scan step before commit.
