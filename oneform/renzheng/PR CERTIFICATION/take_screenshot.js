const puppeteer = require('puppeteer-core');
const fs = require('fs');

const CDP_URL = 'http://127.0.0.1:9235';

async function main() {
  const browser = await puppeteer.connect({
    browserURL: CDP_URL,
    defaultViewport: null
  });

  const pages = await browser.pages();
  const page = pages[0];

  // Capture full page screenshot
  await page.screenshot({ path: '/tmp/after_submit_debug.png', fullPage: true });
  console.log('Screenshot captured to /tmp/after_submit_debug.png');

  // Copy to artifacts
  const dest = '/Users/xaa/.gemini/antigravity-cli/brain/6eb974fe-56c3-46da-9b96-0d715d692209/after_submit_debug.png';
  fs.copyFileSync('/tmp/after_submit_debug.png', dest);
  console.log('Copied to artifacts');

  await browser.disconnect();
}

main().catch(console.error);
