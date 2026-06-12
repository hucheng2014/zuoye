require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  
  const frames = page.frames();
  const taskFrame = frames.find(f => f.url().includes('task-editor'));
  
  // Click Response A tab and see full state
  await taskFrame.locator('button[role="tab"]').filter({ hasText: 'Response A' }).first().click({ timeout: 3000 });
  await page.waitForTimeout(500);
  
  // Get ALL visible form elements with labels
  const formState = await taskFrame.evaluate(() => {
    const result = [];
    const labels = document.querySelectorAll('label');
    labels.forEach(lbl => {
      const input = lbl.querySelector('input');
      if (!input) {
        // Find associated input
        const forId = lbl.getAttribute('for');
        const inp = forId ? document.getElementById(forId) : null;
        if (inp && inp.offsetWidth > 0) {
          result.push({
            type: inp.type,
            name: inp.name,
            value: inp.value,
            checked: inp.checked,
            label: lbl.innerText?.trim(),
            visible: inp.offsetWidth > 0
          });
        }
      } else if (input.offsetWidth > 0) {
        result.push({
          type: input.type,
          name: input.name,
          value: input.value,
          checked: input.checked,
          label: lbl.innerText?.trim(),
          visible: true
        });
      }
    });
    return result;
  });
  console.log('Response A form state:');
  formState.forEach(f => console.log(`  [${f.checked ? 'X' : ' '}] ${f.type}[${f.value}] (${f.name.slice(0,10)}) "${f.label}"`));
  
  // Get the full page text for context
  const text = await taskFrame.evaluate(() => {
    // get just the visible text in the active response tab area
    return document.body.innerText;
  });
  // Find relevant section
  const lines = text.split('\n').filter(l => l.trim());
  console.log('\nPage text lines:');
  lines.forEach((l, i) => console.log(`  ${i}: ${l}`));
  
  await browser.close();
})().catch(e => console.error(e));
