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

  // Fix Response B: re-fill correctness + completeness
  await tab('Response B');
  await radio('all_unnecessary');
  await radio('core_content');
  await checkbox('word_choice_alteration');
  await radio('incomplete');
  await checkbox('punctuation_errors');

  // Fix Response C: empty response needs correctness flow (not altered_input)
  await tab('Response C');
  await radio('all_unnecessary');
  await radio('core_content');
  await checkbox('word_choice_alteration');
  await radio('incomplete');
  await checkbox('punctuation_errors');

  console.log('Fix done');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
