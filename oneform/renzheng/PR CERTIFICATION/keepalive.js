/**
 * PR Certification keepalive — scroll/mouse activity to prevent Inactive timer.
 * Runs for SUBMIT_AT_SEC (default 720s = 12 min), then writes ready.flag.
 *
 * Usage: nohup node keepalive.js >> runs/keepalive.log 2>&1 &
 * Kill before fill/submit: kill $(cat runs/keepalive.pid)
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { SUBMIT_AT_SEC, CDP_URL, CDP_FALLBACK } = require('./config');

const RUNS = path.resolve(__dirname, 'runs');
const LOG_FILE = path.join(RUNS, 'keepalive.log');
const PID_FILE = path.join(RUNS, 'keepalive.pid');
const READY_FILE = path.join(RUNS, 'ready.flag');

let running = true;
let consecutiveErrors = 0;
const MAX_ERRORS = 20;

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  process.stdout.write(line);
  fs.appendFileSync(LOG_FILE, line, { flag: 'a' });
}

async function connect() {
  for (const ep of [CDP_URL, CDP_FALLBACK]) {
    try {
      const browser = await chromium.connectOverCDP(ep);
      log(`Connected to CDP: ${ep}`);
      return browser;
    } catch (e) {
      log(`CDP ${ep} failed: ${e.message}`);
    }
  }
  throw new Error('No CDP endpoint available');
}

function acquireLock() {
  if (fs.existsSync(PID_FILE)) {
    const old = parseInt(fs.readFileSync(PID_FILE, 'utf8').trim(), 10);
    if (old && old !== process.pid) {
      try {
        process.kill(old, 0);
        log(`Another keepalive alive (pid ${old}) — exiting.`);
        process.exit(0);
      } catch {
        log(`Stale pid ${old} — taking over.`);
      }
    }
  }
  fs.writeFileSync(PID_FILE, String(process.pid));
}

async function main() {
  fs.mkdirSync(RUNS, { recursive: true });
  acquireLock();
  try { fs.unlinkSync(READY_FILE); } catch {}
  log(`Keepalive started pid=${process.pid} (target ${SUBMIT_AT_SEC}s / ${SUBMIT_AT_SEC / 60} min)`);

  const startedAt = Date.now();
  let browser = await connect();
  const ctx = browser.contexts()[0];
  let page = ctx.pages().find((p) => p.url().includes('starshot')) || ctx.pages()[0];
  if (!page) throw new Error('No starshot page found');

  await page.setViewportSize({ width: 1919, height: 1079 }).catch(() => {});
  let taskFrame = page.frames().find((f) => f.url().includes('task-editor')) || page;

  let cycle = 0;
  while (running) {
    const elapsed = Math.floor((Date.now() - startedAt) / 1000);
    try {
      page = ctx.pages().find((p) => p.url().includes('starshot')) || ctx.pages()[0];
      taskFrame = page.frames().find((f) => f.url().includes('task-editor')) || page;

      const x = 400 + Math.floor(Math.random() * 300);
      const y = 300 + Math.floor(Math.random() * 300);
      await page.mouse.move(x, y).catch(() => {});
      await page.evaluate(() => {
        window.scrollBy(0, 12);
        setTimeout(() => window.scrollBy(0, -12), 100);
      }).catch(() => {});
      await taskFrame.evaluate(() => window.scrollBy(0, 10)).catch(() => {});

      consecutiveErrors = 0;
      fs.writeFileSync(PID_FILE, String(process.pid));

      const pageTpt = await page.evaluate(() => {
        const parse = (text) => {
          const m = String(text).match(/(?:time worked[:\s]*)?(\d+)\s*(?:seconds?|s)?/i);
          return m ? parseInt(m[1], 10) : -1;
        };
        for (const el of document.querySelectorAll('button,[role=button],[aria-label]')) {
          const blob = `${el.textContent || ''} ${el.getAttribute('aria-label') || ''}`;
          if (/time worked/i.test(blob)) {
            const v = parse(blob);
            if (v >= 0) return v;
          }
        }
        return parse(document.body?.innerText || '');
      }).catch(() => -1);

      if (cycle % 4 === 0) {
        log(`Cycle ${cycle}: elapsed=${elapsed}s pageTPT=${pageTpt}s / ${SUBMIT_AT_SEC}s`);
      }

      if (pageTpt >= SUBMIT_AT_SEC || elapsed >= SUBMIT_AT_SEC) {
        fs.writeFileSync(READY_FILE, new Date().toISOString());
        log(`Target ${SUBMIT_AT_SEC}s reached — ready.flag written. Exiting for submit.`);
        break;
      }

      cycle++;
      const pageTpt2 = pageTpt >= 0 ? pageTpt : elapsed;
      const pollMs = pageTpt2 >= SUBMIT_AT_SEC - 30 ? 3000 : 15000;
      await new Promise((r) => setTimeout(r, pollMs));
    } catch (e) {
      consecutiveErrors++;
      log(`ERROR (${consecutiveErrors}/${MAX_ERRORS}): ${e.message}`);
      if (consecutiveErrors >= MAX_ERRORS) {
        log('Too many consecutive errors — exiting for watchdog restart.');
        break;
      }
      try {
        if (browser) await browser.close().catch(() => {});
        await new Promise((r) => setTimeout(r, 3000));
        browser = await connect();
        const newCtx = browser.contexts()[0];
        page = newCtx.pages().find((p) => p.url().includes('starshot')) || newCtx.pages()[0];
        taskFrame = page.frames().find((f) => f.url().includes('task-editor')) || page;
        log('Reconnected.');
      } catch (reconErr) {
        log(`Reconnect failed: ${reconErr.message}`);
      }
    }
  }

  log('Keepalive stopped.');
  try { fs.unlinkSync(PID_FILE); } catch {}
  if (browser) await browser.close().catch(() => {});
}

process.on('SIGINT', () => { running = false; });
process.on('SIGTERM', () => { running = false; });

main().catch((e) => {
  log(`FATAL: ${e.message}`);
  process.exit(1);
});
