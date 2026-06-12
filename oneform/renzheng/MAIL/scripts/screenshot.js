const { chromium } = require('playwright');
const path = require('path');

const CDP_ENDPOINT = process.env.MAIL_CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP_ENDPOINT);
  try {
    const context = browser.contexts()[0];
    if (!context) throw new Error('No context found');
    const page = context.pages().find((p) => p.url().includes('starshot.scilliance.com')) || context.pages()[0];
    if (!page) throw new Error('No page found');

    const screenshotPath = path.resolve(__dirname, '../runs/current-screenshot.png');
    await page.screenshot({ path: screenshotPath });
    console.log(`Screenshot saved to ${screenshotPath}`);
  } finally {
    await browser.close();
  }
}

// Wrap main execution in a 15s absolute timeout to prevent indefinite hangs
Promise.race([
  main(),
  new Promise((_, reject) => setTimeout(() => reject(new Error('SCREENSHOT_TIMEOUT_LIMIT_REACHED')), 15000))
]).catch((error) => {
  console.error(`[FATAL_TIMEOUT] Screenshot script timed out or failed: ${error.stack || error.message}`);
  process.exit(1);
});
