require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  
  const frames = page.frames();
  const taskFrame = frames.find(f => f.url().includes('task-editor'));
  if (!taskFrame) { console.log('No task-editor frame'); await browser.close(); return; }
  
  // Click each pairwise tab and check available radio values
  const pairTabs = ['A and B', 'A and C', 'B and C', 'B and A', 'C and A', 'C and B'];
  
  for (const tabName of pairTabs) {
    const tab = taskFrame.locator('button[role="tab"]').filter({ hasText: tabName });
    if (await tab.count() === 0) continue;
    await tab.first().click({ timeout: 3000 });
    await page.waitForTimeout(500);
    
    const radios = await taskFrame.evaluate(() => {
      return [...document.querySelectorAll('input[type="radio"]')]
        .filter(r => r.offsetWidth > 0)
        .map(r => ({ name: r.name, value: r.value, checked: r.checked }));
    });
    console.log(`Tab "${tabName}":`, JSON.stringify(radios));
  }
  
  await browser.close();
})().catch(e => console.error(e));
