require('./_timeout');
const { chromium } = require('playwright');

const CDP_ENDPOINTS = [
  process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233',
  'http://127.0.0.1:9232',
];

async function connect() {
  for (const ep of CDP_ENDPOINTS) {
    try { return { browser: await chromium.connectOverCDP(ep), endpoint: ep }; } catch {}
  }
  throw new Error('No CDP endpoint available');
}

async function main() {
  const { browser } = await connect();
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  
  // Click Next Task button
  const nextTaskBtn = page.locator('button:has-text("Next Task")');
  const count = await nextTaskBtn.count();
  if (count > 0) {
    await nextTaskBtn.first().click();
    console.log('Clicked Next Task button');
    await page.waitForTimeout(2000);
  } else {
    console.log('Next Task button not found');
  }
  
  await browser.close();
}

main().catch(console.error);
