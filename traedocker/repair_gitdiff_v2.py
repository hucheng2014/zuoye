"""
Repair: upload git_diff to the 15 records that are missing it.
Uses Filter to isolate specific records by session_id.
"""
import asyncio, os
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MISSING = [
    ("6a204c322c9cb2ad5f585f52", "prompt1_doubao.patch"),
    ("6a2053d66b996e39953eb8b9", "prompt1_gpt5.patch"),
    ("6a2054e16b996e39953eb8e2", "prompt1_gemini.patch"),
    ("6a20556f6b996e39953eb8f0", "prompt1_deepseek.patch"),
    ("6a2056676b996e39953eb90a", "prompt1_minmax.patch"),
    ("6a205b186b996e39953eb918", "prompt2_doubao.patch"),
    ("6a210b431ceaa60b3bb2157c", "prompt6_gpt5.patch"),
    ("6a21134be0b94db7064126d7", "prompt6_gemini.patch"),
    ("6a2116eb517dbb2a2bff43f9", "prompt6_deepseek.patch"),
    ("6a2119a7517dbb2a2bff44d3", "prompt6_qwen.patch"),
    ("6a211cd7517dbb2a2bff455f", "prompt7_doubao.patch"),
    ("6a211f6b517dbb2a2bff45b8", "prompt7_gpt5.patch"),
    ("6a212133d6093219993a0ce8", "prompt7_gemini.patch"),
    ("6a212498d6093219993a0d63", "prompt7_deepseek.patch"),
    ("6a2126e5d6093219993a0dba", "prompt7_minmax.patch"),
]

async def upload_in_drawer(pg, patch_file):
    path = os.path.join(BASE_DIR, patch_file)
    if not os.path.exists(path):
        print(f"  [SKIP] {patch_file} not found")
        return False
    for _ in range(12):
        await pg.evaluate("() => { const d=document.querySelector('[class*=record-card],.base-record-card'); if(d)d.scrollBy(0,300); }")
        await asyncio.sleep(0.5)
    all_attach = pg.locator(".b-collapsed-attach-editor__btn")
    cnt = await all_attach.count()
    if cnt == 0:
        print("  No attach buttons")
        return False
    last_btn = all_attach.last
    await last_btn.scroll_into_view_if_needed()
    await asyncio.sleep(0.8)
    try:
        await last_btn.click(timeout=5000)
    except:
        await last_btn.click(force=True)
    await asyncio.sleep(1.5)
    try:
        await pg.locator("input#attachment-upload").set_input_files(path, timeout=8000)
        await asyncio.sleep(6)
        print(f"  [OK] Uploaded {patch_file}")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        pg = [x for x in b.contexts[0].pages if "larkoffice" in x.url][0]
        await pg.bring_to_front()
        for _ in range(3):
            await pg.keyboard.press("Escape")
            await asyncio.sleep(0.3)
        await asyncio.sleep(2)

        repaired = 0
        for sid, patch in MISSING:
            print(f"\nRepairing: {sid[:16]}... -> {patch}")

            # Click Filter button
            filter_btn = pg.locator("button:has-text('Filter'), [class*='filter-btn'], [data-e2e*='filter']").first
            if await filter_btn.count() == 0:
                filter_btn = pg.locator("text=Filter").first
            await filter_btn.click(force=True)
            await asyncio.sleep(2)

            # Add condition (if filter panel is open)
            add_cond = pg.locator("button:has-text('Add condition'), button:has-text('添加条件'), [class*='add-condition']").first
            if await add_cond.count() > 0:
                await add_cond.click(force=True)
                await asyncio.sleep(1.5)
                # Select field: session_id
                field_sel = pg.locator("[class*='filter-field'], [class*='condition-field']").last
                await field_sel.click(force=True)
                await asyncio.sleep(1)
                opt = pg.locator("[class*='select-option'], [role='option']").filter(has_text="session_id").first
                if await opt.count():
                    await opt.click(force=True)
                    await asyncio.sleep(1)
                # Set value
                val_inp = pg.locator("[class*='filter-value'] input, [class*='condition-value'] input").last
                if await val_inp.count():
                    await val_inp.click(force=True)
                    await val_inp.fill(sid)
                    await asyncio.sleep(1)
                    await val_inp.press("Enter")
                    await asyncio.sleep(2)
            else:
                print("  Filter panel not found, closing")
                await pg.keyboard.press("Escape")
                continue

            # Close filter panel
            await pg.keyboard.press("Escape")
            await asyncio.sleep(1)

            # Now find the one matching row and open it
            # Try clicking around y=160-200 which is first data row
            expand_found = False
            for y in range(160, 300, 22):
                await pg.mouse.move(65, y)
                await asyncio.sleep(0.3)
                # Click expand icon area
                await pg.mouse.click(65, y)
                await asyncio.sleep(2)
                drawer = pg.locator('[class*="record-card"], .base-record-card')
                if await drawer.count() > 0:
                    # Verify this is the right record by checking session_id
                    session_val = await pg.evaluate("""
                    () => {
                        const inputs = document.querySelectorAll('input, textarea, [contenteditable]');
                        for (const inp of inputs) {
                            const v = inp.value || inp.innerText || '';
                            if (v.length === 24 && /^[0-9a-f]{24}$/.test(v)) return v;
                        }
                        return null;
                    }
                    """)
                    if session_val == sid:
                        print(f"  Found matching record!")
                        ok = await upload_in_drawer(pg, patch)
                        if ok:
                            # Submit
                            submit = pg.locator("button:has-text('Submit')").first
                            if await submit.count():
                                await submit.click(force=True)
                            await asyncio.sleep(3)
                            repaired += 1
                        expand_found = True
                        break
                    else:
                        # Wrong record, close
                        for _ in range(2):
                            await pg.keyboard.press("Escape")
                            await asyncio.sleep(0.3)

            if not expand_found:
                print(f"  Could not find row for {sid[:16]}")

            # Clear filter for next iteration
            await asyncio.sleep(1)

        print(f"\nRepaired: {repaired}/{len(MISSING)}")
        await pg.screenshot(path=os.path.join(BASE_DIR, "repair_final.png"))
        await b.close()

asyncio.run(main())
