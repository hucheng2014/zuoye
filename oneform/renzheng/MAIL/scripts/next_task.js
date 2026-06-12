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
    if (!context) throw new Error('No browser context found');
    const page = context.pages().find((p) => p.url().includes('starshot.scilliance.com')) || context.pages()[0];
    if (!page) throw new Error('No page found');

    const checkbox = page.locator('label:has-text("Do not ask for confirmation again") input[type="checkbox"]').first();
    if (await checkbox.count()) {
      const visible = await checkbox.isVisible().catch(() => false);
      if (visible) await checkbox.check({ force: true });
      else {
        const label = page.locator('label', { hasText: 'Do not ask for confirmation again' }).first();
        if (await label.count()) await label.click({ force: true });
      }
    }

    const next = page.locator('button', { hasText: 'Next Task' }).first();
    if (!(await next.count())) throw new Error('Next Task button not found');
    await next.click({ timeout: 5000 });
    await page.waitForTimeout(2500);

    const body = await page.locator('body').innerText({ timeout: 3000 }).catch((error) => error.message);
    console.log(JSON.stringify({ cdpEndpoint: endpoint, body: body.slice(0, 1000) }, null, 2));
  } finally {
    await browser.close();
  }
}

// Wrap main execution in a 30s absolute timeout to prevent indefinite hangs
Promise.race([
  main(),
  new Promise((_, reject) => setTimeout(() => reject(new Error('NEXT_TASK_TIMEOUT_LIMIT_REACHED')), 30000))
]).catch((error) => {
  console.error(`[FATAL_TIMEOUT] Next task script timed out or failed: ${error.stack || error.message}`);
  process.exit(1);
});
