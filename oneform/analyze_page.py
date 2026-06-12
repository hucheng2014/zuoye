import asyncio
import json
from playwright.async_api import async_playwright

async def analyze():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        page = None
        for pg in ctx.pages:
            if "tryrating" in pg.url.lower():
                page = pg
                break
        if not page:
            page = ctx.pages[0]

        JS = """
        () => {
            const out = {};

            // Check wrapper[13] (the empty one after Utterance label)
            const wrappers = document.querySelectorAll('.extra-wrapper');
            if (wrappers[13]) {
                out.wrapper13_html = wrappers[13].innerHTML.substring(0, 1000);
                out.wrapper13_children = wrappers[13].querySelectorAll('*').length;
            }

            // Check ALL iframes
            const iframes = document.querySelectorAll('iframe');
            out.iframeCount = iframes.length;
            out.iframes = [];
            for (let i = 0; i < iframes.length; i++) {
                const iframe = iframes[i];
                let content = 'N/A';
                try {
                    const doc = iframe.contentDocument || iframe.contentWindow.document;
                    content = doc.body ? doc.body.innerText.trim() : doc.documentElement.innerText.trim();
                } catch(e) {
                    content = 'CROSS_ORIGIN: ' + e.message;
                }
                out.iframes.push({
                    i: i,
                    src: (iframe.src || '').substring(0, 200),
                    width: iframe.width,
                    height: iframe.height,
                    style: (iframe.getAttribute('style') || '').substring(0, 100),
                    content: content.substring(0, 300),
                    parent: iframe.parentElement ? iframe.parentElement.className.substring(0, 60) : ''
                });
            }

            // Also check for shadow DOM elements
            const shadowHosts = [];
            wrappers.forEach((w, i) => {
                if (w.shadowRoot) {
                    shadowHosts.push({i: i, text: w.shadowRoot.textContent.substring(0, 100)});
                }
            });
            out.shadowHosts = shadowHosts;

            // Check wrapper 12-15 HTML in detail
            out.wrappers_detail = [];
            for (let i = 12; i <= 15; i++) {
                if (wrappers[i]) {
                    out.wrappers_detail.push({
                        i: i,
                        html: wrappers[i].innerHTML.substring(0, 500),
                        childCount: wrappers[i].children.length
                    });
                }
            }

            return out;
        }
        """

        result = await page.evaluate(JS)
        print(json.dumps(result, indent=2, ensure_ascii=False))

asyncio.run(analyze())
