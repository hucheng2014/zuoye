const { chromium } = require('playwright');
const CDP_ENDPOINT = process.env.MAIL_CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP_ENDPOINT);
  try {
    const context = browser.contexts()[0];
    const page = context.pages().find((p) => p.url().includes('starshot.scilliance.com')) || context.pages()[0];
    console.log('Clicking Cancel...');
    await page.locator('button', { hasText: 'Cancel' }).first().click({ timeout: 5000 });
    console.log('Clicked Cancel.');
    await page.waitForTimeout(3000);
    const body = await page.locator('body').innerText({ timeout: 2000 }).catch(() => '');
    console.log('Current body text:', body.slice(0, 1000));
  } finally {
    await browser.close();
  }
}
main().catch(console.error);
