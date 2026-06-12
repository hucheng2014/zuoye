const { chromium } = require('playwright');
const path = require('path');

async function run() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9237');
  const page = browser.contexts()[0].pages()[0];
  await page.setViewportSize({ width: 1200, height: 1000 });

  console.log('Clicking "提交任务" button...');
  try {
    const btn = page.locator('button:has-text("提交任务")').first();
    await btn.click();
    console.log('Clicked "提交任务"!');
    
    // Wait a few seconds to see if a dialog pops up or if page transitions
    await page.waitForTimeout(3000);
    
    const imgPath = '/Users/xaa/.gemini/antigravity-cli/brain/6ffe4535-d43d-47de-bd8b-27434df1d17f/scratch/port_9237_after_submit.png';
    await page.screenshot({ path: imgPath });
    console.log('Saved screenshot to:', imgPath);
    console.log('Current URL after submit click:', page.url());
  } catch (err) {
    console.error('Click failed:', err);
  }

  await browser.close();
}

run().catch(console.error);
