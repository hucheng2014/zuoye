const { chromium } = require('playwright');
const path = require('path');

async function run() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9237');
  const page = browser.contexts()[0].pages()[0];
  await page.setViewportSize({ width: 1200, height: 1000 });
  const imgPath = '/Users/xaa/.gemini/antigravity-cli/brain/6ffe4535-d43d-47de-bd8b-27434df1d17f/scratch/port_9237_filled.png';
  await page.screenshot({ path: imgPath });
  console.log('Saved screenshot to:', imgPath);
  await browser.close();
}

run().catch(console.error);
