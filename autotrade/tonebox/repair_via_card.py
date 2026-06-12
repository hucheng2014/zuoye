"""
Repair git_diff for the 15 rollout records missing it.
Robust nav: prev-to-top (JS clicks, stop when disabled), then next-to-bottom,
checking every record's session_id and uploading patch for missing ones.
"""
import asyncio, os, re
from playwright.async_api import async_playwright

BASE_DIR = "/Users/xaa/zuoye/traedocker"

MISSING = {
    "6a204c322c9cb2ad5f585f52": "prompt1_doubao.patch",
    "6a2053d66b996e39953eb8b9": "prompt1_gpt5.patch",
    "6a2054e16b996e39953eb8e2": "prompt1_gemini.patch",
    "6a20556f6b996e39953eb8f0": "prompt1_deepseek.patch",
    "6a2056676b996e39953eb90a": "prompt1_minmax.patch",
    "6a205b186b996e39953eb918": "prompt2_doubao.patch",
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

async def read_sid(pg):
    txt = await pg.evaluate("""
    () => {
        const panels = document.querySelectorAll('[class*="card-modal"], [class*="record-card"]');
        let best=null,bw=0;
        for(const el of panels){if(el.offsetParent===null)continue;const r=el.getBoundingClientRect();if(r.width>bw){best=el;bw=r.width;}}
        return best?best.innerText:'';
    }
    """)
    m = re.findall(r'\b[0-9a-f]{24}\b', txt)
    return m[0] if m else None

async def click_nav(pg, direction):
    """JS click prev/next. Returns 'clicked', 'disabled', or 'missing'."""
    return await pg.evaluate(f"""
    () => {{
        const btn = document.querySelector('[data-e2e="bitable-card-modal-toolbar-{direction}"]');
        if (!btn) return 'missing';
        const dis = btn.disabled || btn.getAttribute('aria-disabled')==='true'
                    || (typeof btn.className==='string' && btn.className.includes('disabled'));
        if (dis) return 'disabled';
        btn.click();
        return 'clicked';
    }}
    """)

async def scroll_card_top(pg):
    await pg.evaluate("""
    () => { const sels=['[class*="card-modal"] [class*="scroll"]','[class*="card-modal-content"]','[class*="record-detail"]','[class*="card-modal"]'];
        for(const s of sels){const el=document.querySelector(s);if(el){el.scrollTop=0;return;}} }
    """)

async def scroll_to_gitdiff(pg):
    for _ in range(20):
        found = await pg.evaluate("""
        () => { for (const el of document.querySelectorAll('*')) {
            const cls=typeof el.className==='string'?el.className:'';
            if(cls.includes('field-name') && el.innerText?.replace(/\\u200b/g,'').trim()==='git_diff'){el.scrollIntoView({block:'center'});return true;} }
            return false; }
        """)
        if found:
            await asyncio.sleep(0.5); return True
        await pg.evaluate("""
        () => { const sels=['[class*="card-modal"] [class*="scroll"]','[class*="card-modal-content"]','[class*="record-detail"]','[class*="card-modal"]'];
            for(const s of sels){const el=document.querySelector(s);if(el&&el.scrollHeight>el.clientHeight){el.scrollBy(0,350);return;}} }
        """)
        await asyncio.sleep(0.35)
    return False

async def gitdiff_empty(pg):
    return await pg.evaluate("""
    () => { let lbl=null;
        for (const el of document.querySelectorAll('*')){const cls=typeof el.className==='string'?el.className:'';
            if(cls.includes('field-name')&&el.innerText?.replace(/\\u200b/g,'').trim()==='git_diff'){lbl=el;break;}}
        if(!lbl) return null;
        const cont=lbl.closest('[class*="field-item"],[class*="field-editor-container"],[class*="field-wrapper"],[class*="record-field"]')||lbl.parentElement?.parentElement;
        if(!cont) return null;
        const chips=cont.querySelectorAll('[class*="attach"][class*="item"],[class*="file-card"],[class*="thumbnail"],img');
        return chips.length===0; }
    """)

async def upload_gitdiff(pg, patch_file):
    path = os.path.join(BASE_DIR, patch_file)
    if not os.path.exists(path):
        print(f"    file missing: {path}"); return False
    clicked = await pg.evaluate("""
    () => { let lbl=null;
        for (const el of document.querySelectorAll('*')){const cls=typeof el.className==='string'?el.className:'';
            if(cls.includes('field-name')&&el.innerText?.replace(/\\u200b/g,'').trim()==='git_diff'){lbl=el;break;}}
        if(!lbl) return false;
        const cont=lbl.closest('[class*="field-item"],[class*="field-editor-container"],[class*="field-wrapper"],[class*="record-field"]')||lbl.parentElement?.parentElement;
        if(!cont) return false;
        const btn=cont.querySelector('.b-collapsed-attach-editor__btn,[class*="add-attach"],button');
        if(!btn) return false;
        btn.scrollIntoView({block:'center'}); btn.click(); return true; }
    """)
    if not clicked:
        print("    could not click add button"); return False
    await asyncio.sleep(1.5)
    try:
        await pg.locator("input#attachment-upload").set_input_files(path, timeout=8000)
        await asyncio.sleep(6)
        return True
    except Exception as e:
        print(f"    upload err: {e}")
        await pg.keyboard.press("Escape"); await asyncio.sleep(0.5)
        return False

async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        pg = [x for x in b.contexts[0].pages if "larkoffice" in x.url][0]
        await pg.bring_to_front()
        for _ in range(4):
            await pg.keyboard.press("Escape"); await asyncio.sleep(0.3)
        await asyncio.sleep(1)

        # Scroll grid to absolute top so row 1 = my first top-level record (B00002005)
        await pg.mouse.click(330, 250); await asyncio.sleep(0.4)
        await pg.keyboard.press("Control+Home"); await asyncio.sleep(1.2)

        # Open row 1 via right-click -> Open Record
        await pg.mouse.click(330, 198, button="right")
        await asyncio.sleep(1.5)
        loc = await pg.evaluate("""
        () => { for (const el of document.querySelectorAll('*')){ if(el.offsetParent===null)continue;
            const t=el.innerText?.trim();
            if((t==='Open Record'||t==='打开记录')&&el.children.length<=1){const r=el.getBoundingClientRect();return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};}}
            return null; }
        """)
        if loc:
            await pg.mouse.click(loc['x'], loc['y']); await asyncio.sleep(2.5)
        sid0 = await read_sid(pg)
        print(f"Opened row 1, sid={sid0}")

        # Navigate NEXT through all top-level (my 35) records, check each
        print("Scanning records via next...")
        repaired = {}
        for i in range(70):
            sid = await read_sid(pg)
            if sid:
                if sid in MISSING:
                    print(f"[{i}] {sid} (MISSING)")
                    if sid not in repaired:
                        patch = MISSING[sid]
                        await scroll_to_gitdiff(pg)
                        empty = await gitdiff_empty(pg)
                        if empty is False:
                            print("    already has attachment"); repaired[sid] = "already"
                        else:
                            print(f"    uploading {patch}...")
                            ok = await upload_gitdiff(pg, patch)
                            if ok:
                                print(f"    [OK] {patch}"); repaired[sid] = "done"
                            else:
                                print(f"    [FAIL] {patch}")
                else:
                    print(f"[{i}] {sid} (ok)")
                if len(repaired) >= len(MISSING):
                    print("All 15 handled!"); break
            else:
                print(f"[{i}] (no session_id record)")
            await scroll_card_top(pg); await asyncio.sleep(0.2)
            r = await click_nav(pg, "next")
            if r != "clicked":
                print(f"  end reached ({r})"); break
            await asyncio.sleep(1.1)

        done = [k for k in repaired if repaired[k] == "done"]
        already = [k for k in repaired if repaired[k] == "already"]
        print(f"\n=== Uploaded: {len(done)}, Already had: {len(already)} ===")
        miss = [f"{s[:12]}→{MISSING[s]}" for s in MISSING if s not in repaired]
        if miss:
            print(f"NOT handled ({len(miss)}):")
            for m in miss: print(f"  {m}")
        await b.close()

asyncio.run(main())
