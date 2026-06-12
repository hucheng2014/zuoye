"""探索 Trae 的所有 CDP targets，找到 AI 聊天面板"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]

        # Get CDP session
        cdp_session = await context.new_cdp_session(context.pages[0])

        # List all targets
        result = await cdp_session.send('Target.getTargets')
        print(f"Total targets: {len(result.get('targetInfos', []))}")
        print()
        for t in result.get('targetInfos', []):
            print(f"  targetId: {t['targetId'][:20]}")
            print(f"  type:     {t['type']}")
            print(f"  title:    {t['title'][:80]}")
            print(f"  url:      {t['url'][:120]}")
            print(f"  openerId: {t.get('openerId', 'N/A')[:20]}")
            print()

        # Try to attach to page targets and look for chat/AI elements
        for t in result.get('targetInfos', []):
            if t['type'] == 'page':
                try:
                    page = await context.new_page()
                    cdp2 = await context.new_cdp_session(page)
                    await cdp2.send('Target.attachToTarget', {'targetId': t['targetId'], 'flatten': True})
                    # Just trying
                except Exception as e:
                    print(f"  Error attaching to {t['title'][:30]}: {e}")
                finally:
                    await page.close() if page else None

if __name__ == "__main__":
    asyncio.run(main())
