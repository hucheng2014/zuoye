/**
 * bridge_lite.js — Non-interfering keepalive bridge.
 *
 * Same as bridge.js but does NOT cycle through response tabs.
 * Safe to run during form filling — only scrolls current content.
 *
 * Usage: node scripts/bridge_lite.js &
 */

const { chromium } = require('playwright');

const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';
const FALLBACK_CDP = 'http://127.0.0.1:9232';

async function connect() {
  for (const ep of [CDP, FALLBACK_CDP]) {
    try {
      const browser = await chromium.connectOverCDP(ep);
      console.log(`[bridge_lite] Connected to ${ep}`);
      return browser;
    } catch {}
  }
  throw new Error('[bridge_lite] No CDP endpoint available');
}

(async () => {
  const browser = await connect();
  const ctx = browser.contexts()[0];
  if (!ctx) throw new Error('[bridge_lite] No browser context');

  let page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  if (!page) throw new Error('[bridge_lite] No page found');

  console.log('[bridge_lite] Keepalive started (no tab switching). Kill when done.');

  let cycleCount = 0;

  while (true) {
    try {
      page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];

      // Handle "Task successfully submitted!" → Next Task
      const nextTaskBtn = page.locator('button').filter({ hasText: /^Next Task$/ }).filter({ visible: true }).first();
      if (await nextTaskBtn.count()) {
        console.log('[bridge_lite] "Task successfully submitted!" — clicking Next Task...');
        await nextTaskBtn.click({ timeout: 3000 });
        await page.waitForTimeout(4000);
      }

      // Handle "Task Overview" → Start
      const startBtn = page.locator('[aria-label="Task Overview"] button').filter({ hasText: /^Start$/ });
      if (await startBtn.count()) {
        console.log('[bridge_lite] "Task Overview" modal — clicking Start...');
        await startBtn.first().click({ timeout: 3000 });
        await page.waitForTimeout(1000);
      }

      // Keepalive: scroll only — NO tab switching
      const frame = page.frames().find(f => f.url().includes('task-editor'));
      if (frame) {
        await frame.evaluate(() => window.scrollTo(0, 50)).catch(() => {});
        await page.waitForTimeout(2000);
        await frame.evaluate(() => window.scrollTo(0, 0)).catch(() => {});
        await page.waitForTimeout(2000);
      } else {
        await page.evaluate(() => window.scrollTo(0, 50)).catch(() => {});
        await page.waitForTimeout(2000);
        await page.evaluate(() => window.scrollTo(0, 0)).catch(() => {});
        await page.waitForTimeout(2000);
      }

      cycleCount++;
      if (cycleCount % 10 === 0) {
        console.log(`[bridge_lite] Alive — cycle ${cycleCount}`);
      }

    } catch (e) {
      if (e.message.includes('Target page, context or browser has been closed')) {
        console.error('[bridge_lite] Browser closed. Exiting.');
        process.exit(0);
      }
      console.warn(`[bridge_lite] Cycle error (continuing): ${e.message}`);
      await new Promise(r => setTimeout(r, 2000));
    }
  }
})().catch(e => {
  console.error('[bridge_lite] Fatal:', e.message);
  process.exit(1);
});
