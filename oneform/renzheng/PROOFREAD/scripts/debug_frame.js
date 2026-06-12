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
  
  console.log('Page URL:', page.url());
  
  const frames = page.frames();
  console.log('Frames:', frames.map(f => ({ url: f.url(), name: f.name() })));
  
  const frame = frames.find(f => f.url().includes('task-editor'));
  if (frame) {
    const bodyText = await frame.locator('body').innerText().catch(() => 'Failed to get text');
    console.log('Frame body text (first 500 chars):', bodyText.slice(0, 500));
  } else {
    console.log('task-editor frame not found');
  }
  
  await browser.close();
}

main().catch(console.error);
