const { chromium } = require('playwright');
const CDP_ENDPOINT = process.env.MAIL_CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP_ENDPOINT);
  try {
    const context = browser.contexts()[0];
    if (!context) throw new Error('No context found');
    const page = context.pages().find((p) => p.url().includes('starshot.scilliance.com')) || context.pages()[0];
    if (!page) throw new Error('No page found');

    const retryBtn = page.locator('button', { hasText: 'Retry' }).first();
    if (await retryBtn.count() > 0 && await retryBtn.isVisible()) {
      console.log('Retry button found! Clicking Retry...');
      await retryBtn.click();
      console.log('Clicked Retry. Waiting 10s for page reaction...');
      await page.waitForTimeout(10000);
    } else {
      console.log('Retry button not found or not visible.');
    }
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
