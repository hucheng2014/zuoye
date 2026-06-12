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
  await radio('has_grammar_errors');

  // Response A: has_edits, all_necessary, all_correct, complete
  await tab('Response A');
  await radio('has_edits');
  await radio('all_necessary');
  await radio('all_correct');
  await radio('complete');

  // Response B: has_edits, some_unnecessary, all_correct, core_content, complete
  await tab('Response B');
  await radio('has_edits');
  await radio('some_unnecessary');
  await radio('all_correct');
  await radio('core_content');
  await radio('complete');

  // Response C: has_edits, some_unnecessary, all_correct, core_content, complete
  await tab('Response C');
  await radio('has_edits');
  await radio('some_unnecessary');
  await radio('all_correct');
  await radio('core_content');
  await radio('complete');

  // Pairwise: B and A → A>B
  await tab('B and A');
  await radio('A>B');

  // Pairwise: C and A → A>C
  await tab('C and A');
  await radio('A>C');

  // Pairwise: C and B → B=C
  await tab('C and B');
  await radio('B=C');

  // Observation
  const ta = frame.locator('textarea:visible').first();
  await ta.fill('The input has a word order error: 都我 should be 我都 (the adverb 都 must follow the subject 我, not precede it). Response A made only this minimal necessary correction, preserving everything else including the colloquial particle 的. Response B fixed the error differently by removing 我 (subject deletion) and also removed 的 unnecessarily. Response C fixed the word order but also changed 品位 to 品味 (an unnecessary semantic substitution) and removed 的. A is the best response for making only the minimal required correction.');
  await act();

  console.log('All filled');

  // Active cycling loop
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
  console.log('Submitted task-051');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
