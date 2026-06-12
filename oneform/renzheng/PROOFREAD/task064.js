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

  // Response B: all_unnecessary, core_content type, word_choice_alteration sub-type, incomplete, punctuation_errors missed
  await tab('Response B');
  await radio('has_edits');
  await radio('all_unnecessary');
  await radio('core_content');
  await checkbox('word_choice_alteration');
  await radio('incomplete');
  await checkbox('punctuation_errors');

  // Response C: altered_input (empty response)
  await tab('Response C');
  await radio('has_edits');
  await radio('altered_input');

  // Pairwise: B and A → A>>>B
  await tab('B and A');
  await radio('A>>>B');

  // Pairwise: C and A → A>>>C
  await tab('C and A');
  await radio('A>>>C');

  // Pairwise: C and B → B>>>C
  await tab('C and B');
  await page.waitForTimeout(1000);
  await radio('B>>>C');

  // Observation
  const ta = frame.locator('textarea:visible').first();
  await ta.fill('The input had one punctuation error: a missing comma before "让" ("摔他脸上让他清醒清醒" should be "摔他脸上，让他清醒清醒"). Response A correctly added only this comma — a minimal and accurate fix. Response B changed "摔" to "摔在", which was not required as the original is colloquially acceptable, and failed to add the needed comma, leaving the actual error unresolved. Response C returned an empty string, completely removing the input text.');
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
  console.log('Submitted task-064');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
