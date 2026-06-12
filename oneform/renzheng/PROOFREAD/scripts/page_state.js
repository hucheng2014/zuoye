require('./_timeout');
const { chromium } = require('playwright');
const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot') || p.url().includes('apple')) || ctx.pages()[0];

  console.log('Page URL:', page.url());
  console.log('Page title:', await page.title());

  // Check all frames
  for (const f of page.frames()) {
    const url = f.url();
    if (url === 'about:blank') continue;
    const text = await f.locator('body').innerText({ timeout: 800 }).catch(() => '');
    if (!text.trim()) continue;
    const preview = text.trim().slice(0, 150);
    console.log(`\nFrame [${url.slice(0, 60)}]: ${preview}`);

    // Look for tabs
    const tabs = await f.locator('[role="tab"], button').evaluateAll(els =>
      els.filter(el => el.offsetParent !== null).map(el => ({
        text: (el.innerText || '').trim().slice(0, 30),
        role: el.getAttribute('role'),
        tag: el.tagName,
      }))
    ).catch(() => []);
    if (tabs.length) console.log('  Visible buttons/tabs:', JSON.stringify(tabs));
  }

  await browser.close();
}

main().catch(e => { console.error(e.message); process.exit(1); });
