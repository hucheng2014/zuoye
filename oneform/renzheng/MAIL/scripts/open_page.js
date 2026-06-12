const { chromium } = require('playwright');
const CDP_ENDPOINT = process.env.MAIL_CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP_ENDPOINT);
  try {
    const context = browser.contexts()[0];
    const page = await context.newPage();
    await page.goto('https://starshot.scilliance.com/?broker=true');
    console.log('Page reopened.');
  } finally {
    await browser.close();
  }
}
main();
