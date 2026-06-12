require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  const taskFrame = page.frames().find(f => f.url().includes('task-editor'));
  
  // Set up: has_grammar_errors, Response A, has_edits
  await taskFrame.locator('input[type="radio"][value="has_grammar_errors"]').filter({ visible: true }).first().check({ force: true });
  await page.waitForTimeout(200);
  await taskFrame.locator('button[role="tab"]').filter({ hasText: 'Response A' }).first().click({ timeout: 3000 });
  await page.waitForTimeout(300);
  await taskFrame.locator('input[type="radio"][value="has_edits"]').filter({ visible: true }).first().check({ force: true });
  await page.waitForTimeout(300);
  await taskFrame.locator('input[type="radio"][value="all_unnecessary"]').filter({ visible: true }).first().check({ force: true });
  await page.waitForTimeout(500);
  
  const radios = await taskFrame.evaluate(() => 
    [...document.querySelectorAll('input[type="radio"]')].filter(r=>r.offsetWidth>0).map(r=>({name:r.name,value:r.value,checked:r.checked}))
  );
  console.log('Radios after all_unnecessary:', JSON.stringify(radios));
  
  const checkboxes = await taskFrame.evaluate(() =>
    [...document.querySelectorAll('input[type="checkbox"]')].filter(r=>r.offsetWidth>0).map(r=>({name:r.name,value:r.value}))
  );
  console.log('Checkboxes:', JSON.stringify(checkboxes));
  
  await browser.close();
})().catch(e => console.error(e));
