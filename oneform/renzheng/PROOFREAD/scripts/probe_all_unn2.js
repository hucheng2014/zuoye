require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  const taskFrame = page.frames().find(f => f.url().includes('task-editor'));
  
  await taskFrame.locator('button[role="tab"]').filter({ hasText: 'Response A' }).first().click({ timeout: 3000 });
  await page.waitForTimeout(300);
  
  // Get full text to understand what questions appear
  const text = await taskFrame.evaluate(() => document.body.innerText);
  const lines = text.split('\n').filter(l => l.trim()).slice(0, 80);
  lines.forEach((l, i) => console.log(`${i}: ${l}`));
  
  await browser.close();
})().catch(e => console.error(e));
