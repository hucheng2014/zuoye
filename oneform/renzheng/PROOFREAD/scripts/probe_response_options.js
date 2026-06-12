require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  
  const frames = page.frames();
  const taskFrame = frames.find(f => f.url().includes('task-editor'));
  if (!taskFrame) { console.log('No task-editor frame'); await browser.close(); return; }
  
  // First set q1 = has_grammar_errors
  await taskFrame.locator('input[type="radio"][value="has_grammar_errors"]').check({ force: true });
  await page.waitForTimeout(300);
  
  // Click Response A tab
  await taskFrame.locator('button[role="tab"]').filter({ hasText: 'Response A' }).first().click({ timeout: 3000 });
  await page.waitForTimeout(500);
  
  // Check has_edits
  await taskFrame.locator('input[type="radio"][value="has_edits"]').filter({ visible: true }).first().check({ force: true });
  await page.waitForTimeout(500);
  
  // Get available radios
  let radios = await taskFrame.evaluate(() => {
    return [...document.querySelectorAll('input[type="radio"]')]
      .filter(r => r.offsetWidth > 0)
      .map(r => ({ name: r.name, value: r.value }));
  });
  console.log('After has_edits:', JSON.stringify(radios));
  
  // Now check some_unnecessary
  if (radios.find(r => r.value === 'some_unnecessary')) {
    await taskFrame.locator('input[type="radio"][value="some_unnecessary"]').filter({ visible: true }).first().check({ force: true });
    await page.waitForTimeout(500);
    
    let newRadios = await taskFrame.evaluate(() => {
      return [...document.querySelectorAll('input[type="radio"]')]
        .filter(r => r.offsetWidth > 0)
        .map(r => ({ name: r.name, value: r.value }));
    });
    console.log('After some_unnecessary:', JSON.stringify(newRadios));
    
    // Check checkboxes
    const checkboxes = await taskFrame.evaluate(() => {
      return [...document.querySelectorAll('input[type="checkbox"]')]
        .filter(r => r.offsetWidth > 0)
        .map(r => ({ name: r.name, value: r.value }));
    });
    console.log('Checkboxes:', JSON.stringify(checkboxes));
  }
  
  await browser.close();
})().catch(e => console.error(e));
