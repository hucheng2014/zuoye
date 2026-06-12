const { chromium } = require('playwright');

async function run() {
  console.log('Connecting to browser on http://127.0.0.1:9235...');
  let browser;
  try {
    browser = await chromium.connectOverCDP('http://127.0.0.1:9235');
  } catch (err) {
    console.error('Failed to connect:', err);
    process.exit(1);
  }

  const contexts = browser.contexts();
  const page = contexts[0].pages().find(p => p.url().includes('larkoffice.com/base'));
  if (!page) {
    console.log('Lark page not found in contexts.');
    await browser.close();
    return;
  }

  console.log(`Connected. Page URL: ${page.url()}`);
  console.log(`Page Title: ${await page.title()}`);

  await page.waitForTimeout(5000);
  const bodyText = await page.innerText('body');
  console.log('--- Body Text ---');
  console.log(bodyText.substring(0, 1000));
  console.log('-----------------');

  // List all tab/sheet names
  const tabNames = await page.$$eval('[class*="tab-"]', els => {
    return els.map(el => el.innerText.trim()).filter(Boolean);
  });
  console.log('Tabs/Sheets found:', tabNames);

  // List column headers
  const headers = await page.$$eval('.grid-header-cell, [class*="header-cell"], [class*="column-header"]', els => {
    return els.map(el => el.innerText.trim()).filter(Boolean);
  });
  console.log('Column Headers found (unique):', [...new Set(headers)]);

  // Let's count rows
  const rowCount = await page.locator('.grid-row, [class*="row-wrapper"]').count();
  console.log(`Row elements count: ${rowCount}`);

  await browser.close();
}

run().catch(console.error);
