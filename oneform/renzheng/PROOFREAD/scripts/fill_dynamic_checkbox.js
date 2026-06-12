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
  const frame = page.frames().find(f => f.url().includes('task-editor'));
  
  // Click Response A tab
  const tabA = frame.locator('button[role="tab"]:has-text("Response A")').first();
  await tabA.click();
  await page.waitForTimeout(1000);
  
  // Scroll to bottom multiple times
  await frame.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(500);
  await frame.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(500);
  
  // Find and check "formatting" checkbox
  const formattingCheckbox = frame.locator('input[type="checkbox"][value="formatting"]');
  const count = await formattingCheckbox.count();
  console.log(`Found ${count} formatting checkboxes`);
  
  if (count > 0) {
    // Check the last one (the dynamic group)
    const lastCheckbox = formattingCheckbox.last();
    await lastCheckbox.check({ force: true });
    console.log('Checked formatting checkbox');
  }
  
  await browser.close();
}

main().catch(console.error);
