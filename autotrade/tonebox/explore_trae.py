"""探索 Trae 的页面结构，找到 AI 聊天面板"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")

        print(f"Browser connected")
        print(f"Contexts: {len(browser.contexts)}")

        for ci, context in enumerate(browser.contexts):
            print(f"\n--- Context {ci} ---")
            print(f"  Pages: {len(context.pages)}")
            for pi, page in enumerate(context.pages):
                title = await page.title()
                url = page.url[:100]
                print(f"  Page [{pi}]: title='{title}'")
                print(f"           url='{url}'")
                try:
                    body_text = await page.inner_text('body') if await page.query_selector('body') else ""
                    print(f"           body_text[:200]={body_text[:200]}")
                except:
                    print(f"           body_text=<error>")

        # Also check all targets via CDP
        cdp = await context.cdp_session if browser.contexts else None
        if cdp:
            targets = await browser.contexts[0].cdp_session.send('Target.getTargets')
            print(f"\n--- All targets ---")
            for t in targets.get('targetInfos', []):
                print(f"  type={t['type']:12s} title='{t['title'][:60]:60s}' url='{t['url'][:80]}'")

if __name__ == "__main__":
    asyncio.run(main())
