require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  
  // Submission success criterion: Next Task button appears
  let nextTaskVisible = false;
  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    const nextBtn = page.locator('button').filter({ hasText: /^Next Task$/ }).filter({ visible: true }).first();
    if (await nextBtn.count().then(c => c > 0).catch(() => false)) {
      nextTaskVisible = true;
      break;
    }
    await page.waitForTimeout(1000);
  }

  // Check state snapshot
  const state = await page.evaluate(() => {
    const dialogs = document.querySelectorAll('[role="dialog"]');
    const dlgInfo = [...dialogs].map(d => ({ text: d.innerText?.slice(0, 300), visible: d.offsetWidth > 0 }));
    const visibleBtns = [...document.querySelectorAll('button')].filter(b => b.offsetWidth > 0).map(b => b.innerText?.trim());
    return { dialogs: dlgInfo, buttons: visibleBtns, url: window.location.href };
  });
  console.log('NextTaskVisible:', nextTaskVisible);
  console.log('State after wait:', JSON.stringify(state, null, 2));
  
  // Check for Task Overview modal
  const frames = page.frames();
  const taskFrame = frames.find(f => f.url().includes('task-editor'));
  if (taskFrame) {
    const frameState = await taskFrame.evaluate(() => {
      const radios = document.querySelectorAll('input[type="radio"]');
      const controlNames = [...new Set([...radios].map(r => r.name))];
      return { radioCount: radios.length, controlNames };
    });
    console.log('Task frame state:', JSON.stringify(frameState));
  }
  
  await browser.close();
})().catch(e => console.error(e));
