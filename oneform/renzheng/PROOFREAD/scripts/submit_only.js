require('./_timeout');
const { chromium } = require('playwright');
const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  const frame = page.frames().find(f => f.url().includes('task-editor'));
  if (!frame) throw new Error('No task-editor frame');

  // Click inner Submit
  const submitBtn = frame.locator('button').filter({ hasText: 'Submit' }).first();
  if (await submitBtn.count()) {
    await submitBtn.click({ timeout: 5000 });
    console.log('Inner Submit clicked');
  }
  await page.waitForTimeout(2000);

  // Check for errors
  const errors = await frame.locator('[class*="error"], [class*="invalid"]').evaluateAll(els =>
    els.filter(el => el.offsetParent !== null).map(el => (el.innerText || '').trim().slice(0, 100)).filter(t => t)
  );
  if (errors.length) {
    console.log('ERRORS:', errors);
    await browser.close();
    return;
  }

  // Check if outer Done/Submit Task button appeared
  const doneBtn = page.getByLabel('Submit Task');
  if (await doneBtn.count()) {
    const vis = await doneBtn.isVisible().catch(() => false);
    if (vis) {
      await doneBtn.click({ timeout: 5000 });
      console.log('Outer Done clicked');
      await page.waitForTimeout(3000);
    }
  }

  // Check for Next Task button
  const nextBtn = page.locator('button').filter({ hasText: 'Next Task' });
  if (await nextBtn.count()) {
    const vis = await nextBtn.first().isVisible().catch(() => false);
    console.log('Next Task button visible:', vis);
  }

  // Check body for "no available tasks"
  const body = await page.locator('body').innerText({ timeout: 3000 }).catch(e => e.message);
  const noTasks = body.includes('no available tasks') || body.includes('there are no');
  console.log('No tasks:', noTasks);
  console.log('Body preview:', body.slice(0, 300));

  await browser.close();
}

main().catch(e => { console.error(e.message); process.exit(1); });
