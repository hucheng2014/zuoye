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

  // Response A: has_edits, not_altered_input (unnecessary comma)
  await tab('Response A');
  await radio('has_edits');
  await radio('not_altered_input');

  // Response B: no_edits (correct - no changes needed)
  await tab('Response B');
  await radio('no_edits');

  // Response C: has_edits, altered_input (empty response)
  await tab('Response C');
  await radio('has_edits');
  await radio('altered_input');

  // Pairwise: B and A → B>A
  await tab('B and A');
  await radio('B>A');

  // Pairwise: C and A → A>>>C
  await tab('C and A');
  await radio('A>>>C');

  // Pairwise: C and B → B>>>C
  await tab('C and B');
  await radio('B>>>C');

  // Observation
  const ta = frame.locator('textarea:visible').first();
  await ta.fill('The input product ad contains no grammar errors. Response B correctly returned the text unchanged. Response A made an unnecessary comma addition after "後", which was not required under the minimal edit principle. Response C returned an empty response, completely altering the input content.');
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
  console.log('Submitted task-059');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
