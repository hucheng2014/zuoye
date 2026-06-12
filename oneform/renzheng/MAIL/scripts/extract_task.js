const { chromium } = require('playwright');

const CDP_ENDPOINTS = [
  process.env.MAIL_CDP_ENDPOINT || 'http://127.0.0.1:9233',
  'http://127.0.0.1:9232',
];

async function connect() {
  let lastError;
  for (const endpoint of CDP_ENDPOINTS) {
    if (!endpoint) continue;
    try {
      const browser = await chromium.connectOverCDP(endpoint);
      return { browser, endpoint };
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError || new Error('No CDP endpoint available');
}

function cleanText(text) {
  return (text || '').replace(/\u00a0/g, ' ').replace(/[ \t]+\n/g, '\n').trim();
}

async function main() {
  const { browser, endpoint } = await connect();
  try {
    const context = browser.contexts()[0];
    if (!context) throw new Error('No browser context found');
    const page = context.pages().find((p) => p.url().includes('starshot.scilliance.com')) || context.pages()[0];
    if (!page) throw new Error('No page found');

    page.setDefaultTimeout(1000);
    await page.waitForLoadState('domcontentloaded', { timeout: 1000 }).catch(() => {});
    await page.waitForTimeout(150);

    const frames = [];
    const pageFrames = page.frames();
    const taskEditorFrame = pageFrames.find((frame) => frame.url().includes('/task-editor/'));
    const selectedFrames = taskEditorFrame
      ? [page.mainFrame(), taskEditorFrame, ...pageFrames.filter((frame) => frame !== page.mainFrame() && frame !== taskEditorFrame && frame.url() === 'about:srcdoc')]
      : pageFrames;
    for (const frame of selectedFrames) {
      const index = pageFrames.indexOf(frame);
      let text = '';
      let controls = [];
      try {
        text = cleanText(await frame.locator('body').innerText({ timeout: 500 }));
      } catch {}
      try {
        controls = await frame.locator('input, textarea, button, select').evaluateAll((elements) =>
          elements.map((el, controlIndex) => ({
            controlIndex,
            tag: el.tagName,
            type: el.getAttribute('type'),
            role: el.getAttribute('role'),
            name: el.getAttribute('name'),
            value: el.value || '',
            checked: Boolean(el.checked),
            ariaLabel: el.getAttribute('aria-label'),
            text: (el.innerText || el.textContent || '').trim(),
          }))
        , { timeout: 500 });
      } catch {}
      frames.push({ index, url: frame.url(), text, controls });
    }

    const taskFrame = frames.find((frame) => frame.text.includes('Prompt') && frame.text.includes('Response A'));
    const output = {
      extractedAt: new Date().toISOString(),
      cdpEndpoint: endpoint,
      page: {
        title: await page.title(),
        url: page.url(),
      },
      taskText: taskFrame ? taskFrame.text : '',
      frames,
    };
    console.log(JSON.stringify(output, null, 2));
  } finally {
    await browser.close();
  }
}

// Wrap main execution in a 20s absolute timeout to prevent indefinite hangs
Promise.race([
  main(),
  new Promise((_, reject) => setTimeout(() => reject(new Error('EXTRACT_TASK_TIMEOUT_LIMIT_REACHED')), 20000))
]).catch((error) => {
  console.error(`[FATAL_TIMEOUT] Extract task script timed out or failed: ${error.stack || error.message}`);
  process.exit(1);
});
