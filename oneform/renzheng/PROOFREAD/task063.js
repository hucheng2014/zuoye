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
  await radio('formal');
  await radio('has_grammar_errors');

  // Response A: all_necessary, all_correct, complete
  await tab('Response A');
  await radio('has_edits');
  await radio('all_necessary');
  await radio('all_correct');
  await radio('complete');

  // Response B: all_necessary, all_correct, complete
  await tab('Response B');
  await radio('has_edits');
  await radio('all_necessary');
  await radio('all_correct');
  await radio('complete');

  // Response C: all_unnecessary, formatting type, spacing sub-type, incomplete, missedErrors
  await tab('Response C');
  await radio('has_edits');
  await radio('all_unnecessary');
  await radio('formatting');      // unnecessaryImpact type
  await checkbox('spacing');      // sub-type: added paragraph breaks
  await radio('incomplete');
  await checkbox('grammatical_mixups');  // missed: 严重的→严重地, 制造→造成, 形成→造成
  await checkbox('spelling_errors');     // missed: 发上→发生
  await checkbox('poor_word_usage');     // missed: 制造→造成, 形成→造成

  // Pairwise: A and B → A>B
  await tab('A and B');
  await radio('A>B');

  // Pairwise: A and C → A>>>C
  await tab('A and C');
  await radio('A>>>C');

  // Pairwise: B and C → B>>>C
  await tab('B and C');
  await page.waitForTimeout(1000);
  await radio('B>>>C');

  // Observation
  const ta = frame.locator('textarea:visible').first();
  await ta.fill('The input had four errors: a character typo ("发上"→"发生"), a 的/地 error ("严重的污染了"→"严重地污染了"), and two word choice errors ("制造"→"造成", "形成"→"造成"). Responses A and B both fixed all four errors. Response A used "严重地污染了" (standard grammar correction) while Response B used "严重污染了" (dropped 地 entirely). Response A is marginally preferred as it preserves the adverbial structure more formally. Response C only added paragraph breaks without correcting any errors, making it incomplete.');
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
  console.log('Submitted task-063');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
