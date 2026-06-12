"""
Repair script: find the 15 rollout records missing git_diff and upload the files.
Strategy: scroll through the table, open each row, check session_id, upload if needed.
"""
import asyncio, os, json
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# The 15 records missing git_diff (session_id -> patch_file)
MISSING = {
    # P1 R1-5, P2 R1 (first run failures)
    "6a204c322c9cb2ad5f585f52": "prompt1_doubao.patch",
    "6a2053d66b996e39953eb8b9": "prompt1_gpt5.patch",
    "6a2054e16b996e39953eb8e2": "prompt1_gemini.patch",
    "6a20556f6b996e39953eb8f0": "prompt1_deepseek.patch",
    "6a2056676b996e39953eb90a": "prompt1_minmax.patch",
    "6a205b186b996e39953eb918": "prompt2_doubao.patch",
    # P6 R2-5, P7 R1-5 (dialog overlay failures)
    "6a210b431ceaa60b3bb2157c": "prompt6_gpt5.patch",
    "6a21134be0b94db7064126d7": "prompt6_gemini.patch",
    "6a2116eb517dbb2a2bff43f9": "prompt6_deepseek.patch",
    "6a2119a7517dbb2a2bff44d3": "prompt6_qwen.patch",
    "6a211cd7517dbb2a2bff455f": "prompt7_doubao.patch",
    "6a211f6b517dbb2a2bff45b8": "prompt7_gpt5.patch",
    "6a212133d6093219993a0ce8": "prompt7_gemini.patch",
    "6a212498d6093219993a0d63": "prompt7_deepseek.patch",
    "6a2126e5d6093219993a0dba": "prompt7_minmax.patch",
}

async def main():
    repaired = []
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        pg = [x for x in b.contexts[0].pages if "larkoffice" in x.url][0]
        await pg.bring_to_front()
        for _ in range(3):
            await pg.keyboard.press("Escape")
            await asyncio.sleep(0.3)
        await asyncio.sleep(2)
        
        # Helper: get session_id from open drawer
        async def get_drawer_session_id():
            return await pg.evaluate("""
            () => {
                const all = document.querySelectorAll('*');
                for (const el of all) {
                    if (el.className?.includes?.('field-name') && el.innerText?.trim() === 'session_id') {
                        const p = el.closest('[class*="field-item"], [class*="field-wrapper"], [class*="field-editor"]');
                        if (p) {
                            const inp = p.querySelector('input, textarea, [contenteditable]');
                            if (inp) return inp.value || inp.innerText?.trim();
                        }
                    }
                }
                return null;
            }
            """)
        
        # Helper: upload git_diff to open drawer
        async def upload_to_open_record(patch_file):
            path = os.path.join(BASE_DIR, patch_file)
            # Scroll to git_diff
            for _ in range(12):
                await pg.evaluate("() => { const d=document.querySelector('[class*=record-card],.base-record-card'); if(d)d.scrollBy(0,300); }")
                await asyncio.sleep(0.5)
            # Find and click last attachment button
            all_attach = pg.locator(".b-collapsed-attach-editor__btn")
            cnt = await all_attach.count()
            if cnt == 0:
                print("  No attachment buttons found")
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
        
        # Scroll to bottom of the table to see the newly created records
        # Then use keyboard navigation (End key) and arrow keys to go through rows
        
        # Click somewhere in the table grid to focus it
        await pg.mouse.click(400, 200)
        await asyncio.sleep(1)
        
        # Press Ctrl+End to go to last row
        await pg.keyboard.press("Control+End")
        await asyncio.sleep(2)
        
        # Try to open rows by pressing Enter or clicking expand
        # We'll try a different approach: use the search/filter
        
        # Apply filter: session_id contains each target
        # Actually, let's just scroll through recent rows by clicking on them
        
        # Take screenshot to see current state
        await pg.screenshot(path=os.path.join(BASE_DIR, "repair_start.png"))
        
        # Try to navigate using keyboard
        # Press Tab to move through records, Enter to open
        remaining = set(MISSING.keys())
        
        # Approach: iterate through rows using coordinates
        # The table rows are at fixed heights. Try clicking rows at y positions
        # starting from around the last visible rows
        
        print(f"Need to repair {len(remaining)} records")
        print("Attempting row navigation...")
        
        # Try clicking the expand icon for last rows
        for row_offset in range(50):
            if not remaining:
                break
            # Click at y = 400 - row_offset*20 (guessing row positions)
            y = 400 - row_offset * 22
            if y < 120:
                break
            
            # Hover to see expand icon
            await pg.mouse.move(100, y)
            await asyncio.sleep(0.3)
            
            # Try to click expand icon (usually at x=60-80)
            await pg.mouse.click(65, y)
            await asyncio.sleep(2)
            
            # Check if drawer opened
            drawer = pg.locator('[class*="record-card"], .base-record-card')
            if await drawer.count() > 0:
                # Read session_id
                sid = await get_drawer_session_id()
                if sid and sid in remaining:
                    print(f"Found record with session_id={sid[:16]}...")
                    patch = MISSING[sid]
                    ok = await upload_to_open_record(patch)
                    if ok:
                        # Submit
                        submit = pg.locator("button:has-text('Submit')").first
                        if await submit.count():
                            await submit.click(force=True)
                        else:
                            await pg.keyboard.press("Escape")
                        await asyncio.sleep(3)
                        repaired.append(sid)
                        remaining.discard(sid)
                        print(f"  Repaired! Remaining: {len(remaining)}")
                else:
                    # Close drawer
                    for _ in range(3):
                        await pg.keyboard.press("Escape")
                        await asyncio.sleep(0.3)
        
        print(f"\nRepaired: {len(repaired)}/{len(MISSING)}")
        if remaining:
            print(f"Still missing: {list(remaining)[:3]}...")
        await pg.screenshot(path=os.path.join(BASE_DIR, "repair_done.png"))
        await b.close()

asyncio.run(main())
