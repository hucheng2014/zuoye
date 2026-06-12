const { chromium } = require('playwright');
const CDP_ENDPOINT = process.env.MAIL_CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP_ENDPOINT);
  try {
    const context = browser.contexts()[0];
    if (!context) throw new Error('No context found');
    const page = context.pages().find((p) => p.url().includes('starshot.scilliance.com')) || context.pages()[0];
    if (!page) throw new Error('No page found');

    const submitBtn = page.locator('button', { hasText: 'Submit' }).first();
    if (await submitBtn.count() > 0) {
      console.log('Clicking Submit button in confirmation dialog...');
      await submitBtn.click();
      console.log('Clicked Submit in dialog. Waiting for dialog to disappear...');
      await page.waitForTimeout(2000);
    }

    const doneBtn = page.getByLabel('Submit Task');
    if (await doneBtn.count() > 0) {
      const isVisible = await doneBtn.first().isVisible();
      const isDisabled = await doneBtn.first().isDisabled();
      console.log(`Done button status: visible=${isVisible}, disabled=${isDisabled}`);
      if (isVisible && !isDisabled) {
        console.log('Clicking Done button...');
        await doneBtn.first().click();
        console.log('Clicked Done button. Waiting for page transition...');
        await page.waitForTimeout(3000);
      }
    }
    
    const body = await page.locator('body').innerText({ timeout: 2000 }).catch(() => '');
    console.log('--- Page text preview ---');
    console.log(body.slice(0, 1000));
    console.log('-------------------------');
  } finally {
    await browser.close();
  }
}
// Wrap main execution in a 45s absolute timeout to prevent indefinite hangs
Promise.race([
  main(),
  new Promise((_, reject) => setTimeout(() => reject(new Error('CLICK_CONFIRM_SUBMIT_TIMEOUT_LIMIT_REACHED')), 45000))
]).catch((error) => {
  console.error(`[FATAL_TIMEOUT] Click confirm submit script timed out or failed: ${error.stack || error.message}`);
  process.exit(1);
});
