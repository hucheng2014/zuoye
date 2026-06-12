require('./_timeout');
const { chromium } = require('playwright');
const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot') || p.url().includes('apple')) || ctx.pages()[0];

  const bodyText = await page.locator('body').innerText({ timeout: 3000 }).catch(e => e.message);

  // Check all frames
  const frameTexts = [];
  for (const f of page.frames()) {
    try {
      const t = await f.locator('body').innerText({ timeout: 800 }).catch(() => '');
      if (t.trim()) frameTexts.push({ url: f.url(), text: t.trim().slice(0, 500) });
    } catch {}
  }

  // Check for buttons
  const buttons = await page.locator('button').evaluateAll(els =>
    els.map(el => ({
      text: (el.innerText || '').trim().slice(0, 50),
      visible: el.offsetParent !== null,
      ariaLabel: el.getAttribute('aria-label') || '',
    }))
  );

  console.log(JSON.stringify({ url: page.url(), buttons, frameTexts }, null, 2));
  await browser.close();
}

main().catch(e => { console.error(e.message); process.exit(1); });
