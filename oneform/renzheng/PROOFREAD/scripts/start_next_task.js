require('./_timeout');
// Navigate to next task then keepalive-cycle while extract_task.js runs separately.
// Usage: node start_next_task.js & (run in background, then run extract_task.js)
//
// NOTE: Prefer `node scripts/bridge.js &` for fully automated use — bridge.js runs
// indefinitely and auto-handles the submit dialog, eliminating the most critical gap.
// Use start_next_task.js only when you want a fixed 90-second keepalive window.

const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  let page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];

  // ── Auto-handle "Task successfully submitted!" dialog ────────────────────
  // Check whether the post-submit dialog is showing before trying Next Task.
  // This prevents a >10s gap if the script was launched after the dialog appeared.
  const submittedDialogBtn = page.locator('button').filter({ hasText: /^Next Task$/ }).filter({ visible: true }).first();
  if (await submittedDialogBtn.count()) {
    console.log('Auto-dismissing "Task successfully submitted!" dialog...');
    await submittedDialogBtn.click({ timeout: 3000 });
    await page.waitForTimeout(4000);  // SOP: wait ≥4s after Next Task
  } else {
    // Navigate to next task (legacy path: called before submit dialog appeared)
    const nextBtn = page.locator('button').filter({ hasText: 'Next Task' }).filter({ visible: true }).first();
    if (await nextBtn.count()) { await nextBtn.click(); await page.waitForTimeout(4000); }
  }

  // Dismiss Task Overview popup if present
  const startBtn = page.locator('[aria-label="Task Overview"] button').filter({ hasText: /^Start$/ });
  if (await startBtn.count()) { await startBtn.first().click(); await page.waitForTimeout(1000); }

  console.log('READY');

  // Keepalive cycling for 90 seconds
  const endAt = Date.now() + 90 * 1000;
  const tabNames = ['Response A', 'Response B', 'Response C'];
  let i = 0;
  while (Date.now() < endAt) {
    try {
      // Re-fetch page and frame each cycle in case navigation occurred
      page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
      const frame = page.frames().find(f => f.url().includes('task-editor'));
      if (frame) {
        const tb = frame.locator('button[role="tab"]').filter({ hasText: tabNames[i % tabNames.length] }).first();
        if (await tb.count()) await tb.click();
        await frame.evaluate(() => window.scrollTo(0, 200)); await page.waitForTimeout(3000);
        await frame.evaluate(() => window.scrollTo(0, 0));   await page.waitForTimeout(3000);
      } else {
        await page.evaluate(() => window.scrollTo(0, 100)).catch(() => {});
        await page.waitForTimeout(3000);
        await page.evaluate(() => window.scrollTo(0, 0)).catch(() => {});
        await page.waitForTimeout(3000);
      }
      i++;
    } catch(e) { break; }
  }
  console.log('KEEPALIVE_DONE');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
