require('./_timeout');
const { chromium } = require('playwright');
const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function checkBox(frame, name, value) {
  const loc = frame.locator(`input[type="checkbox"][name="${name}"][value="${value}"]`);
  if (await loc.count()) {
    await loc.first().check({ force: true });
    console.log(`  Checked ${name} = ${value}`);
  } else {
    console.log(`  NOT FOUND: ${name} = ${value}`);
  }
}

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  const frame = page.frames().find(f => f.url().includes('task-editor'));

  // === Response A ===
  console.log('=== Response A ===');
  const tabA = frame.locator('button[role="tab"]').filter({ hasText: 'Response A' });
  await tabA.first().click({ timeout: 3000 });
  await page.waitForTimeout(600);

  // 12-item group: errors in unnecessary edits
  await checkBox(frame, 'oUpxh7QfQmfuFJ5UjvihJ', 'word_choice_alteration');
  await checkBox(frame, 'oUpxh7QfQmfuFJ5UjvihJ', 'new_errors');
  await page.waitForTimeout(300);

  // 5-item group: type of unnecessary edits
  await checkBox(frame, 'G-4T3Kqk7o43bLBb-Vy9U', 'mechanical');
  await page.waitForTimeout(300);

  // 8-item group: uncorrected/improperly corrected errors
  await checkBox(frame, 'U4kThOe776Dtab944SHCQ', 'mild_punctuation_formatting');
  await checkBox(frame, 'U4kThOe776Dtab944SHCQ', 'poor_word_usage');
  await page.waitForTimeout(300);

  // === Response C ===
  console.log('\n=== Response C ===');
  const tabC = frame.locator('button[role="tab"]').filter({ hasText: 'Response C' });
  await tabC.first().click({ timeout: 3000 });
  await page.waitForTimeout(600);

  // 12-item group: errors in unnecessary edits
  await checkBox(frame, '5bSvqPU0MWWQmTQJq73Fv', 'new_errors');
  await checkBox(frame, '5bSvqPU0MWWQmTQJq73Fv', 'spacing');
  await page.waitForTimeout(300);

  // 8-item group: uncorrected/improperly corrected errors
  await checkBox(frame, 'Fv-JCkFDLAKQWoBKy7Yke', 'poor_word_usage');
  await checkBox(frame, 'Fv-JCkFDLAKQWoBKy7Yke', 'mild_punctuation_formatting');
  await checkBox(frame, 'Fv-JCkFDLAKQWoBKy7Yke', 'spelling_errors');
  await page.waitForTimeout(300);

  // Verify completion
  await page.waitForTimeout(500);
  const bodyText = await frame.locator('body').innerText({ timeout: 2000 }).catch(() => '');
  const completion = bodyText.match(/\d+\/\d+ Complete/g);
  console.log('\nCompletion:', completion);

  await browser.close();
}

main().catch(e => { console.error(e.stack || e.message); process.exit(1); });
