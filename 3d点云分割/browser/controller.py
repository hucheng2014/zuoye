import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class BrowserController:
    def __init__(self, cdp_url: str, title_keyword: str, url_host: str):
        self.cdp_url = cdp_url
        self.title_keyword = title_keyword
        self.url_host = url_host
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def connect(self) -> Page:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
        self.context = self.browser.contexts[0] if self.browser.contexts else await self.browser.new_context()
        self.page = await self._find_annotation_page()
        if not self.page:
            raise RuntimeError("Annotation page not found")
        await self.page.bring_to_front()
        return self.page

    async def _find_annotation_page(self) -> Optional[Page]:
        for p in self.context.pages:
            title = await p.title()
            if self.title_keyword in title and self.url_host in p.url:
                return p
        return None

    async def heartbeat(self, move_pixels: int = 5):
        if not self.page:
            return
        await self.page.mouse.move(move_pixels, move_pixels)
        await self.page.mouse.move(0, 0)
        await self.page.evaluate("() => { window.lastAutoActivity = Date.now(); }")

    async def is_pause_modal_present(self) -> bool:
        if not self.page:
            return False
        text = "监测到您长时间没有操作"
        try:
            body = await self.page.inner_text("body", timeout=2000)
            return text in body
        except Exception:
            return False

    async def reload_annotation_page(self):
        if not self.page:
            raise RuntimeError("Not connected")
        await self.page.reload(wait_until="networkidle", timeout=60000)
        await self.page.wait_for_timeout(3000)

    async def close(self):
        if self.browser:
            await self.browser.close()
        if hasattr(self, "playwright"):
            await self.playwright.stop()
