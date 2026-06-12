require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  const taskFrame = page.frames().find(f => f.url().includes('task-editor'));
  
  const pairTabs = ['B and A', 'C and A', 'C and B'];
  
  for (const tab of pairTabs) {
    const t = taskFrame.locator('button[role="tab"]').filter({ hasText: tab });
    await t.first().click({ timeout: 3000 });
    await page.waitForTimeout(300);
    
    const radios = await taskFrame.evaluate(() =>
      [...document.querySelectorAll('input[type="radio"]')]
        .filter(r => r.offsetWidth > 0)
        .map(r => ({value: r.value, checked: r.checked}))
    );
    const groups = {};
    radios.forEach(r => {
      if (!groups[r.value.match(/[A-Z]/)?.[0]]) {}
    });
    
    const pairGroup = radios.filter(r => /^[A-C][=><!]+[A-C]/.test(r.value) || /^[A-C]>>/.test(r.value));
    const checkedPair = pairGroup.find(r => r.checked);
    console.log(`${tab}: ${checkedPair ? checkedPair.value : 'UNCHECKED'} (options: ${pairGroup.map(r=>r.value).join(',')})`);
  }
  
  await browser.close();
})().catch(e => console.error(e));
