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

async function main() {
  const { browser, endpoint } = await connect();
  try {
    const context = browser.contexts()[0];
    const page = context.pages().find((p) => p.url().includes('starshot.scilliance.com')) || context.pages()[0];
    page.setDefaultTimeout(750);
    const body = await page.locator('body').innerText({ timeout: 750 }).catch((error) => error.message);
    const buttons = await page.locator('button').evaluateAll((elements) =>
      elements.map((el, index) => {
        const rect = el.getBoundingClientRect();
        return {
          index,
          text: (el.innerText || el.textContent || '').trim(),
          ariaLabel: el.getAttribute('aria-label'),
          disabled: Boolean(el.disabled),
          visible: Boolean(rect.width || rect.height || el.getClientRects().length),
        };
      })
    ).catch(() => []);
    console.log(JSON.stringify({ cdpEndpoint: endpoint, body: body.slice(0, 1200), buttons }, null, 2));
  } finally {
    await browser.close();
  }
}

// Wrap main execution in a 10s absolute timeout to prevent indefinite hangs
Promise.race([
  main(),
  new Promise((_, reject) => setTimeout(() => reject(new Error('QUICK_STATUS_TIMEOUT_LIMIT_REACHED')), 10000))
]).catch((error) => {
  console.error(`[FATAL_TIMEOUT] Quick status script timed out or failed: ${error.stack || error.message}`);
  process.exit(1);
});
