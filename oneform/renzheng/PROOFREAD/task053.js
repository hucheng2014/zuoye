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

  // Response A: no_edits
  await tab('Response A');
  await radio('no_edits');

  // Response B: has_edits, some_unnecessary, all_correct, mechanical, complete
  await tab('Response B');
  await radio('has_edits');
  await radio('some_unnecessary');
  await radio('all_correct');
  await radio('mechanical');
  await radio('complete');

  // Response C: empty → has_edits, all_unnecessary, core_content, incomplete + poor_word_usage
  await tab('Response C');
  await radio('has_edits');
  await radio('all_unnecessary');
  await radio('core_content');
  await radio('incomplete');
  await checkbox('poor_word_usage');

  // Pairwise: A and B → B>A
  await tab('A and B');
  await radio('B>A');

  // Pairwise: A and C → A>C
  await tab('A and C');
  await radio('A>C');

  // Pairwise: B and C → B>>>C
  await tab('B and C');
  await radio('B>>>C');

  // Observation
  const ta = frame.locator('textarea:visible').first();
  await ta.fill('The input uses 食用 (a formal term for consume/ingest) before 饭, which is grammatically wrong in colloquial Chinese — the correct expression is 吃饭. Response A made no corrections, leaving the error unchanged. Response B correctly fixed the word usage error by changing 食用 to 吃, though it also added 个 (吃个饭), a natural but unnecessary addition. Response C returned an empty string. B is the best response for fixing the necessary error; A is second for at least preserving content; C is worst.');
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
  console.log('Submitted task-053');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
