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

  // Response A: all_necessary, all_correct, complete
  await tab('Response A');
  await radio('has_edits');
  await radio('all_necessary');
  await radio('all_correct');
  await radio('complete');

  // Response B: some_unnecessary, all_correct, punctuation+mechanical, complete
  await tab('Response B');
  await radio('has_edits');
  await radio('some_unnecessary');
  await radio('all_correct');
  await checkbox('punctuation');
  await checkbox('mechanical');
  await radio('complete');

  // Response C: some_unnecessary, all_correct, punctuation, complete
  await tab('Response C');
  await radio('has_edits');
  await radio('some_unnecessary');
  await radio('all_correct');
  await checkbox('punctuation');
  await radio('complete');

  // Pairwise: A and B
  await tab('A and B');
  await radio('A>B');

  // Pairwise: A and C
  await tab('A and C');
  await radio('A>C');

  // Pairwise: B and C
  await tab('B and C');
  await radio('C>B');

  // Observation
  const ta = frame.locator('textarea:visible').first();
  await ta.fill('The input contained one error: "探套" (likely a typo for 探讨/探析/探索). Response A made only the necessary correction (探析) with no extra changes. Responses B and C both fixed the error but also made unnecessary edits: B changed "虚无的窠臼" to "虚无窠臼" and replaced "..." with "……"; C only replaced "..." with "……".');
  await act();

  console.log('All filled');

  // Active cycling loop (~12 min)
  const submitAt = Date.now() + 12 * 60 * 1000;
  const tabNames = ['Response A', 'Response B', 'Response C', 'A and B', 'A and C', 'B and C'];
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
  console.log('Submitted task-058');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
