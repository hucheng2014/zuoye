/**
 * submit_task.js — Submit → confirm dialog → Next Task
 * Shared by fill_task.js and keepalive.js
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const CDP_ENDPOINTS = [
  process.env.TAMESSAGE_CDP_ENDPOINT || 'http://127.0.0.1:9233',
  'http://127.0.0.1:9232',
];
const RUNS = path.resolve(__dirname, '..', 'runs');

async function connect() {
  let lastError;
  for (const endpoint of CDP_ENDPOINTS) {
    try {
      const browser = await chromium.connectOverCDP(endpoint);
      return { browser, endpoint };
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError || new Error('No CDP endpoint available');
}

async function getTaskFrame(page) {
  for (const frame of page.frames()) {
    const text = await frame.locator('body').innerText({ timeout: 1000 }).catch(() => '');
    if (text.includes('Response A1') && text.includes('Pairwise Comparison')) return frame;
  }
  throw new Error('Task frame not found');
}

const { dismissPopups } = require('./dismiss_popups');

function log(msg, logger) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  if (logger) logger(msg);
  else console.log(line);
}

async function submitAndNext(page, frame, { logger, clickNext = true } = {}) {
  await dismissPopups(page, (m) => log(m, logger));
  log('Step 1: Click Submit in task editor', logger);
  await frame.getByText('Submit', { exact: true }).first().evaluate((el) => el.click());
  await page.waitForTimeout(1500);

  log('Step 2: Click Done (Submit Task) on main page', logger);
  const doneBtn = page.getByLabel('Submit Task');
  if (await doneBtn.count()) {
    const visible = await doneBtn.first().isVisible().catch(() => false);
    const disabled = await doneBtn.first().isDisabled().catch(() => true);
    if (visible && !disabled) {
      await doneBtn.first().click({ force: true }).catch(() => doneBtn.first().evaluate((el) => el.click()));
      await page.waitForTimeout(2000);
    }
  }

  log('Step 3: Confirm Submit in dialog', logger);
  for (let attempt = 0; attempt < 5; attempt++) {
    const confirmDialog = page.locator('div[role="dialog"]');
    if (await confirmDialog.count() > 0) {
      const submitBtn = confirmDialog.locator('button', { hasText: /^Submit$/i }).first();
      if (await submitBtn.isVisible().catch(() => false)) {
        await submitBtn.click({ timeout: 5000 });
        await page.waitForTimeout(3000);
        break;
      }
    }
    const pageSubmit = page.locator('button', { hasText: /^Submit$/i }).first();
    if (await pageSubmit.isVisible().catch(() => false)) {
      await pageSubmit.click({ timeout: 3000 }).catch(() => {});
      await page.waitForTimeout(3000);
      break;
    }
    await page.waitForTimeout(1000);
  }

  log('Step 4: Wait for submission result', logger);
  let submitted = false;
  for (let retry = 0; retry < 8; retry++) {
    const body = await page.locator('body').innerText({ timeout: 3000 }).catch(() => '');
    if (/Submission failed/i.test(body)) {
      log('Submission failed — clicking Retry', logger);
      const retryBtn = page.locator('button', { hasText: 'Retry' }).first();
      if (await retryBtn.isVisible().catch(() => false)) {
        await retryBtn.click({ timeout: 5000 }).catch(() => {});
        await page.waitForTimeout(8000);
      }
    } else if (/Task successfully submitted|successfully submitted/i.test(body)) {
      submitted = true;
      log('Task successfully submitted.', logger);
      break;
    } else if (/Next Task/i.test(body)) {
      submitted = true;
      log('Submit success (Next Task visible).', logger);
      break;
    } else {
      await page.waitForTimeout(2000);
    }
  }

  if (!submitted) {
    const body = await page.locator('body').innerText({ timeout: 2000 }).catch(() => '');
    log(`Submit uncertain. Page: ${body.slice(0, 200)}`, logger);
  }

  if (!clickNext) return { submitted, nextTask: false };

  log('Step 5: Click Next Task', logger);
  const checkbox = page.locator('label:has-text("Do not ask for confirmation again") input[type="checkbox"]').first();
  if (await checkbox.count()) {
    await checkbox.check({ force: true }).catch(() => {});
  }

  let nextTask = false;
  for (let attempt = 0; attempt < 5; attempt++) {
    const nextBtn = page.locator('button', { hasText: /Next Task/i }).first();
    if (await nextBtn.count() && await nextBtn.isVisible().catch(() => false)) {
      await nextBtn.click({ timeout: 5000 });
      await page.waitForTimeout(4000);
      nextTask = true;
      log('Clicked Next Task.', logger);
      break;
    }
    await page.waitForTimeout(2000);
  }

  if (nextTask) {
    for (let wait = 0; wait < 15; wait++) {
      await page.waitForTimeout(2000);
      const body = await page.locator('body').innerText({ timeout: 2000 }).catch(() => '');
      if (/Response A1|Response A|Pairwise/i.test(body)) {
        log('New task loaded.', logger);
        break;
      }
    }
    fs.mkdirSync(RUNS, { recursive: true });
    fs.writeFileSync(path.join(RUNS, 'new_task.ready'), new Date().toISOString());
    try { fs.unlinkSync(path.join(RUNS, 'submitted.flag')); } catch {}
  }

  return { submitted, nextTask };
}

async function main() {
  const clickNext = !process.argv.includes('--no-next');
  const { browser } = await connect();
  try {
    const context = browser.contexts()[0];
    const page = context.pages().find((p) => p.url().includes('starshot.scilliance.com')) || context.pages()[0];
    const frame = await getTaskFrame(page);
    const result = await submitAndNext(page, frame, { clickNext });
    console.log(JSON.stringify(result, null, 2));
    if (!result.submitted) process.exit(1);
  } finally {
    await browser.close();
  }
}

if (require.main === module) {
  main().catch((e) => {
    console.error(e.stack || e.message);
    process.exit(1);
  });
}

module.exports = { connect, getTaskFrame, submitAndNext, readTimer: async (page) => {
  const body = await page.locator('body').innerText({ timeout: 2000 }).catch(() => '');
  const m = body.match(/(\d+)s/);
  return m ? parseInt(m[1], 10) : 0;
}};
