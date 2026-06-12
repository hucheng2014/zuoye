require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  
  // Click "Next Task" button
  const nextBtn = await page.locator('button', { hasText: 'Next Task' }).filter({ visible: true }).first();
  if (nextBtn) {
    console.log('Clicking Next Task...');
    await nextBtn.click({ force: true });
    await page.waitForTimeout(4000);  // wait for page load due to network delay
  } else {
    console.log('No Next Task button found');
    await browser.close();
    return;
  }

  // Check for Task Overview modal
  await page.waitForTimeout(2000);
  const overview = await page.$('[aria-label="Task Overview"]');
  if (overview) {
    console.log('Task Overview modal found, clicking Start...');
    const startBtn = await page.locator('[aria-label="Task Overview"] button', { hasText: 'Start' });
    if (startBtn) {
      await startBtn.click({ force: true });
      await page.waitForTimeout(2000);
    }
  }
  
  // Check new task frame state
  const frames = page.frames();
  const taskFrame = frames.find(f => f.url().includes('task-editor'));
  if (taskFrame) {
    const state = await taskFrame.evaluate(() => {
      const radios = document.querySelectorAll('input[type="radio"]');
      const controlNames = [...new Set([...radios].map(r => r.name))];
      const text = document.body.innerText.slice(0, 500);
      return { radioCount: radios.length, controlNames, text };
    });
    console.log('New task frame state:', JSON.stringify(state, null, 2));
  } else {
    console.log('No task-editor frame after navigation');
  }
  
  await browser.close();
})().catch(e => console.error(e));
