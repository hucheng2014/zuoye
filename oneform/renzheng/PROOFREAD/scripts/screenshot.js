require('./_timeout');
const { chromium } = require('playwright');
const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot') || p.url().includes('apple')) || ctx.pages()[0];

  await page.screenshot({ path: 'PROOFREAD/runs/task-002-screenshot.png', fullPage: false });
  console.log('Screenshot saved to PROOFREAD/runs/task-002-screenshot.png');

  // Also check frame content
  const frame = page.frames().find(f => f.url().includes('task-editor'));
  if (frame) {
    const text = await frame.locator('body').innerText({ timeout: 2000 }).catch(() => '');
    const hasInput = text.includes('Input (original text)');
    const hasResponses = text.includes('Response A');
    const hasPairwise = text.includes('Pairwise Comparison');
    const completion = text.match(/(\d+\/\d+) Complete/g);
    console.log({ hasInput, hasResponses, hasPairwise, completion });
    console.log('Frame text preview:', text.slice(0, 500));
  } else {
    console.log('No task-editor frame found');
  }

  await browser.close();
}

main().catch(e => { console.error(e.message); process.exit(1); });
