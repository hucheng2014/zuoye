/**
 * extract_task.js — Extract current Intelligent Polls task data from the browser.
 *
 * Connects via CDP, reads the task-editor iframe and srcdoc iframe to extract:
 *   - prompt (conversation text)
 *   - locale
 *   - outputs (poll title + options)
 *   - current form state (checked radios)
 *
 * Usage:
 *   node scripts/extract_task.js > runs/task-NNN-task.json
 */

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

function extractJsonFromCreateTaskAPI(html) {
  const idx = html.indexOf('createTaskAPI(');
  if (idx < 0) throw new Error('createTaskAPI not found');
  const comma = html.indexOf(',', idx);
  if (comma < 0) throw new Error('comma not found');
  let start = html.indexOf('{', comma);
  if (start < 0) throw new Error('json start not found');
  let depth = 0, inStr = false, esc = false;
  for (let i = start; i < html.length; i++) {
    const ch = html[i];
    if (inStr) { if (esc) esc = false; else if (ch === '\\') esc = true; else if (ch === '"') inStr = false; }
    else { if (ch === '"') inStr = true; else if (ch === '{') depth++; else if (ch === '}') { depth--; if (depth === 0) return html.slice(start, i + 1); } }
  }
  throw new Error('json end not found');
}

async function main() {
  const { browser, endpoint } = await connect();
  try {
    const ctx = browser.contexts()[0];
    if (!ctx) throw new Error('No browser context');
    const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
    if (!page) throw new Error('No page');

    // Dismiss Task Overview dialog if present
    const dialog = page.locator('[aria-label="Task Overview"]');
    if (await dialog.count() > 0) {
      const startBtn = dialog.locator('button:has-text("Start")');
      if (await startBtn.count() > 0) {
        console.log('[extract] Dismissing Task Overview dialog...');
        await startBtn.first().click({ timeout: 3000 });
        await page.waitForTimeout(1000);
      }
    }

    const taskFrame = page.frames().find(f => f.url().includes('task-editor'));
    if (!taskFrame) throw new Error('task-editor frame not found');

    await page.waitForTimeout(500);

    // Extract task data from srcdoc iframe via createTaskAPI
    let taskData = null;
    const srcdocFrames = page.frames().filter(f => f.url() === 'about:srcdoc');
    for (const sf of srcdocFrames) {
      const html = await sf.content().catch(() => '');
      if (html.includes('createTaskAPI(')) {
        try {
          taskData = JSON.parse(extractJsonFromCreateTaskAPI(html));
          break;
        } catch (e) {
          console.error('[extract] Failed to parse createTaskAPI JSON:', e.message);
        }
      }
    }

    // Get form text for locale and question structure
    const formText = await taskFrame.locator('body').innerText({ timeout: 2000 }).catch(() => '');
    const localeMatch = formText.match(/Locale:\s*(\S+)/);

    // Get current radio state
    const checkedRadios = await taskFrame.locator('input:checked').evaluateAll(els =>
      els.map(e => ({ type: e.type, name: e.name, value: e.value }))
    ).catch(() => []);

    // Get all radio options for reference
    const allRadios = await taskFrame.locator('input[type="radio"]').evaluateAll(els =>
      els.map((el, i) => ({
        i, name: el.name, value: el.value,
        label: (el.closest('label')?.innerText || '').trim().slice(0, 120),
        checked: el.checked,
      }))
    ).catch(() => []);

    // Get timer from main page
    const timer = await page.evaluate(() => {
      const el = Array.from(document.querySelectorAll('*'))
        .find(e => /^\d+s$/.test(e.textContent.trim()) && e.children.length === 0);
      return el ? parseInt(el.textContent.trim()) : -1;
    }).catch(() => -1);

    const output = {
      extractedAt: new Date().toISOString(),
      cdpEndpoint: endpoint,
      pageUrl: page.url(),
      timer,
      locale: localeMatch ? localeMatch[1] : (taskData?.locale || 'unknown'),
      prompt: taskData?.prompt || '',
      outputs: taskData?.outputs || [],
      num_output: taskData?.num_output || 0,
      eval_set_item_id: taskData?.eval_set_item_id || '',
      query_id: taskData?.query_id || '',
      result_id: taskData?.result_id || '',
      checkedRadios,
      allRadios,
      formTextPreview: formText.slice(0, 3000),
    };

    console.log(JSON.stringify(output, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch(e => { console.error(e.stack || e.message); process.exit(1); });
