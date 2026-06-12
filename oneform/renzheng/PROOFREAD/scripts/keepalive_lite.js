/**
 * keepalive_lite.js — Lightweight keepalive for AI analysis phase.
 *
 * Unlike bridge.js, this does NOT switch Response tabs (won't interfere with fill_task.js).
 * It only scrolls the main page and clicks non-destructive elements to prevent
 * the 10-second inactivity threshold.
 *
 * Usage:
 *   node scripts/keepalive_lite.js
 *   # Kill it (SIGTERM/SIGINT) before running fill_task.js
 *
 * Interval: clicks/scrolls every ~6 seconds (well under the 10s inactivity cutoff).
 */

const { chromium } = require('playwright');

const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';
const FALLBACK_CDP = 'http://127.0.0.1:9232';

let running = true;
process.on('SIGINT', () => { running = false; });
process.on('SIGTERM', () => { running = false; });

async function connect() {
  for (const ep of [CDP, FALLBACK_CDP]) {
    try { return await chromium.connectOverCDP(ep); } catch {}
  }
  throw new Error('[keepalive_lite] No CDP endpoint available');
}

(async () => {
  const browser = await connect();
  const ctx = browser.contexts()[0];
  if (!ctx) throw new Error('[keepalive_lite] No browser context');

  let page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  if (!page) throw new Error('[keepalive_lite] No page found');

  console.log('[keepalive_lite] Started — scrolling main page every ~6s (no tab switching)');
  console.log('[keepalive_lite] Kill me (Ctrl+C or kill PID) before running fill_task.js');

  let cycle = 0;
  const startedAt = Date.now();

  while (running) {
    try {
      page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];

      const elapsed = Math.floor((Date.now() - startedAt) / 1000);
      const ts = new Date().toTimeString().slice(0, 8);

      // Alternate between scroll down and scroll up on the MAIN page (not iframe)
      if (cycle % 2 === 0) {
        await page.evaluate(() => window.scrollBy(0, 80));
      } else {
        await page.evaluate(() => window.scrollBy(0, -80));
      }

      // Every 4th cycle, do a mouse move to simulate human presence
      if (cycle % 4 === 0) {
        const x = 400 + Math.floor(Math.random() * 200);
        const y = 300 + Math.floor(Math.random() * 200);
        await page.mouse.move(x, y);
      }

      process.stdout.write(`\r${ts} [keepalive_lite] cycle=${cycle} elapsed=${elapsed}s  `);
      cycle++;

      await page.waitForTimeout(6000);
    } catch (e) {
      if (!running) break;
      if (e.message.includes('Target page, context or browser has been closed')) {
        console.log('\n[keepalive_lite] Browser closed. Exiting.');
        break;
      }
      console.warn(`\n[keepalive_lite] Error: ${e.message.substring(0, 80)}`);
      await new Promise(r => setTimeout(r, 3000));
    }
  }

  console.log('\n[keepalive_lite] Stopped gracefully.');
  await browser.close();
  process.exit(0);
})().catch(e => {
  console.error('[keepalive_lite] Fatal:', e.message);
  process.exit(1);
});
