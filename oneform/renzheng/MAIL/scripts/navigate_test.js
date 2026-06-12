const { chromium } = require('playwright');

const CDP_ENDPOINT = process.env.MAIL_CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  console.log('Connecting to CDP...');
  const browser = await chromium.connectOverCDP(CDP_ENDPOINT);
  try {
    const context = browser.contexts()[0];
    if (!context) throw new Error('No context found');
    const page = context.pages().find((p) => p.url().includes('starshot.scilliance.com')) || context.pages()[0];
    if (!page) throw new Error('No page found');

    console.log(`Current page URL: "${page.url()}"`);
    console.log('Navigating to https://starshot.scilliance.com/?broker=true ...');
    const response = await page.goto('https://starshot.scilliance.com/?broker=true', { waitUntil: 'commit', timeout: 10000 });
    console.log(`Navigation successful! Status: ${response ? response.status() : 'no response'}`);
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
