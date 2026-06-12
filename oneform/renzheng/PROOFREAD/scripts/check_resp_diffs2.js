require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  const taskFrame = page.frames().find(f => f.url().includes('task-editor'));
  
  for (const tab of ['Response A', 'Response B', 'Response C']) {
    await taskFrame.locator('button[role="tab"]').filter({ hasText: tab }).first().click({ timeout: 3000 });
    await page.waitForTimeout(800);
    
    // Get all srcdoc frames and find the ones with content
    const srcdocFrames = page.frames().filter(f => f.url() === 'about:srcdoc');
    const results = [];
    for (const f of srcdocFrames) {
      const data = await f.evaluate(() => {
        const raw = document.querySelector('#raw-content');
        const box = document.querySelector('#raw-content')?.getBoundingClientRect();
        return raw ? { text: raw.textContent?.trim().slice(-100), visible: box && box.width > 0, top: box?.top } : null;
      }).catch(() => null);
      if (data && data.text) results.push(data);
    }
    
    // Sort by position (top) and get the most recently focused one
    const sorted = results.sort((a, b) => Math.abs(a.top - 400) - Math.abs(b.top - 400));
    console.log(`\n${tab} (${results.length} diffs):`);
    console.log('  Last 100 chars of first:', sorted[0]?.text);
  }
  
  await browser.close();
})().catch(e => console.error(e));
