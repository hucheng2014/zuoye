const puppeteer = require('puppeteer-core');
const fs = require('fs');

const CDP_URL = 'http://127.0.0.1:9235';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  const browser = await puppeteer.connect({
    browserURL: CDP_URL,
    defaultViewport: null
  });

  const pages = await browser.pages();
  const page = pages[0];
  const frames = page.frames();
  const frm1 = frames.find(f => f.url().includes('task-editor'));

  if (!frm1) {
    console.error('Task editor frame not found');
    await browser.disconnect();
    return;
  }

  // Click Response B tab
  console.log('Clicking Response B tab...');
  await frm1.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll('[role="tab"], button'));
    const tab = tabs.find(t => t.textContent.includes('Response B'));
    if (tab) tab.click();
  });

  await sleep(1000);

  // Take screenshot
  await page.screenshot({ path: '/tmp/after_submit_debug.png', fullPage: true });
  console.log('Screenshot of Response B captured to /tmp/after_submit_debug.png');

  // Copy to artifacts
  const dest = '/Users/xaa/.gemini/antigravity-cli/brain/6eb974fe-56c3-46da-9b96-0d715d692209/after_submit_debug.png';
  fs.copyFileSync('/tmp/after_submit_debug.png', dest);

  await browser.disconnect();
}

main().catch(console.error);
