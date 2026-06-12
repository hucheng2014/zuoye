const { chromium } = require('playwright');

const CDP_ENDPOINT = process.env.MAIL_CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP_ENDPOINT);
  try {
    const context = browser.contexts()[0];
    if (!context) {
      console.log('No context found');
      return;
    }
    const pages = context.pages();
    console.log(`Found ${pages.length} page(s):`);
    for (let i = 0; i < pages.length; i++) {
      const page = pages[i];
      console.log(`Page ${i}: URL="${page.url()}" Title="${await page.title().catch(() => '')}"`);
    }
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
