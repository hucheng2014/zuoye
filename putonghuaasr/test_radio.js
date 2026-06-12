const { chromium } = require('playwright');

async function run() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9237');
  const page = browser.contexts()[0].pages()[0];

  // Try direct click on the radio input
  console.log('Method 1: Direct click on input[type="radio"][value="中文"]');
  try {
    const radio = page.locator('input[type="radio"][value="中文"]').first();
    await radio.click({ force: true });
    await page.waitForTimeout(500);
    const checked = await radio.isChecked();
    console.log('  Checked after Method 1:', checked);
  } catch (err) {
    console.error('  Method 1 failed:', err);
  }

  // If not checked, try clicking the label text span
  const radio = page.locator('input[type="radio"][value="中文"]').first();
  if (!(await radio.isChecked())) {
    console.log('Method 2: Click on the span/text next to it');
    try {
      // Find the label or parent wrapper and click it
      const parent = page.locator('label:has(input[type="radio"][value="中文"])').first();
      if (await parent.count() > 0) {
        await parent.click();
        await page.waitForTimeout(500);
        console.log('  Checked after Method 2:', await radio.isChecked());
      }
    } catch (err) {
      console.error('  Method 2 failed:', err);
    }
  }

  // If still not checked, try checking the label list items or custom classes
  if (!(await radio.isChecked())) {
    console.log('Method 3: Locate Ant Design radio wrapper');
    try {
      const antRadio = page.locator('.ant-radio-wrapper, .ant-radio, .ant-v5-radio-wrapper').filter({ has: page.locator('input[value="中文"]') }).first();
      if (await antRadio.count() > 0) {
        await antRadio.click();
        await page.waitForTimeout(500);
        console.log('  Checked after Method 3:', await radio.isChecked());
      }
    } catch (err) {
      console.error('  Method 3 failed:', err);
    }
  }

  await browser.close();
}

run().catch(console.error);
