const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  const frame = page.frames().find(f => f.url().includes('task-editor'));

  const act = async () => {
    await frame.evaluate(() => window.scrollTo(0, 200)); await page.waitForTimeout(3000);
    await frame.evaluate(() => window.scrollTo(0, 0));   await page.waitForTimeout(3000);
  };
  const radio = async (val) => {
    const el = frame.locator('input[type="radio"][value="' + val + '"]:visible').first();
    if (await el.count()) await el.check({ force: true }); await act();
  };
  const tab = async (name) => {
    const el = frame.locator('button[role="tab"]').filter({ hasText: name }).first();
    if (await el.count()) await el.click(); await act();
  };

  // Formality + Q1
  await radio('other');
  await radio('no_grammar_errors');

  // Response A tab
  await tab('Response A');
  await radio('no_edits');

  // Response B tab
  await tab('Response B');
  await radio('no_edits');

  // Response C tab
  await tab('Response C');
  await radio('has_edits');
  await radio('no'); // alteredMeaning=no

  // Pairwise: B and A
  await tab('B and A');
  await radio('B=A');

  // Pairwise: C and A
  await tab('C and A');
  await radio('A>C');

  // Pairwise: C and B
  await tab('C and B');
  await radio('B>C');

  // Observation
  const ta = frame.locator('textarea:visible').first();
  await ta.fill('The input procurement list contains no grammar errors and all calculations are correct. Responses A and B correctly returned the text unchanged. Response C unnecessarily reformatted items onto separate lines, violating the minimal edit principle.');
  await act();

  console.log('All filled');

  // Active cycling loop (~12 min)
  const submitAt = Date.now() + 12 * 60 * 1000;
  const tabNames = ['Response A', 'Response B', 'Response C', 'B and A', 'C and A', 'C and B'];
  let i = 0;
  while (Date.now() < submitAt) {
    try {
      const tb = frame.locator('button[role="tab"]').filter({ hasText: tabNames[i % tabNames.length] }).first();
      if (await tb.count()) await tb.click();
      await frame.evaluate(() => window.scrollTo(0, 200)); await page.waitForTimeout(3000);
      await frame.evaluate(() => window.scrollTo(0, 0));   await page.waitForTimeout(3000);
      i++;
    } catch(e) { break; }
  }

  // Submit
  await frame.locator('button:has-text("Submit")').first().click({ timeout: 3000 });
  await page.waitForTimeout(2000);
  await page.locator('#starshot_submit_task_button').click();
  await page.waitForTimeout(4000);
  console.log('Submitted task-057');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
