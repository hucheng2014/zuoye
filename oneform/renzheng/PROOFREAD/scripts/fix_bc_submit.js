require('./_timeout');
const { chromium } = require('playwright');
const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  const frame = page.frames().find(f => f.url().includes('task-editor'));

  for (const tabName of ['Response B', 'Response C']) {
    console.log(`--- ${tabName} ---`);

    // Click tab
    const tab = frame.getByRole('tab', { name: tabName, exact: true });
    await tab.first().click();
    await page.waitForTimeout(600);

    // Re-click all_necessary to trigger conditional re-render
    const allNec = frame.locator('input[type="radio"][value="all_necessary"]');
    const necCount = await allNec.count();
    for (let i = 0; i < necCount; i++) {
      const el = allNec.nth(i);
      if (await el.isVisible().catch(() => false)) {
        // Uncheck by clicking something else first, then re-check
        const someUnnec = frame.locator('input[type="radio"][value="some_unnecessary"]');
        for (let j = 0; j < await someUnnec.count(); j++) {
          if (await someUnnec.nth(j).isVisible().catch(() => false)) {
            await someUnnec.nth(j).check({ force: true });
            break;
          }
        }
        await page.waitForTimeout(400);
        // Now re-check all_necessary
        await el.check({ force: true });
        await page.waitForTimeout(600);
        console.log(`Re-triggered all_necessary for ${tabName}`);
        break;
      }
    }

    // Now find and check all_correct
    const allCorr = frame.locator('input[type="radio"][value="all_correct"]');
    const corrCount = await allCorr.count();
    let found = false;
    for (let i = 0; i < corrCount; i++) {
      const el = allCorr.nth(i);
      if (await el.isVisible().catch(() => false)) {
        await el.check({ force: true });
        console.log(`Checked all_correct for ${tabName}`);
        found = true;
        break;
      }
    }
    if (!found) console.log(`WARNING: all_correct not found visible for ${tabName}`);
    await page.waitForTimeout(300);
  }

  // Verify state
  const checked = await frame.locator('input:checked').evaluateAll(els =>
    els.map(el => ({ name: el.name, value: el.value }))
  );
  const correctFields = checked.filter(c => c.value === 'all_correct');
  console.log(`\nall_correct checked count: ${correctFields.length}`);
  console.log('All correct fields:', JSON.stringify(correctFields));

  // Check completion status
  const formText = await frame.locator('body').innerText({ timeout: 2000 }).catch(() => '');
  const completeMatch = formText.match(/(\d+\/\d+) Complete/g);
  console.log('Completion:', completeMatch);

  // DO NOT submit - just verify state
  console.log('\n=== VERIFICATION (no submit) ===');

  await browser.close();
}

main().catch(e => { console.error(e.message); process.exit(1); });
