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
  const checkbox = async (val) => {
    const el = frame.locator('input[type="checkbox"][value="' + val + '"]:visible').first();
    if (await el.count()) await el.check({ force: true }); await act();
  };

  // Formality + Q1
  await radio('other');
  await radio('has_grammar_errors');

  // Response A: has_edits, some_unnecessary, all_correct, core_content, complete
  // A fixed phrasing error (是合→适合) but also unnecessarily changed classifier (辆→台)
  await tab('Response A');
  await radio('has_edits');
  await radio('some_unnecessary');
  await radio('all_correct');
  await radio('core_content');
  await radio('complete');

  // Response B: has_edits, all_necessary, all_correct, complete
  // B added 的 after 合他 — minimal natural fix
  await tab('Response B');
  await radio('has_edits');
  await radio('all_necessary');
  await radio('all_correct');
  await radio('complete');

  // Response C: empty → has_edits, all_unnecessary, core_content, incomplete + grammatical_mixups
  await tab('Response C');
  await radio('has_edits');
  await radio('all_unnecessary');
  await radio('core_content');
  await radio('incomplete');
  await checkbox('grammatical_mixups');

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
  await ta.fill('The input has a phrasing issue: 感觉很是合他 sounds incomplete; the natural forms are 感觉很合他的 or 感觉很适合他. Response A fixed the phrasing by changing 是合 to 适合 (good fix), but also unnecessarily changed the classifier 辆 to 台 without clear context for what is being bought. Response B made the minimal necessary fix by adding 的 after 合他, making it 合他的 — natural in colloquial speech. Response C returned empty. B is better for making only the necessary minimal change; A is second; C is worst.');
  await act();

  console.log('All filled');

  // Active cycling
  const submitAt = Date.now() + 11 * 60 * 1000;
  const tabNames = ['Response A', 'Response B', 'Response C', 'B and A', 'C and A', 'C and B'];
  let i = 0;
  while (Date.now() < submitAt) {
    const tb = frame.locator('button[role="tab"]').filter({ hasText: tabNames[i % tabNames.length] }).first();
    if (await tb.count()) await tb.click();
    await frame.evaluate(() => window.scrollTo(0, 200)); await page.waitForTimeout(3000);
    await frame.evaluate(() => window.scrollTo(0, 0));   await page.waitForTimeout(3000);
    i++;
  }

  // Submit
  await frame.locator('button:has-text("Submit")').first().click({ timeout: 3000 });
  await page.waitForTimeout(2000);
  await page.locator('#starshot_submit_task_button').click();
  await page.waitForTimeout(4000);
  console.log('Submitted task-056');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
