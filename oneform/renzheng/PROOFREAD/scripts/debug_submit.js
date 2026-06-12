require('./_timeout');
const { chromium } = require('playwright');
const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  const frame = page.frames().find(f => f.url().includes('task-editor'));

  // Check all checked fields
  const checked = await frame.locator('input:checked').evaluateAll(els =>
    els.map(el => ({ name: el.name, value: el.value, type: el.type }))
  );
  console.log('Checked inputs:', JSON.stringify(checked, null, 2));

  // Check textarea value
  const textareas = await frame.locator('textarea').evaluateAll(els =>
    els.map(el => ({ name: el.name, value: (el.value || '').slice(0, 100) }))
  );
  console.log('Textareas:', JSON.stringify(textareas, null, 2));

  // Look for error messages or validation text
  const errorTexts = await frame.locator('[class*="error"], [class*="warning"], [class*="invalid"], [class*="required"]').evaluateAll(els =>
    els.map(el => (el.innerText || '').trim().slice(0, 100)).filter(t => t)
  );
  console.log('Errors:', errorTexts);

  // Check "0/3 Complete" status
  const formText = await frame.locator('body').innerText({ timeout: 2000 }).catch(() => '');
  const completeMatch = formText.match(/(\d+\/\d+) Complete/g);
  console.log('Completion status:', completeMatch);

  // Try clicking inner Submit
  const innerSubmit = frame.locator('button').filter({ hasText: 'Submit' }).first();
  if (await innerSubmit.count()) {
    console.log('Inner Submit button found, clicking...');
    await innerSubmit.click({ timeout: 3000 });
    await page.waitForTimeout(1500);
  }

  // Check for popup/modal
  const allButtons = await page.locator('button').evaluateAll(els =>
    els.filter(el => el.offsetParent !== null).map(el => ({
      text: (el.innerText || '').trim().slice(0, 50),
      ariaLabel: el.getAttribute('aria-label') || '',
    }))
  );
  console.log('Visible page buttons:', JSON.stringify(allButtons, null, 2));

  // Get page body text
  const bodyText = await page.locator('body').innerText({ timeout: 2000 }).catch(() => '');
  console.log('Body preview:', bodyText.slice(0, 500));

  await browser.close();
}

main().catch(e => { console.error(e.message); process.exit(1); });
