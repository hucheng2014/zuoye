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

  // Response A: all_necessary, all_correct, complete (fixed comma only)
  await tab('Response A');
  await radio('has_edits');
  await radio('all_necessary');
  await radio('all_correct');
  await radio('complete');

  // Response B: some_unnecessary, mechanical type, mechanical sub-type, complete
  await tab('Response B');
  await radio('has_edits');
  await radio('some_unnecessary');
  await radio('all_correct');   // editsCorrect (required after some_unnecessary)
  await radio('mechanical');
  await checkbox('mechanical');
  await radio('complete');

  // Response C: all_unnecessary, core_content type, incomplete, mild_punctuation_formatting missed
  await tab('Response C');
  await radio('has_edits');
  await radio('all_unnecessary');
  await radio('core_content');
  await radio('incomplete');
  await checkbox('mild_punctuation_formatting');

  // Pairwise: B and A → A>B
  await tab('B and A');
  await radio('A>B');

  // Pairwise: C and A → A>>>C
  await tab('C and A');
  await radio('A>>>C');

  // Pairwise: C and B → B>>>C
  await tab('C and B');
  await page.waitForTimeout(1000);
  await radio('B>>>C');

  // Observation
  const ta = frame.locator('textarea:visible').first();
  await ta.fill('The input had one error: a missing comma after "了" ("发你邮箱了查收一下" → "发你邮箱了，查收一下"). Response A correctly added only this comma — a precise minimal fix. Response B also added the comma but additionally changed "15:00" to "三点", which was unnecessary since "下午15:00" is commonly accepted in informal Chinese. Response C returned an empty string, entirely removing the input.');
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
  console.log('Submitted task-065');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
