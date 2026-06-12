/**
 * starshot_keepalive.js — Dedicated keep-alive, active monitoring, and self-healing script for Starshot.
 *
 * Keeps the starshot session alive by:
 * 1. Performing minor, non-disruptive scroll movements every 30 seconds to prevent Chrome tab throttling.
 * 2. Clicks "Try Again" every 3 minutes if no tasks are available.
 * 3. Instantly reloads the page to silently re-login using OIDC cookies if "Session expired / Error 440" is detected.
 * 4. Implements absolute 30-second watchdog timeout for each cycle, restarting container controlled-browser-browser on deadlock.
 * 5. Self-terminates on persistent deadlocks to actively alert upstream agents/users.
 * 6. Triggers audio alerts (beep sound + terminal bell + native speech/play commands) on any non-active time or system failure.
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const CDP_ENDPOINTS = [
  process.env.MAIL_CDP_ENDPOINT || 'http://127.0.0.1:9233',
  'http://127.0.0.1:9232',
];

const LOG_FILE = process.env.MAIL_LOG_FILE || path.resolve(__dirname, '..', 'runs', 'keepalive.log');

function log(msg) {
  const ts = new Date().toISOString();
  const line = `[${ts}] ${msg}\n`;
  process.stdout.write(line);
  try {
    fs.appendFileSync(LOG_FILE, line);
  } catch {}
}

function beep(count = 1) {
  // 1. Send ANSI Bell character to trigger terminal alarm sound/visual flash
  for (let i = 0; i < count; i++) {
    process.stdout.write('\x07');
  }
  // 2. Try native system alerts on Linux (spd-say speech or aplay sound clip)
  try {
    const { exec } = require('child_process');
    exec('spd-say "Warning, system inactive" || aplay /usr/share/sounds/alsa/Front_Center.wav', (err) => {});
  } catch {}
}

function restartBrowserContainer() {
  log('[FATAL] Watchdog triggered! Attempting to restart docker container: controlled-browser-browser...');
  try {
    execSync('docker restart controlled-browser-browser', { stdio: 'inherit' });
    log('Docker container controlled-browser-browser restarted successfully.');
  } catch (err) {
    log(`[ERROR] Failed to restart Docker container: ${err.message}`);
  }
}

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

let running = true;
process.on('SIGINT', () => { running = false; });
process.on('SIGTERM', () => { running = false; });

async function runLoop() {
  let browser = null;
  let lastTryAgainTime = 0;
  let cycle = 0;
  let consecutiveTimeouts = 0;

  while (running) {
    // (Re)connect if browser is not alive
    if (!browser || !browser.isConnected()) {
      try {
        if (browser) await browser.close().catch(() => {});
        const result = await connect();
        browser = result.browser;
        log(`Connected to CDP endpoint: ${result.endpoint}`);
        cycle = 0;
      } catch (err) {
        beep(3);
        log(`Warning: Could not connect to CDP (${err.message}). Retrying in 15s...`);
        await new Promise((r) => setTimeout(r, 15000));
        continue;
      }
    }

    try {
      // Execute the keep-alive cycle with a 30s absolute watchdog timeout
      const stepPromise = (async () => {
        const context = browser.contexts()[0];
        if (!context) {
          beep(2);
          log('Warning: No browser context. Reconnecting...');
          browser = null;
          return;
        }

        const page = context.pages().find((p) => p.url().includes('starshot.scilliance.com')) || context.pages()[0];
        if (!page) {
          beep(2);
          log('Warning: No starshot page found. Sleeping for 15s...');
          await new Promise((resolve) => setTimeout(resolve, 15000));
          return;
        }

        // 0. Time limit check: 6.5 hours since session start
        const startFile = process.env.MAIL_START_FILE || path.resolve(__dirname, '..', 'runs', 'session_start_time.txt');
        if (fs.existsSync(startFile)) {
          const startStr = fs.readFileSync(startFile, 'utf8').trim();
          const startTime = new Date(startStr).getTime();
          const elapsedMs = Date.now() - startTime;
          const limitMs = 6.5 * 3600 * 1000; // 6.5 hours
          if (elapsedMs >= limitMs) {
            log(`🛑 Session elapsed time reached 6.5 hours limit (${(elapsedMs / 3600000).toFixed(2)}h). Closing Annotation Tool page...`);
            await page.close().catch(() => {});
            running = false;
            return;
          }
        }

        // Check current page body text
        const body = await page.locator('body').innerText({ timeout: 2000 }).catch(() => '');

        // 1. Self-healing: Detect Session Expired
        if (/Session expired|Error: 440/i.test(body)) {
          beep(5);
          log('🚨 [INACTIVE] Session expired detected! Reloading page...');
          await page.reload().catch(() => {});
          await new Promise((r) => setTimeout(r, 6000));
          log('Page reloaded. Session should be silently restored.');
          return;
        }

        // 2. Click "Try Again" every 3 minutes if no tasks are available
        // SAFETY: Never click Try Again if a task is in-flight (Done button visible = task active)
        const now = Date.now();
        const taskInFlight = /there are no available tasks/i.test(body) === false &&
                             (/Response A|Response B|Pairwise/i.test(body));
        
        const isNoTasks = /there are no available tasks/i.test(body);
        // Match timer "0s" only as standalone token, not inside "10s","20s" etc.
        const isBlankWaiting = /Mail Smart Reply/i.test(body) && /(?<!\d)0s(?!\d)/.test(body) && !taskInFlight;

        if ((isNoTasks || isBlankWaiting) && !taskInFlight) {
          // BEEP: We are in non-active time!
          beep(2);
          log(`🚨 [INACTIVE] Non-active time detected! (No tasks / Loading 0s). Beeping...`);

          if (isNoTasks && (now - lastTryAgainTime > 180000 || lastTryAgainTime === 0)) {
            log('🔍 Clicking "Try Again" to check for tasks and keep session fresh...');
            const tryAgainBtn = page.locator('button', { hasText: 'Try Again' }).first();
            if (await tryAgainBtn.count() > 0 && await tryAgainBtn.isVisible()) {
              await tryAgainBtn.click({ timeout: 1000 }).catch(() => {});
              lastTryAgainTime = now;
              await new Promise((r) => setTimeout(r, 3000));
            }
          }
        } else if (taskInFlight) {
          // Task in progress — just log occasionally, never click Try Again
          if (cycle % 10 === 0) log('📝 Task in progress, skipping Try Again.');
        }

        // 3. Prevent tab throttling: subtle scroll every 30s
        if (cycle % 2 === 0) {
          await page.evaluate(() => {
            window.scrollBy(0, 10);
            setTimeout(() => window.scrollBy(0, -10), 100);
          }).catch(() => {});
        }

        // Tiny mouse movement every 60s
        if (cycle % 4 === 0) {
          const x = 500 + Math.floor(Math.random() * 200);
          const y = 400 + Math.floor(Math.random() * 200);
          await page.mouse.move(x, y).catch(() => {});
        }

        cycle++;
      })();

      // Watchdog timeout Promise (30s)
      const timeoutPromise = new Promise((_, reject) => {
        const timer = setTimeout(() => reject(new Error('KEEPALIVE_CYCLE_TIMEOUT')), 30000);
        stepPromise.finally(() => clearTimeout(timer)).catch(() => {});
      });

      await Promise.race([stepPromise, timeoutPromise]);
      consecutiveTimeouts = 0; // Reset consecutive timeouts count on success

      if (running) {
        await new Promise((r) => setTimeout(r, 15000));
      }

    } catch (error) {
      if (!running) break;
      const msg = error.message || '';

      if (msg === 'KEEPALIVE_CYCLE_TIMEOUT') {
        consecutiveTimeouts++;
        beep(10);
        log(`[FATAL] Keepalive cycle timeout (30s absolute limit reached). Consecutive timeouts: ${consecutiveTimeouts}. Beeping...`);
        
        // Sever old browser connection
        if (browser) {
          await browser.close().catch(() => {});
          browser = null;
        }

        // Action: restart docker container to unlock chrome
        restartBrowserContainer();

        if (consecutiveTimeouts >= 3) {
          log(`[FATAL] Persistent deadlocks detected. Container restarted ${consecutiveTimeouts} times but still failing. Terminating process to alert user!`);
          process.exit(1);
        }

        // Cool down for 15s before starting the next connection attempt
        await new Promise((r) => setTimeout(r, 15000));

      } else if (/browser has been closed|context or browser has been closed|Target closed/i.test(msg)) {
        beep(4);
        log(`Warning: Browser/context closed unexpectedly. Will reconnect... (${msg.slice(0, 80)})`);
        browser = null;
        await new Promise((r) => setTimeout(r, 3000));
      } else {
        beep(3);
        log(`Warning: Error in cycle: ${msg.slice(0, 120)}`);
        await new Promise((r) => setTimeout(r, 5000));
      }
    }
  }

  log('Starshot Keepalive script stopped gracefully.');
  if (browser) await browser.close().catch(() => {});
}

async function main() {
  fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
  log('Starting Starshot Keepalive script...');
  await runLoop();
}

main().catch((error) => {
  log(`Fatal error: ${error.stack || error.message}`);
  process.exit(1);
});
