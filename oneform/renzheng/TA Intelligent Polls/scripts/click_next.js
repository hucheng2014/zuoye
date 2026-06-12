/**
 * click_next.js — Click "Next Task" button and dismiss the Task Overview dialog.
 *
 * Used after submission to advance to the next task.
 *
 * Usage:
 *   node scripts/click_next.js
 */

require('./_timeout');
const { chromium } = require('playwright');

const CDP_ENDPOINTS = [
  process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233',
  'http://127.0.0.1:9232',
];

(async () => {
  let browser;
  for (const ep of CDP_ENDPOINTS) {
    try { browser = await chromium.connectOverCDP(ep); break; } catch {}
  }
  if (!browser) throw new Error('No CDP endpoint available');

  try {
    const ctx = browser.contexts()[0];
    const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];

    // Click Next Task button
    const nextBtn = page.locator('button').filter({ hasText: /^Next Task$/ }).filter({ visible: true }).first();
    if (await nextBtn.count() > 0) {
      console.log('Clicking Next Task...');
      await nextBtn.click({ timeout: 5000 });
      await page.waitForTimeout(4000);
    } else {
      console.log('No Next Task button found.');
    }

    // Dismiss Task Overview dialog if it appears
    const dialog = page.locator('[aria-label="Task Overview"]');
    if (await dialog.count() > 0) {
      const startBtn = dialog.locator('button:has-text("Start")');
      if (await startBtn.count() > 0) {
        console.log('Clicking Start to dismiss Task Overview...');
        await startBtn.first().click({ timeout: 3000 });
        await page.waitForTimeout(1000);
      }
    }

    console.log('Next task ready.');
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e.message); process.exit(1); });
