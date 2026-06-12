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

  // Global: formality + Q1
  await radio('other');
  await radio('has_grammar_errors');

  // Response A: no_edits (A kept errors unchanged)
  await tab('Response A');
  await radio('no_edits');

  // Response B: has_edits, all_necessary, all_correct, complete
  await tab('Response B');
  await radio('has_edits');
  await radio('all_necessary');
  await radio('all_correct');
  await radio('complete');

  // Response C: has_edits, all_unnecessary, core_content, incomplete + spelling_errors
  await tab('Response C');
  await radio('has_edits');
  await radio('all_unnecessary');
  await radio('core_content');
  await radio('incomplete');
  await checkbox('spelling_errors');

  // Pairwise: B and A → B>>>A
  await tab('B and A');
  await radio('B>>>A');

  // Pairwise: C and A → A>C
  await tab('C and A');
  await radio('A>C');

  // Pairwise: C and B → B>>>C
  await tab('C and B');
  await radio('B>>>C');

  // Observation textarea (visible, name=null)
  const ta = frame.locator('textarea:visible').first();
  await ta.fill('The input is a casual cooking tip with two spelling errors: 基本工 (should be 基本功, meaning basic skills) and 砸实 (should be 扎实, meaning solid/thorough). Response A made no changes, leaving both errors uncorrected. Response B correctly fixed both errors without any unnecessary changes, producing a well-proofread result. Response C returned an empty string. B is clearly the best response; A preserved the content at least; C is worst.');
  await act();

  console.log('All filled');

  // Active cycling loop until submitAt
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
  console.log('Submitted task-050');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
