require('./_timeout');
const { chromium } = require('playwright');

const CDP_ENDPOINTS = [
  process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233',
  'http://127.0.0.1:9232',
];

async function connect() {
  for (const ep of CDP_ENDPOINTS) {
    try { return { browser: await chromium.connectOverCDP(ep), endpoint: ep }; } catch {}
  }
  throw new Error('No CDP endpoint available');
}

async function main() {
  const { browser } = await connect();
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  await page.setViewportSize({width: 1919, height: 1079});
  const frame = page.frames().find(f => f.url().includes('task-editor'));

  // === Step 1: Response B tab - fill dynamic checkbox "mechanical" ===
  console.log('Step 1: Switching to Response B tab...');
  const tabB = frame.locator('button[role="tab"]:has-text("Response B")').first();
  await tabB.click();
  await page.waitForTimeout(2000);

  // Scroll down to find dynamic checkboxes
  await frame.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(500);
  await frame.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(500);
  await frame.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(500);

  // Find the dynamic checkbox group with name EPqQMZGVMnWFggEOsp7TT
  const mechanicalCheckbox = frame.locator('input[type="checkbox"][name="EPqQMZGVMnWFggEOsp7TT"][value="mechanical"]');
  const mechCount = await mechanicalCheckbox.count();
  console.log(`Found ${mechCount} mechanical checkboxes in dynamic group`);
  if (mechCount > 0) {
    await mechanicalCheckbox.first().check({ force: true });
    console.log('Checked mechanical checkbox in Response B dynamic group');
  } else {
    // Fallback: find by value
    const allMech = frame.locator('input[type="checkbox"][value="mechanical"]');
    const allMechCount = await allMech.count();
    console.log(`Fallback: found ${allMechCount} mechanical checkboxes total`);
    if (allMechCount > 0) {
      // Check the last visible one (likely in dynamic group)
      await allMech.last().check({ force: true });
      console.log('Checked last mechanical checkbox');
    }
  }
  await page.waitForTimeout(1000);

  // Verify Response B
  const respBChecks = await frame.evaluate(() => {
    const group = document.querySelector('input[name="EPqQMZGVMnWFggEOsp7TT"][value="mechanical"]');
    return group ? group.checked : 'not found';
  });
  console.log('Response B mechanical checkbox state:', respBChecks);

  // === Step 2: Fill Pairwise comparisons ===
  // A vs B: A>>>B
  console.log('Step 2: Switching to A and B pairwise tab...');
  const tabAB = frame.locator('button[role="tab"]:has-text("A and B")').first();
  await tabAB.click();
  await page.waitForTimeout(2000);

  // Click A>>>B (Left Much Better)
  const abRadio = frame.locator('input[type="radio"][name="lhibvYfpu69u04_n4LBzq"][value="A>>>B"]');
  await abRadio.check({ force: true });
  console.log('Checked A>>>B');
  await page.waitForTimeout(1000);

  // A vs C: A=C
  console.log('Step 3: Switching to A and C pairwise tab...');
  const tabAC = frame.locator('button[role="tab"]:has-text("A and C")').first();
  await tabAC.click();
  await page.waitForTimeout(2000);

  // Click A=C (About The Same)
  const acRadio = frame.locator('input[type="radio"][name="kXkNHYEdwNRxZnCvI7G14"][value="A=C"]');
  await acRadio.check({ force: true });
  console.log('Checked A=C');
  await page.waitForTimeout(1000);

  // B vs C: C>>>B
  console.log('Step 4: Switching to B and C pairwise tab...');
  const tabBC = frame.locator('button[role="tab"]:has-text("B and C")').first();
  await tabBC.click();
  await page.waitForTimeout(2000);

  // Click C>>>B (Right Much Better)
  const bcRadio = frame.locator('input[type="radio"][name="PtKaqBf-4Z6t9wAxbk-OB"][value="C>>>B"]');
  await bcRadio.check({ force: true });
  console.log('Checked C>>>B');
  await page.waitForTimeout(1000);

  // === Step 3: Fill Observation textarea ===
  console.log('Step 5: Filling observation textarea...');
  // Scroll to bottom
  await frame.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(500);

  // Find observation textarea and fill it
  const textareas = await frame.locator('textarea').all();
  console.log(`Found ${textareas.length} textareas`);
  for (let i = 0; i < textareas.length; i++) {
    const t = textareas[i];
    const isVisible = await t.isVisible();
    if (isVisible) {
      const placeholder = await t.getAttribute('placeholder') || '';
      const name = await t.getAttribute('name') || '';
      const val = await t.inputValue();
      console.log(`Textarea ${i}: visible=${isVisible}, name=${name}, placeholder=${placeholder}, currentVal="${val.substring(0,30)}"`);
    }
  }
  
  // The observation textarea is likely on the pairwise tab - fill the one that's for "observations"
  // We need to find the empty textarea (not the one with "x" value)
  for (let i = textareas.length - 1; i >= 0; i--) {
    const t = textareas[i];
    try {
      const isVisible = await t.isVisible();
      if (isVisible) {
        const val = await t.inputValue();
        if (!val || val === '' || val === 'x') {
          await t.click({ force: true });
          await t.selectAll();
          await t.fill('Response A and C both correctly fix the typo from 风向 to 风险 with no unnecessary changes, but miss correcting 入期 to 日期. Response B incorrectly changes 风险 to 倾向 and adds unnecessary 一下, making it the worst.');
          console.log('Filled observation textarea');
          break;
        }
      }
    } catch(e) {
      // skip invisible
    }
  }

  await page.waitForTimeout(1000);
  console.log('All fixes applied!');

  await browser.disconnect();
  process.exit(0);
}

main().catch(e => { console.error(e); process.exit(1); });