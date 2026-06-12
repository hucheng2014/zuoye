require('./_timeout');
const { chromium } = require('playwright');
const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  const frame = page.frames().find(f => f.url().includes('task-editor'));

  const dialog = page.locator('div[role="dialog"][aria-label="Task Overview"]');
  if (await dialog.count() > 0) {
    const closeBtn = dialog.locator('button:has-text("Close")');
    if (await closeBtn.count() > 0) {
      await closeBtn.first().click({ timeout: 2000 });
    } else {
      await page.keyboard.press('Escape');
    }
    await page.waitForTimeout(500);
  }

  for (const tabName of ['Response A', 'Response B', 'Response C']) {
    console.log(`\n=== ${tabName} ===`);
    const tab = frame.locator('button[role="tab"]').filter({ hasText: tabName });
    await tab.first().click({ timeout: 3000 });
    await page.waitForTimeout(500);

    // Get visible checked and unchecked radios
    const visible = await frame.locator('input[type="radio"]').evaluateAll(els =>
      els.filter(el => el.offsetParent !== null).map(el => ({
        name: el.name, value: el.value, checked: el.checked,
        label: (el.closest('label')?.innerText || '').trim().slice(0, 80),
      }))
    );

    // Show unchecked required groups (groups where nothing is checked)
    const groups = {};
    for (const v of visible) {
      if (!groups[v.name]) groups[v.name] = { checked: false, values: [] };
      groups[v.name].values.push(v.value);
      if (v.checked) groups[v.name].checked = true;
    }

    const uncheckedGroups = Object.entries(groups).filter(([_, g]) => !g.checked);
    if (uncheckedGroups.length) {
      console.log('UNCHECKED GROUPS:');
      for (const [name, g] of uncheckedGroups) {
        console.log(`  ${name}: ${JSON.stringify(g.values)}`);
      }
    } else {
      console.log('All visible radio groups have a selection');
    }

    // Check for visible error messages
    const errors = await frame.locator('[class*="error"], [class*="required"]').evaluateAll(els =>
      els.filter(el => el.offsetParent !== null).map(el => (el.innerText || '').trim().slice(0, 100)).filter(t => t)
    );
    if (errors.length) console.log('ERRORS:', errors);
  }

  // Check completion after visiting all tabs
  const formText = await frame.locator('body').innerText({ timeout: 2000 }).catch(() => '');
  const complete = formText.match(/(\d+\/\d+) Complete/g);
  console.log('\nFinal completion:', complete);

  await browser.close();
}

main().catch(e => { console.error(e.message); process.exit(1); });
