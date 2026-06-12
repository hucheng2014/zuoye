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

  // Response A: has_edits, all_necessary, complete
  await tab('Response A');
  await radio('has_edits');
  await radio('all_necessary');
  await radio('complete');

  // Response B: has_edits, some_unnecessary, core_content, complete
  await tab('Response B');
  await radio('has_edits');
  await radio('some_unnecessary');
  await radio('core_content');
  await radio('complete');

  // Response C: has_edits, all_unnecessary, formatting, incomplete
  await tab('Response C');
  await radio('has_edits');
  await radio('all_unnecessary');
  await radio('formatting');
  await radio('incomplete');

  // Pairwise
  await tab('A and B');
  await radio('A>B');
  await tab('A and C');
  await radio('A>>>C');
  await tab('B and C');
  await radio('B>>>C');

  // Observation
  const obs = 'The input is an informal message about a father\'s medical report with three errors: 整里 (typo for 整理), 乱七八遭 (wrong character for 乱七八糟), and missing commas between 输尿管/膀胱/前列腺. Response A correctly fixed all three errors with no additional changes. Response B fixed all errors but also removed 让 (altering the meaning of the sentence) and changed a period to a comma unnecessarily. Response C only reformatted the numbered list from inline to multiline, leaving all three errors uncorrected. A is the best response.';
  const ta = frame.locator('textarea[name="input"]').first();
  if (await ta.count()) await ta.fill(obs);
  await act();

  console.log('All filled');

  // Keep active until submitAt
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
  console.log('Submitted task-049');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
