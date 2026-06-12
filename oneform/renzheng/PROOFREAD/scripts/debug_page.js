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
  
  // Check for any dialog
  const dialogText = await page.evaluate(() => {
    const dialogs = Array.from(document.querySelectorAll('[role="dialog"]'));
    return dialogs.map(d => ({
      label: d.getAttribute('aria-label'),
      text: d.textContent.slice(0, 200)
    }));
  });
  
  console.log('Dialogs found:', JSON.stringify(dialogText, null, 2));
  
  // Try to find any button with "Next" or "Task"
  const buttons = await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    return btns.map(b => ({
      text: b.textContent.trim(),
      visible: b.offsetParent !== null
    })).filter(b => b.text.includes('Next') || b.text.includes('Task'));
  });
  
  console.log('Buttons with Next/Task:', JSON.stringify(buttons, null, 2));
  
  await browser.close();
}

main().catch(console.error);
