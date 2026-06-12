require('./_timeout');
const { chromium } = require('playwright');
const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  const frame = page.frames().find(f => f.url().includes('task-editor'));

  const tabs = ['Response A', 'Response B', 'Response C'];
  for (const tabName of tabs) {
    const tab = frame.getByRole('tab', { name: tabName, exact: true });
    if (await tab.count()) {
      await tab.first().click();
      await page.waitForTimeout(500);
    }

    // Find and check the "all_correct" radio (visible one in active tab)
    const allCorrect = frame.locator('input[type="radio"][value="all_correct"]');
    const count = await allCorrect.count();
    for (let i = 0; i < count; i++) {
      const el = allCorrect.nth(i);
      const vis = await el.isVisible().catch(() => false);
      if (vis) {
        await el.check({ force: true });
        console.log(`Checked all_correct for ${tabName}`);
        break;
      }
    }
    await page.waitForTimeout(300);
  }

  // Now submit via inner frame Submit button
  const submitBtn = frame.locator('button:has-text("Submit")').first();
  if (await submitBtn.count()) {
    await submitBtn.click({ timeout: 3000 });
    console.log('Clicked inner Submit');
  }
  await page.waitForTimeout(2000);

  // Check if outer Done button needs clicking
  const doneBtn = page.getByLabel('Submit Task');
  if (await doneBtn.count()) {
    const vis = await doneBtn.isVisible().catch(() => false);
    if (vis) {
      await doneBtn.click({ timeout: 3000 });
      console.log('Clicked outer Done');
    }
  }
  await page.waitForTimeout(2000);

  // Check page state
  const body = await page.locator('body').innerText({ timeout: 3000 }).catch(e => e.message);
  console.log('Page state:', body.slice(0, 300));

  await browser.close();
}

main().catch(e => { console.error(e.message); process.exit(1); });
