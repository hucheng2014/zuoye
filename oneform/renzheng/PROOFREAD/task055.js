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

  // Response A: has_edits, all_necessary, all_correct, complete
  await tab('Response A');
  await radio('has_edits');
  await radio('all_necessary');
  await radio('all_correct');
  await radio('complete');

  // Response B: has_edits, all_necessary, some_incorrect, partial_complete
  // B replaced 洗→讶 (wrong: should be 喜) + kept wrong 地 particle
  await tab('Response B');
  await radio('has_edits');
  await radio('all_necessary');
  await radio('some_incorrect');
  await radio('partial_complete');
  await checkbox('poor_word_usage');
  await checkbox('grammatical_mixups');

  // Response C: empty → has_edits, all_unnecessary, core_content, incomplete
  await tab('Response C');
  await radio('has_edits');
  await radio('all_unnecessary');
  await radio('core_content');
  await radio('incomplete');
  await checkbox('spelling_errors');
  await checkbox('grammatical_mixups');

  // Pairwise: A and B → A>B
  await tab('A and B');
  await radio('A>B');

  // Pairwise: A and C → A>>>C
  await tab('A and C');
  await radio('A>>>C');

  // Pairwise: B and C → B>C
  await tab('B and C');
  await radio('B>C');

  // Observation
  const ta = frame.locator('textarea:visible').first();
  await ta.fill('The input has two errors: 惊洗 is a homophone typo for 惊喜 (pleasant surprise; 洗 xǐ confused with 喜 xǐ), and 地 should be 的 since 感觉 is a noun here requiring the adjective marker 的 not adverb marker 地. Response A correctly fixed both errors, producing 惊喜的感觉. Response B replaced 洗 with 讶 (惊讶 = astonished), which is contextually inappropriate for the joyful blind-box experience, and also retained the incorrect 地 particle. Response C returned empty. A is the best response.');
  await act();

  console.log('All filled');

  // Active cycling
  const submitAt = Date.now() + 11 * 60 * 1000;
  const tabNames = ['Response A', 'Response B', 'Response C', 'A and B', 'A and C', 'B and C'];
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
  console.log('Submitted task-055');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
