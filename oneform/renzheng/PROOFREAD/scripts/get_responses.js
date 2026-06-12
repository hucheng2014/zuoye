require('./_timeout');
const { chromium } = require('playwright');
const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

function clean(t) { return (t || '').replace(/ /g, ' ').replace(/[ \t]+\n/g, '\n').trim(); }

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];

  // Get all srcdoc frames with full text
  const frames = page.frames().filter(f => f.url() === 'about:srcdoc');
  const result = {};

  for (let i = 0; i < frames.length; i++) {
    const text = clean(await frames[i].locator('body').innerText({ timeout: 800 }).catch(() => ''));
    if (!text) continue;

    // Identify frame content type
    if (text.startsWith('Response A (')) result[`pairA_${i}`] = text.slice(0, 200);
    else if (text.startsWith('Response B (')) result[`pairB_${i}`] = text.slice(0, 200);
    else if (text.startsWith('Response C (')) result[`pairC_${i}`] = text.slice(0, 200);
    else if (text.startsWith('Proposed edits')) result[`diff_${i}`] = text.slice(0, 500);
    else if (text.includes('Dimension') && text.includes('Correctness')) result[`score_${i}`] = text.slice(0, 200);
    else if (text.includes('Necessary edits')) result[`legend_${i}`] = 'legend';
    else if (text.length > 50) result[`content_${i}`] = text.slice(0, 300);
  }

  // Now click each response tab to get clean response text
  const taskFrame = page.frames().find(f => f.url().includes('task-editor'));
  for (const tabName of ['Response A', 'Response B', 'Response C']) {
    const tab = taskFrame.locator(`button[role="tab"]`).filter({ hasText: tabName });
    if (await tab.count()) {
      await tab.first().click({ timeout: 3000 });
      await page.waitForTimeout(500);
      // Take screenshot for each tab
      await page.screenshot({ path: `PROOFREAD/runs/task-002-${tabName.replace(' ', '')}.png` });
    }
  }

  console.log(JSON.stringify(result, null, 2));
  await browser.close();
}

main().catch(e => { console.error(e.message); process.exit(1); });
