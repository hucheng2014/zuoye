require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  const taskFrame = page.frames().find(f => f.url().includes('task-editor'));
  
  // Click C and A pairwise tab
  const tab = taskFrame.locator('button[role="tab"]').filter({ hasText: 'C and A' });
  await tab.first().click({ timeout: 3000 });
  await page.waitForTimeout(500);
  
  // Get visible radios
  const radios = await taskFrame.evaluate(() =>
    [...document.querySelectorAll('input[type="radio"]')]
      .filter(r => r.offsetWidth > 0)
      .map(r => ({name: r.name, value: r.value, checked: r.checked}))
  );
  console.log('C and A radios:', JSON.stringify(radios));
  
  // Click C=A
  const caRadio = taskFrame.locator('input[type="radio"][value="C=A"]').filter({ visible: true });
  if (await caRadio.count() > 0) {
    await caRadio.first().check({ force: true });
    console.log('Checked C=A');
  } else {
    console.log('C=A radio not found');
  }
  
  await browser.close();
})().catch(e => console.error(e));
