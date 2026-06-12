require('./_timeout');
const { chromium } = require('playwright');
const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  const frame = page.frames().find(f => f.url().includes('task-editor'));

  // Set formality and Q1
  await frame.locator('input[value="other"]').first().check({ force: true });
  await page.waitForTimeout(300);
  await frame.locator('input[value="has_grammar_errors"]').first().check({ force: true });
  await page.waitForTimeout(300);

  // Click Response A tab
  const tabA = frame.locator('button[role="tab"]').filter({ hasText: 'Response A' });
  await tabA.first().click();
  await page.waitForTimeout(300);

  // Set has_edits
  const hasEdits = frame.locator('input[value="has_edits"]');
  for (let i = 0; i < await hasEdits.count(); i++) {
    if (await hasEdits.nth(i).isVisible().catch(() => false)) {
      await hasEdits.nth(i).check({ force: true });
      break;
    }
  }
  await page.waitForTimeout(500);

  // Set some_unnecessary
  const someUnnec = frame.locator('input[value="some_unnecessary"]');
  for (let i = 0; i < await someUnnec.count(); i++) {
    if (await someUnnec.nth(i).isVisible().catch(() => false)) {
      await someUnnec.nth(i).check({ force: true });
      break;
    }
  }
  await page.waitForTimeout(800);

  // Now capture ALL visible controls to see what appeared
  const controls = await frame.locator('input, textarea, select').evaluateAll(els =>
    els.filter(el => el.offsetParent !== null).map((el, i) => ({
      i, tag: el.tagName, type: el.getAttribute('type'),
      name: el.getAttribute('name'), value: el.value || '',
      checked: el.checked || false,
      label: (el.closest('label')?.innerText || '').trim().slice(0, 100),
    }))
  );

  console.log(JSON.stringify(controls, null, 2));

  await browser.close();
}

main().catch(e => { console.error(e.message); process.exit(1); });
