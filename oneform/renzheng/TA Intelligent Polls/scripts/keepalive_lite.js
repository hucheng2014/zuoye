/**
 * keepalive_lite.js — Lightweight keepalive for AI analysis phase.
 *                     V2: Visible main page actions + jittered timing.
 *
 * What you'll see on noVNC:
 *   - Mouse cursor moving across the page
 *   - Main page scrolling up/down slightly
 *   - Occasional click on the timer element
 *
 * Usage:
 *   nohup node scripts/keepalive_lite.js > /dev/null 2>&1 &
 *   # Kill it (SIGTERM/SIGINT) before running fill_task.js
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

  console.log('[keepalive_lite] Started — visible main page actions every 5-7s');
  console.log('[keepalive_lite] Kill me (Ctrl+C or kill PID) before running fill_task.js');

  let cycle = 0;
  const startedAt = Date.now();

  while (running) {
    try {
      page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];

      const elapsed = Math.floor((Date.now() - startedAt) / 1000);
      const ts = new Date().toTimeString().slice(0, 8);

      // 1. Move mouse visibly across the main page
      const mx = 200 + Math.floor(Math.random() * 800);
      const my = 100 + Math.floor(Math.random() * 500);
      await page.mouse.move(mx, my);

      // 2. Scroll main page (visible on noVNC)
      const scrollDist = 60 + Math.floor(Math.random() * 40);
      if (cycle % 2 === 0) {
        await page.evaluate(d => window.scrollBy(0, d), scrollDist);
      } else {
        await page.evaluate(d => window.scrollBy(0, -d), scrollDist);
      }

      // 3. Every 6th cycle, click the timer (non-destructive, registers as user click)
      if (cycle % 6 === 0) {
        const timerEl = page.locator('#timer');
        if (await timerEl.count() > 0) {
          await timerEl.click({ timeout: 2000 }).catch(() => {});
        }
      }

      process.stdout.write(`\r${ts} [keepalive_lite] cycle=${cycle} elapsed=${elapsed}s  `);
      cycle++;

      // Jittered interval: 5-7s
      const jitter = 5000 + Math.floor(Math.random() * 2000);
      await page.waitForTimeout(jitter);
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
