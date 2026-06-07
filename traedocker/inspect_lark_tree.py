import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        target_page = None
        for page in context.pages:
            url = page.url
            if "bytedance.larkoffice.com" in url:
                target_page = page
                break
                
        if not target_page:
            print("No Lark page found!")
            await browser.close()
            return
            
        print(f"Inspecting Lark page: {await target_page.title()}")
        
        # Capture inner text of the body to see if other records are mentioned
        text = await target_page.evaluate("() => document.body.innerText")
        
        # Check if B00001629 or B00001630 are in text
        print("Does text contain B00001629?", "B00001629" in text)
        print("Does text contain B00001630?", "B00001630" in text)
        
        # Let's count row elements
        rows = target_page.locator(".grid-row, [class*='row'], tr")
        print("Number of rows found:", await rows.count())
        
        # Take a screenshot focusing on the tree list
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/inspect_tree.png")
        print("Saved inspect_tree.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
