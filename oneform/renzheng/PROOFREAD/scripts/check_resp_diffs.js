require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  const taskFrame = page.frames().find(f => f.url().includes('task-editor'));
  
  for (const tab of ['Response A', 'Response B', 'Response C']) {
    await taskFrame.locator('button[role="tab"]').filter({ hasText: tab }).first().click({ timeout: 3000 });
    await page.waitForTimeout(500);
    
    // Get the srcdoc frames that are currently active (only visible ones)
    const srcdocFrames = page.frames().filter(f => f.url() === 'about:srcdoc');
    // The currently active response diff frame should be the one visible
    for (const f of srcdocFrames) {
      const raw = await f.evaluate(() => {
        const el = document.querySelector('#raw-content');
        return el ? el.textContent?.trim() : null;
      }).catch(() => null);
      
      if (raw && raw.includes('先')) {  // check a known part of the input
        console.log(`\n${tab} diff: ${raw.slice(0, 200)}`);
        break;
      }
    }
  }
  
  await browser.close();
})().catch(e => console.error(e));
