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
    console.log('Lark page not found.');
    await browser.close();
    return;
  }

  console.log('Lark page found. Waiting for table to load...');
  await page.waitForTimeout(5000);

  // Let's dump all column headers first
  const headers = await page.$$eval('.grid-header-cell-text, [class*="header-cell-text"], .header-cell-text-content, [class*="header-cell"]', els => {
    return els.map(el => el.innerText.trim()).filter(Boolean);
  });
  console.log('Column Headers:', [...new Set(headers)]);

  // Let's dump the text content of the visible grid cells to see what data lies there
  const cellTexts = await page.$$eval('.grid-cell, [class*="cell-content"], [role="gridcell"]', els => {
    return els.slice(0, 100).map(el => el.innerText.trim()).filter(Boolean);
  });
  console.log('First 100 Cell Texts:', cellTexts);

  await browser.close();
}

run().catch(console.error);
