require('./_timeout');
const { chromium } = require('playwright');
const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  const frame = page.frames().find(f => f.url().includes('task-editor'));

  // Check ALL checked inputs
  const checked = await frame.locator('input:checked').evaluateAll(els =>
    els.map(el => ({ name: el.name, value: el.value, type: el.type, visible: el.offsetParent !== null }))
  );
  console.log('Checked inputs:', checked.length);
  for (const c of checked) console.log(`  ${c.value} (visible: ${c.visible})`);

  // Check textarea
  const ta = await frame.locator('textarea').first().inputValue().catch(() => '');
  console.log('\nObservation filled:', ta.length > 0 ? 'YES (' + ta.length + ' chars)' : 'NO');

  // Check completion status
  const formText = await frame.locator('body').innerText({ timeout: 2000 }).catch(() => '');
  const complete = formText.match(/(\d+\/\d+) Complete/g);
  console.log('Completion:', complete);

  // Check derived scores
  for (const f of page.frames()) {
    const t = await f.locator('body').innerText({ timeout: 500 }).catch(() => '');
    if (t.includes('Grading for Response') && t.includes('Correctness')) {
      console.log('\nScore:', t.trim().replace(/\n/g, ' | '));
    }
  }

  // Check for errors
  const errors = await frame.locator('[class*="error"], [class*="invalid"]').evaluateAll(els =>
    els.filter(el => el.offsetParent !== null).map(el => (el.innerText || '').trim().slice(0, 80)).filter(t => t)
  );
  if (errors.length) console.log('\nERRORS:', errors);
  else console.log('\nNo validation errors found');

  // Take verification screenshots
  for (const tabName of ['Response A', 'Response B', 'Response C']) {
    const tab = frame.locator('button[role="tab"]').filter({ hasText: tabName });
    if (await tab.count()) {
      await tab.first().click({ timeout: 3000 });
      await page.waitForTimeout(300);
    }
  }
  await page.screenshot({ path: 'PROOFREAD/runs/task-002-verify.png' });

  await browser.close();
}

main().catch(e => { console.error(e.message); process.exit(1); });
