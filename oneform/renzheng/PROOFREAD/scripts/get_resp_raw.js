require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  const taskFrame = page.frames().find(f => f.url().includes('task-editor'));
  
  for (const tab of ['Response A', 'Response B', 'Response C']) {
    await taskFrame.locator('button[role="tab"]').filter({ hasText: tab }).first().click({ timeout: 3000 });
    await page.waitForTimeout(600);
    
    // Read the task frame's current visible input vs response diff
    const diffText = await taskFrame.evaluate(() => {
      // Get all the rendered diff elements in the current visible panel
      const addedSpans = document.querySelectorAll('span.added-text');
      const removedSpans = document.querySelectorAll('span.removed-text');
      const added = [...addedSpans].filter(s => s.offsetWidth > 0).map(s => s.innerText);
      const removed = [...removedSpans].filter(s => s.offsetWidth > 0).map(s => s.innerText);
      return { added, removed };
    });
    console.log(`${tab}:`, JSON.stringify(diffText));
  }
  
  await browser.close();
})().catch(e => console.error(e));
