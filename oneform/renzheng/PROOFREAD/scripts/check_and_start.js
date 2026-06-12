require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  
  await page.waitForTimeout(2000);
  
  // Check for Task Overview modal
  const overview = await page.$('[aria-label="Task Overview"]');
  if (overview) {
    console.log('Task Overview found');
    const startBtn = page.locator('[aria-label="Task Overview"] button').filter({ hasText: 'Start' });
    if (await startBtn.count() > 0) {
      await startBtn.click({ force: true });
      await page.waitForTimeout(2000);
      console.log('Clicked Start');
    }
  }
  
  const frames = page.frames();
  const tf = frames.find(f => f.url().includes('task-editor'));
  if (tf) {
    const state = await tf.evaluate(() => {
      const radios = document.querySelectorAll('input[type="radio"]');
      const controlNames = [...new Set([...radios].map(r => r.name))];
      return { radioCount: radios.length, controlNames, text: document.body.innerText.slice(0, 300) };
    });
    console.log('Task frame state:', JSON.stringify(state));
  } else {
    const buttons = await page.evaluate(() => [...document.querySelectorAll('button')].filter(b=>b.offsetWidth>0).map(b=>b.innerText?.trim()));
    const dialogs = await page.evaluate(() => [...document.querySelectorAll('[role="dialog"]')].filter(d=>d.offsetWidth>0).map(d=>({text:d.innerText?.slice(0,200)})));
    console.log('No task frame. Buttons:', JSON.stringify(buttons));
    console.log('Dialogs:', JSON.stringify(dialogs));
  }
  
  await browser.close();
})().catch(e => console.error(e));
