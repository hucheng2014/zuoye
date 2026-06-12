import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        target_page = None
        for page in context.pages:
            title = await page.title()
            if "需求二正式作业表_BBS" in title and not title.startswith("\u202d"):
                target_page = page
                break
        if not target_page:
            target_page = context.pages[0]
            
        await target_page.bring_to_front()
        await asyncio.sleep(1)
        
        # Let's inspect the fields in the drawer. 
        # Are there any link fields, sub-tables, or relation fields?
        drawer_fields = await target_page.evaluate("""
            () => {
                const results = [];
                const card = document.querySelector('.bitable-record-card-content, [class*="record-card"]');
                if (!card) return "CARD NOT FOUND";
                
                // Find wrappers
                const wrappers = card.querySelectorAll('.bitable-node-container-wrapper-field');
                wrappers.forEach((wrap, idx) => {
                    const label = wrap.querySelector('.bitable-field-name')?.innerText || 'NO_LABEL';
                    // Find editor class
                    const editor = wrap.querySelector('[class*="editor"], [class*="cell"]');
                    const editorClass = editor ? editor.className : 'NONE';
                    
                    results.push({
                        idx,
                        label,
                        editorClass,
                        htmlSnippet: wrap.outerHTML.substring(0, 400)
                    });
                });
                return results;
            }
        """)
        
        print("Drawer field structure:")
        for f in drawer_fields:
            print(f"[{f['idx']}] Label: '{f['label']}'")
            print(f"    Editor Class: {f['editorClass']}")
            print(f"    HTML Snippet: {f['htmlSnippet']}")
            print("-" * 40)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
