require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  
  const frames = page.frames();
  const taskFrame = frames.find(f => f.url().includes('task-editor'));
  if (!taskFrame) { console.log('No task-editor frame'); await browser.close(); return; }
  
  // Click Response C tab
  const tabC = taskFrame.locator('button[role="tab"]').filter({ hasText: 'Response C' });
  await tabC.first().click({ timeout: 3000 });
  await page.waitForTimeout(500);
  
  // Get all visible radio options
  const radios = await taskFrame.evaluate(() => {
    return [...document.querySelectorAll('input[type="radio"]')]
      .filter(r => r.offsetWidth > 0)
      .map(r => ({ name: r.name, value: r.value, checked: r.checked }));
  });
  console.log('Response C radio options:', JSON.stringify(radios, null, 2));
  
  // Also get text to understand labels
  const text = await taskFrame.evaluate(() => document.body.innerText.slice(0, 2000));
  console.log('Page text:', text);
  
  await browser.close();
})().catch(e => console.error(e));
