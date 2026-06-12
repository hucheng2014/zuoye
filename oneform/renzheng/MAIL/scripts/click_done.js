const { chromium } = require('playwright');

const CDP_ENDPOINT = process.env.MAIL_CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP_ENDPOINT);
  try {
    const context = browser.contexts()[0];
    if (!context) throw new Error('No context found');
    const page = context.pages().find((p) => p.url().includes('starshot.scilliance.com')) || context.pages()[0];
    if (!page) throw new Error('No page found');

    console.log('Checking Done button status...');
    const doneBtn = page.getByLabel('Submit Task');
    const count = await doneBtn.count();
    console.log(`Found ${count} Done button(s)`);

    if (count > 0) {
      const isVisible = await doneBtn.first().isVisible();
      const isDisabled = await doneBtn.first().isDisabled();
      console.log(`Visibility: ${isVisible}, Disabled: ${isDisabled}`);

      if (isVisible && !isDisabled) {
        console.log('Clicking Done button with force...');
        await doneBtn.first().click({ force: true }).catch(async (e) => {
          console.log(`Force click failed: ${e.message}. Trying evaluate click...`);
          await doneBtn.first().evaluate(el => el.click());
        });
        console.log('Clicked Done button. Waiting for page transition...');
        await page.waitForTimeout(3000);
      } else {
        console.log('Done button is not clickable right now.');
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

main().catch(console.error);
