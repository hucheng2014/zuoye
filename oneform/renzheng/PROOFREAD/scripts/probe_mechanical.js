require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  
  const frames = page.frames();
  const taskFrame = frames.find(f => f.url().includes('task-editor'));
  
  // Click Response C tab
  await taskFrame.locator('button[role="tab"]').filter({ hasText: 'Response C' }).first().click({ timeout: 3000 });
  await page.waitForTimeout(500);
  
  // Set has_grammar_errors first (should already be set)
  await taskFrame.locator('input[type="radio"][value="has_grammar_errors"]').filter({ visible: true }).first().check({ force: true });
  await page.waitForTimeout(300);
  
  // Set has_edits
  await taskFrame.locator('input[type="radio"][value="has_edits"]').filter({ visible: true }).first().check({ force: true });
  await page.waitForTimeout(300);
  
  // Set some_unnecessary
  await taskFrame.locator('input[type="radio"][value="some_unnecessary"]').filter({ visible: true }).first().check({ force: true });
  await page.waitForTimeout(300);
  
  // Set mechanical
  await taskFrame.locator('input[type="radio"][value="mechanical"]').filter({ visible: true }).first().check({ force: true });
  await page.waitForTimeout(500);
  
  // Get all visible checkboxes
  const checkboxes = await taskFrame.evaluate(() => {
    const labels = document.querySelectorAll('label');
    const result = [];
    labels.forEach(lbl => {
      const input = lbl.querySelector('input[type="checkbox"]');
      if (input && input.offsetWidth > 0) {
        result.push({ value: input.value, name: input.name, label: lbl.innerText?.trim() });
      }
    });
    return result;
  });
  console.log('Checkboxes after mechanical:', JSON.stringify(checkboxes, null, 2));
  
  await browser.close();
})().catch(e => console.error(e));
