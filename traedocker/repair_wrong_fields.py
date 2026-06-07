import asyncio

from playwright.async_api import async_playwright

import submit_missing_rollouts as submit


MODEL_OPTION_IDS = {
    "GPT5.4": "opttmG9mvd",
    "Gemini3.1pro": "optFKlmCZ1",
    "DeepSeekv4": "opt8PIgTPC",
    "Doubao-Seed-2.0-Code": "optdq7pjiH",
    "MinMax-M2.7": "optpJxwC4R",
    "GLM-5.1": "opt4VtM6Yv",
    "Qwen3.6-Plus": "optFeV1aEq",
}

SCORE_OPTION_IDS = {
    "0": "optSaqIhP9",
    "1": "optjodJbEG",
    "2": "optOxnPN6c",
}


def cell_value(field_name, expected):
    if field_name == "prompt_index":
        return {"type": 2, "value": int(expected)}
    if field_name in {"rollout_id", "session_id", "score_reason"}:
        return {"type": 1, "value": [{"type": "text", "text": str(expected)}]}
    if field_name == "model_name":
        return {"type": 3, "value": MODEL_OPTION_IDS[expected]}
    if field_name == "score":
        return {"type": 3, "value": SCORE_OPTION_IDS[str(expected)]}
    raise KeyError(field_name)


async def apply_updates(page, updates):
    return await page.evaluate(
        """
        ({ table, view, updates }) => {
          const result = window.bitableStore.commandManager.execute({
            cmd: 'SetRecords',
            tableId: table,
            viewId: view,
            data: updates,
            ignoreCheckRecordLoaded: true,
          });
          return JSON.parse(JSON.stringify(result, (k, v) => typeof v === 'function' ? '[function]' : v));
        }
        """,
        {"table": submit.TABLE_ID, "view": submit.VIEW_ID, "updates": updates},
    )


async def main():
    rollouts = submit.load_rollouts()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9235")
        page = [p for p in browser.contexts[0].pages if "larkoffice" in p.url][0]
        await page.bring_to_front()

        for attempt in range(1, 4):
            missing, wrong_git, wrong_fields, rows = await submit.get_missing(page, rollouts)
            print(
                f"Attempt {attempt}: rows={len(rows)} missing={len(missing)} "
                f"wrong_git={len(wrong_git)} wrong_fields={len(wrong_fields)}"
            )
            if missing or wrong_git:
                for item in missing:
                    print(f"  missing: P{item['prompt']} R{item['rollout_id']} {item['session_id']}")
                for item, row in wrong_git:
                    print(f"  wrong git: {row['recordId']} {item['session_id']} expected {item['patch_name']}")
                break
            if not wrong_fields:
                break

            updates = {}
            for _rollout, row, diffs in wrong_fields:
                record_updates = updates.setdefault(row["recordId"], {})
                for field_name, _actual, expected in diffs:
                    record_updates[submit.FIELDS[field_name]] = cell_value(field_name, expected)

            result = await apply_updates(page, updates)
            print(
                f"  SetRecords result={result.get('result')} "
                f"records={len(updates)} actions={len(result.get('operation', {}).get('actions', []))}"
            )
            await asyncio.sleep(6)

        missing, wrong_git, wrong_fields, rows = await submit.get_missing(page, rollouts)
        print(
            f"FINAL rows={len(rows)} missing={len(missing)} "
            f"wrong_git={len(wrong_git)} wrong_fields={len(wrong_fields)}"
        )
        for rollout, row, diffs in wrong_fields[:50]:
            detail = "; ".join(f"{key}: {actual!r} != {expected!r}" for key, actual, expected in diffs)
            print(f"  wrong fields: {row['recordId']} P{rollout['prompt']} R{rollout['rollout_id']} {detail}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
