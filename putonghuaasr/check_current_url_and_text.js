const { chromium } = require('playwright');

async function run() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9237');
  const page = browser.contexts()[0].pages()[0];
  
  console.log('Current page URL:', page.url());
  const origCaption = await page.locator("div[class*='captionBlock']").first().innerText().catch(() => 'N/A');
  console.log('--- Current Original Caption ---');
  console.log(origCaption);
  console.log('--------------------------------');
  await browser.close();
}

run().catch(console.error);
