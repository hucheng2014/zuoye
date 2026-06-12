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

  // Response A: some_unnecessary, all_correct, mechanical type, nearly_complete, spelling_errors missed
  await tab('Response A');
  await radio('has_edits');
  await radio('some_unnecessary');
  await radio('all_correct');
  await radio('mechanical');   // unnecessaryImpact type
  await checkbox('mechanical'); // sub-type checkbox after mechanical type
  await radio('nearly_complete');
  await checkbox('spelling_errors'); // missedErrors: missed 对干→对于

  // Response B: all_necessary, all_correct, nearly_complete, spelling_errors missed
  await tab('Response B');
  await radio('has_edits');
  await radio('all_necessary');
  await radio('all_correct');
  await radio('nearly_complete');
  await checkbox('spelling_errors'); // missedErrors: missed 对干→对于

  // Response C: all_unnecessary, formatting type, spacing sub-type, incomplete
  await tab('Response C');
  await radio('has_edits');
  await radio('all_unnecessary');
  await radio('formatting');   // unnecessaryImpact type
  await checkbox('spacing');   // sub-type: added newlines
  await radio('incomplete');
  await checkbox('spelling_errors');     // missed: 笨掘, 选择困难证, 对干
  await checkbox('grammatical_mixups'); // missed: 没在意一直 word order

  // Pairwise: B and A → B>A
  await tab('B and A');
  await radio('B>A');

  // Pairwise: C and A → A>>>C
  await tab('C and A');
  await radio('A>>>C');

  // Pairwise: C and B → B>>>C (extra wait for equal-adjacent tabs)
  await tab('C and B');
  await page.waitForTimeout(1000);
  await radio('B>>>C');

  // Observation
  const ta = frame.locator('textarea:visible').first();
  await ta.fill('The input contained multiple errors: a word order error ("没在意一直"), two character typos ("笨掘"→"笨拙", "选择困难证"→"选择困难症"), an undetected typo ("对干"→"对于"), and ASCII punctuation. Response B correctly fixed all necessary errors with minimal changes. Response A fixed the same but added an unnecessary word order swap ("甚至自动还"→"甚至还自动"). Response C only reformatted with line breaks, correcting nothing.');
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
  console.log('Submitted task-062');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
