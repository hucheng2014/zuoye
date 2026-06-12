require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  const taskFrame = page.frames().find(f => f.url().includes('task-editor'));
  
  await taskFrame.locator('button[role="tab"]').filter({ hasText: 'Response A' }).first().click({ timeout: 3000 });
  await page.waitForTimeout(300);
  
  const checkboxes = await taskFrame.evaluate(() => {
    const labels = document.querySelectorAll('label');
    const result = [];
    labels.forEach(lbl => {
      const input = lbl.querySelector('input[type="checkbox"]');
      if (input && input.offsetWidth > 0) {
        result.push({ name: input.name, value: input.value, label: lbl.innerText?.trim().slice(0, 80) });
      }
    });
    return result;
  });
  console.log('All visible checkboxes:', JSON.stringify(checkboxes, null, 2));
  
  await browser.close();
})().catch(e => console.error(e));
