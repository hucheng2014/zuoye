const { chromium } = require('playwright');

async function run() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9237');
  const page = browser.contexts()[0].pages()[0];
  await page.setViewportSize({ width: 1200, height: 1000 });

  // Check if Chinese radio is checked
  const radio = page.locator('input[type="radio"][value="中文"]').first();
  console.log('Is Chinese radio checked currently?', await radio.isChecked());

  // Let's click it
  console.log('Clicking Chinese radio...');
  await radio.click({ force: true });
  await page.waitForTimeout(1000);
  console.log('Is Chinese radio checked now?', await radio.isChecked());

  // Click Submit
  console.log('Clicking Submit Task...');
  await page.locator('button:has-text("提交任务")').first().click();
  await page.waitForTimeout(5000);

  // Take screenshot
  const imgPath = '/Users/xaa/.gemini/antigravity-cli/brain/6ffe4535-d43d-47de-bd8b-27434df1d17f/scratch/port_9237_after_third_submit.png';
  await page.screenshot({ path: imgPath });
  console.log('Saved screenshot to:', imgPath);
  console.log('URL after submit:', page.url());

  await browser.close();
}

run().catch(console.error);
