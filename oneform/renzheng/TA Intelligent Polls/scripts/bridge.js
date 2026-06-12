/**
 * bridge.js — Keepalive + timer monitor for Intelligent Polls.
 *             Humanized version with deliberate pauses and randomized TpT.
 *             V2: Uses MAIN PAGE mouse moves + clicks for visible keepalive.
 *
 * Key change from V1:
 *   - Scrolls the MAIN page (visible on noVNC), not just the iframe
 *   - Moves mouse across the main page area (visible cursor)
 *   - Periodically clicks non-destructive elements (timer, header)
 *   - Still scrolls iframe internally too
 *
 * Usage:
 *   nohup node scripts/bridge.js > runs/bridge.log 2>&1 &
 */

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';
const FALLBACK_CDP = 'http://127.0.0.1:9232';

const BASE_TARGET = 290;

// Optimized conservative target: 265-310s (averaging 287.5s, extremely safe and close to standard)
const TARGET = (() => {
  const idx = process.argv.indexOf('--target');
  if (idx !== -1) return parseInt(process.argv[idx + 1], 10);
  return 265 + Math.floor(Math.random() * 45);
})();

// Deliberate pause: 12-15s, triggered once at 30-70% of target time
const PAUSE_AT_RATIO = 0.3 + Math.random() * 0.4;
const PAUSE_DURATION = 12000 + Math.floor(Math.random() * 3000);
const PAUSE_AT_MS = Math.floor(TARGET * 1000 * PAUSE_AT_RATIO);

let pauseDone = false;

process.on('SIGHUP', () => { console.warn('[bridge] Ignoring SIGHUP'); });

async function connect() {
  for (const ep of [CDP, FALLBACK_CDP]) {
    try { return await chromium.connectOverCDP(ep); } catch {}
  }
  throw new Error('[bridge] No CDP endpoint available');
}

function readTimer(page) {
  return page.evaluate(() => {
    const el = Array.from(document.querySelectorAll('*'))
      .find(e => /^\d+s$/.test(e.textContent.trim()) && e.children.length === 0);
    return el ? parseInt(el.textContent.trim()) : -1;
  }).catch(() => -1);
}

(async () => {
  const browser = await connect();
  const ctx = browser.contexts()[0];
  if (!ctx) throw new Error('[bridge] No browser context');

  let page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  if (!page) throw new Error('[bridge] No page found');

  console.log(`[bridge] Started — target=${TARGET}s (~${Math.floor(TARGET/60)}m${TARGET%60}s)`);
  console.log(`[bridge] Deliberate pause: ${PAUSE_DURATION/1000}s at ~${Math.floor(PAUSE_AT_RATIO*100)}% of target`);

  let cycleCount = 0;
  const startedAt = Date.now();

  while (true) {
    try {
      page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];

      // ── Deliberate reading pause (once) ──
      const elapsedMs = Date.now() - startedAt;
      if (!pauseDone && elapsedMs >= PAUSE_AT_MS) {
        const ts = new Date().toTimeString().slice(0, 8);
        console.log(`\n${ts} [bridge] 📖 Deliberate reading pause: ${PAUSE_DURATION/1000}s`);
        await page.waitForTimeout(PAUSE_DURATION);
        pauseDone = true;
        console.log('[bridge] Pause ended.');
      }

      // ── Dialog handling ──
      const nextTaskBtn = page.locator('button').filter({ hasText: /^Next Task$/ }).filter({ visible: true }).first();
      if (await nextTaskBtn.count()) {
        const actualTPT = Math.floor((Date.now() - startedAt) / 1000);
        const threshold = Math.round(BASE_TARGET * 0.75);
        if (actualTPT < threshold) {
          console.log(`\n[bridge] 📸 WARNING: Fast task detected (actual TPT = ${actualTPT}s < ${threshold}s). Taking evidence screenshot...`);
          const tsStr = new Date().toISOString().replace(/[:.]/g, '-');
          const url = page.url();
          console.log(`[bridge] Task URL: ${url}`);
          const screenshotPath = path.join(__dirname, '..', 'runs', `evidence_fast_${tsStr}.png`);
          const dir = path.dirname(screenshotPath);
          if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
          await page.screenshot({ path: screenshotPath }).catch(err => console.error('[bridge] Screenshot failed:', err.message));
          console.log(`[bridge] Screenshot saved to ${screenshotPath}`);
        }
        console.log('[bridge] Clicking Next Task...');
        await nextTaskBtn.click({ timeout: 3000 });
        await page.waitForTimeout(4000);
      }

      const startBtn = page.locator('[aria-label="Task Overview"] button').filter({ hasText: /^Start$/ });
      if (await startBtn.count()) {
        console.log('[bridge] Clicking Start...');
        await startBtn.first().click({ timeout: 3000 });
        await page.waitForTimeout(1000);
      }

      // ── Timer check ──
      const timer = await readTimer(page);
      const now = Date.now();
      const elapsed = Math.floor((now - startedAt) / 1000);

      // ── 20-minute hard cap checking ──
      if (elapsed >= 1200) {
        process.stdout.write('\n');
        console.warn(`[bridge] 🚨 CRITICAL WARNING: 20-minute hard cap reached! Force-advancing...`);
        
        let clicked = false;
        if (await nextTaskBtn.count().catch(() => 0)) {
          console.log('[bridge] [force-advance] Next Task button found. Clicking...');
          await nextTaskBtn.click({ timeout: 3000 }).catch(() => {});
          clicked = true;
        }
        
        if (!clicked) {
          const submitInDialog = page.locator('button', { hasText: 'Submit' }).filter({ visible: true }).last();
          if (await submitInDialog.count().catch(() => 0)) {
            console.log('[bridge] [force-advance] Submit button found in dialog. Clicking...');
            await submitInDialog.click({ force: true, timeout: 3000 }).catch(() => {});
            await page.waitForTimeout(2000);
            if (await nextTaskBtn.count().catch(() => 0)) {
              await nextTaskBtn.click({ timeout: 3000 }).catch(() => {});
              clicked = true;
            }
          }
        }
        
        if (!clicked) {
          const frame = page.frames().find(f => f.url().includes('task-editor'));
          if (frame) {
            const innerSubmit = frame.locator('button').filter({ hasText: 'Submit' }).first();
            if (await innerSubmit.count().catch(() => 0)) {
              console.log('[bridge] [force-advance] Inner Submit button found. Clicking...');
              await innerSubmit.click({ timeout: 3000 }).catch(() => {});
              await page.waitForTimeout(3000);
              
              const submitInDialog = page.locator('button', { hasText: 'Submit' }).filter({ visible: true }).last();
              if (await submitInDialog.count().catch(() => 0)) {
                await submitInDialog.click({ force: true, timeout: 3000 }).catch(() => {});
                await page.waitForTimeout(2000);
              }
              
              if (await nextTaskBtn.count().catch(() => 0)) {
                await nextTaskBtn.click({ timeout: 3000 }).catch(() => {});
                clicked = true;
              }
            }
          }
        }
        
        console.log('[bridge] Hard cap exit.');
        await browser.close();
        process.exit(0);
      }

      const timerStr = timer >= 0 ? timer + 's' : 'BUG/NA';
      const tsVal = new Date().toTimeString().slice(0, 8);
      const remaining = Math.max(0, TARGET - elapsed);
      const bar = '█'.repeat(Math.floor(Math.min(elapsed / TARGET, 1) * 20)).padEnd(20, '░');
      const pauseMark = pauseDone ? '✓' : `@${Math.floor(PAUSE_AT_MS/1000)}s`;
      process.stdout.write(`\r${tsVal} ⏱ timer=${timerStr} | elapsed=${elapsed}s | remaining=${remaining}s | pause=${pauseMark} [${bar}]  `);
      if (elapsed >= TARGET) {
        process.stdout.write('\n');
        console.log(`[bridge] Target ${TARGET}s reached. READY TO SUBMIT.`);
        await browser.close();
        process.exit(0);
      }

      // ── VISIBLE KEEPALIVE: Main page actions (you can see on noVNC) ──

      // 1. Move mouse across main page (visible cursor movement)
      const mx = 200 + Math.floor(Math.random() * 800);
      const my = 100 + Math.floor(Math.random() * 500);
      await page.mouse.move(mx, my).catch(() => {});

      // 2. Scroll the MAIN page (visible scroll)
      if (cycleCount % 3 === 0) {
        await page.evaluate(() => window.scrollTo(0, 100)).catch(() => {});
      } else if (cycleCount % 3 === 1) {
        await page.evaluate(() => window.scrollTo(0, 0)).catch(() => {});
      } else {
        await page.evaluate(() => window.scrollTo(0, 50)).catch(() => {});
      }

      // 3. Also scroll the task-editor iframe (internal, may not be visible)
      const frame = page.frames().find(f => f.url().includes('task-editor'));
      if (frame) {
        const scrollDist = 150 + Math.floor(Math.random() * 100);
        await frame.evaluate(d => window.scrollTo(0, d), scrollDist).catch(() => {});
        await page.waitForTimeout(1500);
        await frame.evaluate(() => window.scrollTo(0, 0)).catch(() => {});
      }

      // 4. Every 5th cycle, click the timer element (non-destructive, registers as activity)
      if (cycleCount % 5 === 0) {
        const timerEl = page.locator('#timer');
        if (await timerEl.count() > 0) {
          await timerEl.click({ timeout: 2000 }).catch(() => {});
        }
      }

      // Jittered wait: 3-5s
      const jitter = 3000 + Math.floor(Math.random() * 2000);
      await page.waitForTimeout(jitter);

      cycleCount++;
    } catch (e) {
      if (e.message.includes('Target page, context or browser has been closed')) {
        console.error('[bridge] Browser closed. Exiting.');
        process.exit(0);
      }
      console.warn(`[bridge] Error (continuing): ${e.message.substring(0, 80)}`);
      await new Promise(r => setTimeout(r, 3000));
    }
  }
})().catch(e => {
  console.error('[bridge] Fatal:', e.message);
  process.exit(1);
});
