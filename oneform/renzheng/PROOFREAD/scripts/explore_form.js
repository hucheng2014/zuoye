require('./_timeout');
const { chromium } = require('playwright');

const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const context = browser.contexts()[0];
  const page = context.pages().find(p => p.url().includes('starshot')) || context.pages()[0];

  const taskFrame = page.frames().find(f => f.url().includes('task-editor'));
  if (!taskFrame) throw new Error('task-editor frame not found');

  // Step 1: Select formality = formal
  await taskFrame.locator('input[name="gYvBPJ6Eicgt7C_tID-o1"][value="formal"]').check({ force: true });
  await page.waitForTimeout(500);

  // Step 2: Select Q1 = has_grammar_errors
  await taskFrame.locator('input[name="XtKb-NGOhNUWjDl22pPtq"][value="has_grammar_errors"]').check({ force: true });
  await page.waitForTimeout(500);

  // Step 3: Click Response A tab, select has_edits
  const tabA = taskFrame.getByRole('tab', { name: 'Response A' });
  if (await tabA.count()) await tabA.first().click();
  await page.waitForTimeout(300);

  await taskFrame.locator('input[name="ijNnQjuyV_ir9qKX9Jt-7"][value="has_edits"]').check({ force: true });
  await page.waitForTimeout(1000);

  // Now capture ALL controls to see what conditional fields appeared
  const controls = await taskFrame.locator('input, textarea, select').evaluateAll(elements =>
    elements.map((el, i) => ({
      i,
      tag: el.tagName,
      type: el.getAttribute('type'),
      name: el.getAttribute('name'),
      value: el.value || '',
      checked: el.checked || false,
      visible: el.offsetParent !== null,
      label: el.closest('label')?.innerText?.trim()?.slice(0, 80) || '',
    }))
  );

  // Also get text to understand question labels
  const text = await taskFrame.locator('body').innerText();

  console.log(JSON.stringify({ controlCount: controls.length, controls, formText: text.slice(0, 5000) }, null, 2));

  await browser.close();
}

main().catch(e => { console.error(e.message); process.exit(1); });
