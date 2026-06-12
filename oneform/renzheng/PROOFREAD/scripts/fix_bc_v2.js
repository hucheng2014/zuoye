require('./_timeout');
const { chromium } = require('playwright');
const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  const frame = page.frames().find(f => f.url().includes('task-editor'));
  if (!frame) throw new Error('No task-editor frame');

  for (const tabName of ['Response B', 'Response C']) {
    console.log(`\n=== ${tabName} ===`);

    // Click tab using button text
    const tabBtn = frame.locator(`button[role="tab"]`).filter({ hasText: tabName });
    const tabCount = await tabBtn.count();
    console.log(`Tab button count: ${tabCount}`);
    if (tabCount) {
      await tabBtn.first().click({ timeout: 5000 });
      await page.waitForTimeout(800);
      console.log('Tab clicked');
    }

    // Check if all_necessary is selected; if not, select it
    const visRadios = await frame.locator('input[type="radio"]').evaluateAll(els =>
      els.filter(el => el.offsetParent !== null).map(el => ({
        name: el.name, value: el.value, checked: el.checked
      }))
    );
    console.log('Visible radios:', JSON.stringify(visRadios.filter(r => r.checked)));

    // Toggle: first select some_unnecessary, wait, then back to all_necessary
    const someUnnec = frame.locator('input[type="radio"][value="some_unnecessary"]');
    for (let i = 0; i < await someUnnec.count(); i++) {
      if (await someUnnec.nth(i).isVisible().catch(() => false)) {
        await someUnnec.nth(i).check({ force: true });
        console.log('Toggled to some_unnecessary');
        await page.waitForTimeout(500);
        break;
      }
    }

    const allNec = frame.locator('input[type="radio"][value="all_necessary"]');
    for (let i = 0; i < await allNec.count(); i++) {
      if (await allNec.nth(i).isVisible().catch(() => false)) {
        await allNec.nth(i).check({ force: true });
        console.log('Back to all_necessary');
        await page.waitForTimeout(800);
        break;
      }
    }

    // Now check all_correct
    const allCorr = frame.locator('input[type="radio"][value="all_correct"]');
    const corrCount = await allCorr.count();
    console.log(`all_correct radio count: ${corrCount}`);
    for (let i = 0; i < corrCount; i++) {
      if (await allCorr.nth(i).isVisible().catch(() => false)) {
        await allCorr.nth(i).check({ force: true });
        console.log(`Checked all_correct (index ${i})`);
        await page.waitForTimeout(300);
        break;
      }
    }
  }

  // Final verification
  console.log('\n=== FINAL VERIFICATION ===');
  const allChecked = await frame.locator('input:checked').evaluateAll(els =>
    els.map(el => ({ name: el.name, value: el.value }))
  );
  console.log('All checked:', JSON.stringify(allChecked, null, 2));

  // Check derived scores from srcdoc frames
  for (const f of page.frames()) {
    const t = await f.locator('body').innerText({ timeout: 500 }).catch(() => '');
    if (t.includes('Grading for Response') && t.includes('Correctness')) {
      console.log('Score frame:', t.trim().slice(0, 200));
    }
  }

  await browser.close();
}

main().catch(e => { console.error(e.message); process.exit(1); });
