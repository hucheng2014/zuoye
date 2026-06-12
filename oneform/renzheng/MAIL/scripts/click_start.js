const { chromium } = require('playwright');

const CDP_ENDPOINT = process.env.MAIL_CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP_ENDPOINT);
  try {
    const context = browser.contexts()[0];
    if (!context) throw new Error('No context found');
    const page = context.pages().find((p) => p.url().includes('starshot.scilliance.com')) || context.pages()[0];
    if (!page) throw new Error('No page found');

    console.log('Locating Start button...');
    const startBtn = page.locator('button', { hasText: 'Start' }).first();
    const count = await startBtn.count();
    console.log(`Found ${count} Start button(s)`);

    if (count > 0) {
      console.log('Clicking Start button...');
      await startBtn.click();
      console.log('Waiting 5 seconds for page load...');
      await page.waitForTimeout(5000);
    } else {
      console.log('Start button not found.');
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
