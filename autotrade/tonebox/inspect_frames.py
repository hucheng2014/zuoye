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
            
        print(f"Target Page URL: {target_page.url}")
        print(f"Total frames: {len(target_page.frames)}")
        
        # Click dockerfile row attachment button first to make sure it's triggered
        row = target_page.locator(".base_record_card_field_editor_wrapper, .bitable-field-item").filter(
            has=target_page.locator(".bitable-field-name, [class*='field-name']", has_text="dockerfile")
        ).first
        await row.evaluate("el => el.scrollIntoView({ block: 'center' })")
        await asyncio.sleep(1)
        print("Clicking Add attachment...")
        await row.locator("button, .b-collapsed-attach-editor__btn, .bitable-card-edit-cell-editor-Attachment").first.click(force=True)
        await asyncio.sleep(2)
        
        for idx, frame in enumerate(target_page.frames):
            print(f"Frame [{idx}] Name: '{frame.name}', URL: {frame.url}")
            # Check for input#attachment-upload inside this frame
            try:
                exists = await frame.evaluate("() => !!document.querySelector('input#attachment-upload')")
                file_count = await frame.evaluate("() => document.querySelectorAll('input[type=\"file\"]').length")
                print(f"  -> input#attachment-upload exists: {exists}")
                print(f"  -> input[type='file'] count: {file_count}")
                if file_count > 0:
                    htmls = await frame.evaluate("""
                        () => Array.from(document.querySelectorAll('input[type="file"]')).map(el => el.outerHTML)
                    """)
                    print(f"  -> File inputs: {htmls}")
            except Exception as e:
                print(f"  -> Error: {e}")
                
        # Close dialog
        await target_page.keyboard.press("Escape")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
