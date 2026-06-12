const { chromium } = require('playwright');
const path = require('path');

async function run() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9237');
  const page = browser.contexts()[0].pages()[0];
  await page.setViewportSize({ width: 1200, height: 1000 });

  // Click "编辑" tab
  console.log('Clicking "编辑" tab...');
  await page.locator('div:text("编辑")').first().click();
  await page.waitForTimeout(1000);

  // Print textarea value
  const val = await page.locator('textarea').first().inputValue();
  console.log('--- Current Textarea Value ---');
  console.log(val);
  console.log('------------------------------');

  const imgPath = '/Users/xaa/.gemini/antigravity-cli/brain/6ffe4535-d43d-47de-bd8b-27434df1d17f/scratch/port_9237_edit_tab.png';
  await page.screenshot({ path: imgPath });
  console.log('Saved screenshot to:', imgPath);
  await browser.close();
}

run().catch(console.error);
