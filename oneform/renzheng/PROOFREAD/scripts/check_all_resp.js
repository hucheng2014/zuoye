require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  const taskFrame = page.frames().find(f => f.url().includes('task-editor'));
  
  for (const tab of ['Response A', 'Response B', 'Response C']) {
    await taskFrame.locator('button[role="tab"]').filter({ hasText: tab }).first().click({ timeout: 3000 });
    await page.waitForTimeout(300);
    
    const checked = await taskFrame.evaluate(() =>
      [...document.querySelectorAll('input[type="radio"]:checked, input[type="checkbox"]:checked')]
        .filter(r => r.offsetWidth > 0)
        .map(r => r.value)
    );
    console.log(`${tab}: ${JSON.stringify(checked)}`);
  }
  
  await browser.close();
})().catch(e => console.error(e));
