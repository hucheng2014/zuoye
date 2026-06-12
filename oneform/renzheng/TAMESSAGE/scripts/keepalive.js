
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { submitAndNext, readTimer } = require('./submit_task');

const CDP_URL = 'http://127.0.0.1:9233';
const { SUBMIT_AT_SEC: SUBMIT_AT } = require('./config');
const RUNS = path.resolve(__dirname, '..', 'runs');
const LOG_FILE = path.join(RUNS, 'keepalive.log');
const PID_FILE = path.join(RUNS, 'keepalive.pid');

let running = true;

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  process.stdout.write(line);
  fs.appendFileSync(LOG_FILE, line, { flag: 'a' });
}

async function keepalive() {
  fs.mkdirSync(RUNS, { recursive: true });
  log(`Keepalive started (TPT target ${SUBMIT_AT}s).`);
  fs.writeFileSync(PID_FILE, String(process.pid));

  let browser;
  try {
    browser = await chromium.connectOverCDP(CDP_URL);
    log(`Connected to CDP: ${CDP_URL}`);
  } catch (e) {
    log(`FATAL: CDP connect failed: ${e.message}`);
    process.exit(1);
  }

  const context = browser.contexts()[0];
  if (!context) { log('FATAL: No context'); process.exit(1); }

  let page = context.pages().find((p) => p.url().includes('starshot')) || context.pages()[0];
  if (!page) { log('FATAL: No starshot page'); process.exit(1); }

  await page.setViewportSize({ width: 1919, height: 1079 }).catch(() => {});
  let taskFrame = page.frames().find((f) => f.url().includes('/task-editor/')) || page;
  log('Task editor frame located.');

  let cycle = 0;
  while (running) {
    try {
      const x = 400 + Math.floor(Math.random() * 300);
      const y = 300 + Math.floor(Math.random() * 300);
      await page.mouse.move(x, y).catch(() => {});
      await page.evaluate(() => {
        window.scrollBy(0, 10);
        setTimeout(() => window.scrollBy(0, -10), 100);
      }).catch(() => {});
      await taskFrame.evaluate(() => window.scrollBy(0, 10)).catch(() => {});

      const timerSec = await readTimer(page);
      if (cycle % 4 === 0) {
        const bodyText = await taskFrame.innerText('body', { timeout: 2000 }).catch(() => '');
        const hasTask = /Response A|Response B|Pairwise/i.test(bodyText);
        log(`Cycle ${cycle}: TPT=${timerSec}s/${SUBMIT_AT}s task=${hasTask}`);
      }

      if (timerSec >= SUBMIT_AT) {
        log(`TPT ${timerSec}s >= ${SUBMIT_AT}s — submitting + Next Task`);
        running = false;
        const result = await submitAndNext(page, taskFrame, { logger: log, clickNext: true });
        fs.writeFileSync(path.join(RUNS, 'submitted.flag'), new Date().toISOString());
        log(`Submit done: submitted=${result.submitted} nextTask=${result.nextTask}`);
        break;
      }

      cycle++;
      await new Promise((r) => setTimeout(r, 15000));
    } catch (e) {
      log(`ERROR: ${e.message}`);
      try {
        if (browser) await browser.close().catch(() => {});
        browser = await chromium.connectOverCDP(CDP_URL);
        const ctx = browser.contexts()[0];
        page = ctx.pages().find((p) => p.url().includes('starshot')) || ctx.pages()[0];
        taskFrame = page.frames().find((f) => f.url().includes('/task-editor/')) || page;
        log('Reconnected.');
      } catch (reconErr) {
        log(`FATAL reconnect: ${reconErr.message}`);
        running = false;
      }
    }
  }

  log('Keepalive stopped.');
  try { fs.unlinkSync(PID_FILE); } catch {}
  if (browser) await browser.close().catch(() => {});
}

process.on('SIGINT', () => { running = false; });
process.on('SIGTERM', () => { running = false; });

keepalive().catch((e) => {
  log(`FATAL: ${e.message}`);
  process.exit(1);
});
