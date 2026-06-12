// Scroll-only keepalive — keeps timer running without switching tabs
const { chromium } = require('playwright');

const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

(async () => {
  let browser;
  for (const ep of [CDP, 'http://127.0.0.1:9232']) {
    try { browser = await chromium.connectOverCDP(ep); break; } catch {}
  }
  if (!browser) { console.error('[scroll] No CDP'); process.exit(1); }

  const ctx = browser.contexts()[0];
  console.log('[scroll] Scroll keepalive started');
  let cycle = 0;

  while (true) {
    try {
      const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
      const frame = page.frames().find(f => f.url().includes('task-editor'));
      if (frame) {
        await frame.evaluate(() => window.scrollTo(0, 150));
        await page.waitForTimeout(2500);
        await frame.evaluate(() => window.scrollTo(0, 0));
        await page.waitForTimeout(2500);
      } else {
        await page.evaluate(() => window.scrollTo(0, 100)).catch(() => {});
        await page.waitForTimeout(2500);
        await page.evaluate(() => window.scrollTo(0, 0)).catch(() => {});
        await page.waitForTimeout(2500);
      }
      cycle++;
      if (cycle % 12 === 0) console.log(`[scroll] cycle ${cycle}`);
    } catch (e) {
      console.log('[scroll] err:', e.message.substring(0, 50));
      await new Promise(r => setTimeout(r, 5000));
    }
  }
})();
