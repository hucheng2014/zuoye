const { chromium } = require('playwright');
const path = require('path');

async function run() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9237');
  const page = browser.contexts()[0].pages()[0];
  await page.setViewportSize({ width: 1200, height: 1000 });

  await page.waitForTimeout(5000);
  
  const imgPath = '/Users/xaa/.gemini/antigravity-cli/brain/6ffe4535-d43d-47de-bd8b-27434df1d17f/scratch/port_9237_next_loaded.png';
  await page.screenshot({ path: imgPath });
  console.log('Saved screenshot of next task to:', imgPath);
  
  const leftText = await page.locator("div[class*='captionBlock']").first().innerText().catch(() => 'N/A');
  console.log('--- Left text after reload ---');
  console.log(leftText);
  console.log('------------------------------');

  await browser.close();
}

run().catch(console.error);
