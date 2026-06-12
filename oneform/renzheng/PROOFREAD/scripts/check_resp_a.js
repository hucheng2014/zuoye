require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  const taskFrame = page.frames().find(f => f.url().includes('task-editor'));
  
  await taskFrame.locator('button[role="tab"]').filter({ hasText: 'Response A' }).first().click({ timeout: 3000 });
  await page.waitForTimeout(500);
  
  const state = await taskFrame.evaluate(() => {
    const labels = document.querySelectorAll('label');
    const result = [];
    labels.forEach(lbl => {
      const input = lbl.querySelector('input');
      if (input && input.offsetWidth > 0) {
        result.push({ type: input.type, value: input.value, checked: input.checked, label: lbl.innerText?.trim().slice(0, 60) });
      }
    });
    return result;
  });
  state.filter(s => s.checked || s.type === 'radio').forEach(s => 
    console.log(`[${s.checked?'X':' '}] ${s.type}[${s.value}] "${s.label}"`)
  );
  
  await browser.close();
})().catch(e => console.error(e));
