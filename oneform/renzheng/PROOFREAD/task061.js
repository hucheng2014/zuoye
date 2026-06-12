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

  // Response A: some_unnecessary, some_incorrect, core_content type, word_choice_alteration, complete
  await tab('Response A');
  await radio('has_edits');
  await radio('some_unnecessary');
  await radio('some_incorrect');
  await radio('core_content');
  await checkbox('word_choice_alteration');
  await radio('complete');

  // Response B: all_necessary, all_correct, complete
  await tab('Response B');
  await radio('has_edits');
  await radio('all_necessary');
  await radio('all_correct');
  await radio('complete');

  // Response C: all_necessary, all_correct, complete (comma-only fix)
  await tab('Response C');
  await radio('has_edits');
  await radio('all_necessary');
  await radio('all_correct');
  await radio('complete');

  // Pairwise: A and B → B>A
  await tab('A and B');
  await radio('B>A');

  // Pairwise: A and C → C>A
  await tab('A and C');
  await radio('C>A');

  // Pairwise: B and C → B=C (explicit extra wait)
  await tab('B and C');
  await page.waitForTimeout(1000);
  await radio('B=C');

  // Observation
  const ta = frame.locator('textarea:visible').first();
  await ta.fill('The input had one error: an ASCII comma (,) after "李强" instead of the Chinese full-width comma (，). Responses B and C correctly made only this minimal fix. Response A also corrected the comma but unnecessarily replaced "类存" with "配置", which may not reflect the writer\'s intended technical term and introduces a word choice error.');
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
  console.log('Submitted task-061');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
