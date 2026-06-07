import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        target_page = None
        for idx, page in enumerate(context.pages):
            title = await page.title()
            if "需求二正式作业表_BBS" in title and not title.startswith("\u202d"):
                target_page = page
                break
        if not target_page:
            target_page = context.pages[0]
            
        await target_page.bring_to_front()
        await asyncio.sleep(1)
        
        # Ensure drawer is open
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        if not drawer_visible:
            await target_page.locator('[data-e2e="bitable-add-record-btn"]').first.click(force=True)
            await asyncio.sleep(3)
            
        # Get repo_type row
        row = target_page.locator(".base_record_card_field_editor_wrapper, .bitable-field-item").filter(
            has=target_page.locator(".bitable-field-name, [class*='field-name']", has_text="repo_type")
        ).first
        
        # Click dropdown trigger
        print("Clicking dropdown trigger...")
        await row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button']").first.click(force=True)
        await asyncio.sleep(2)
        
        # Look for elements containing '公有仓库' in the entire DOM
        elements = await target_page.evaluate("""
            () => {
                const results = [];
                const all = document.querySelectorAll('*');
                all.forEach(el => {
                    if (el.innerText && el.innerText.trim() === '公有仓库') {
                        // Traverse up to find parent containers with classes or ids
                        let parents = [];
                        let p = el.parentElement;
                        for (let i = 0; i < 5 && p; i++) {
                            parents.push({
                                tagName: p.tagName,
                                className: p.className,
                                outerHTML: p.outerHTML.substring(0, 100)
                            });
                            p = p.parentElement;
                        }
                        results.push({
                            tagName: el.tagName,
                            className: el.className,
                            html: el.outerHTML.substring(0, 300),
                            parents: parents
                        });
                    }
                });
                return results;
            }
        """)
        
        print(f"Found {len(elements)} elements containing '公有仓库':")
        for idx, el in enumerate(elements):
            print(f"[{idx}] Tag: {el['tagName']}, Class: {el['className']}")
            print(f"    HTML: {el['html']}")
            print(f"    Parents:")
            for p_idx, p in enumerate(el['parents']):
                print(f"      ({p_idx}) Tag: {p['tagName']}, Class: {p['className']}, HTML: {p['outerHTML']}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
