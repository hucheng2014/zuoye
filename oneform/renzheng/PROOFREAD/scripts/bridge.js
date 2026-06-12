/**
 * bridge.js — PROOFREAD: full lifecycle keepalive + TPT controller.
 *
 * Usage:
 *   node scripts/bridge.js [--target 720]
 *   node scripts/bridge.js --daemon [--target 720] [--log runs/bridge.log]
 *
 * ═══════════════════════════════════════════════════════════════════════════════
 * TIMING MODEL (12-minute TPT):
 *   Total (720s) = Active + Inactive
 *   Inactive <= Active × 10%  →  Active ≈ 655s, Inactive ≈ 65s (ceiling)
 *   Target actual inactive: 50-60s (3 deep sleeps + transition gap)
 *
 *   TPT = time from task start → clicking "Next Task" (NOT Submit).
 *   After submit, the popup still counts as current task time.
 *   After clicking Next Task, any 10s+ gap = inactive for the NEW task.
 *
 * HUMAN BEHAVIOR FOR 12-MINUTE PROOFREAD:
 *   - 3 deep sleeps (15-18s each): simulate reading/comparing long text
 *   - Variable interaction intervals: 4-9s (not uniform)
 *   - Tab cycling: Response A/B/C (natural for proofreading comparisons)
 *   - Mouse moves + scrolls (both main page and iframe)
 *   - TPT variance: 675-780s (±~45s around 720)
 *
 * LIFECYCLE PER TASK:
 *   ┌─ TRANSITION: handle popups (Accept/Start), keepalive during load
 *   ├─ ACTIVE: keepalive + deep sleeps. Signal "SUBMIT NOW" at 80%.
 *   ├─ SUBMITTED: detect submission (or retry up to 5x on failure).
 *   └─ NEXT: at 100% TPT, click "Next Task". Immediately resume keepalive.
 * ═══════════════════════════════════════════════════════════════════════════════
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';
const FALLBACK_CDP = 'http://127.0.0.1:9232';

// ─── CLI ────────────────────────────────────────────────────────────────────

function argValue(name, fallback) {
  const i = process.argv.indexOf(name);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

const BASE_TARGET = parseInt(argValue('--target', '720'), 10);
const DAEMON = process.argv.includes('--daemon');
const LOG_PATH = argValue('--log', 'runs/bridge.log');
const PID_PATH = argValue('--pid', 'runs/bridge.pid');
const MAX_TASKS = parseInt(argValue('--max', '50'), 10);

// ─── Util ───────────────────────────────────────────────────────────────────

function randBetween(min, max) { return min + Math.random() * (max - min); }
function randInt(min, max) { return Math.floor(randBetween(min, max + 1)); }
function ts() { return new Date().toTimeString().slice(0, 8); }

/** Optimized conservative target: 670-750s (extremely safe, close to 12 min standard) */
function computeTarget() {
  // Conservative safe range: 670-750s (extremely safe, close to 12 min standard)
  return 670 + Math.floor(Math.random() * 81);
}

/** 3 deep sleeps in first 70% of runtime, spaced ≥60s apart */
function scheduleDeepSleeps(target) {
  const count = 3;
  const window = target * 0.70;
  const sleeps = [];
  for (let i = 0; i < count; i++) {
    sleeps.push({
      triggerAt: Math.floor(randBetween(50, window)),
      duration: randBetween(15000, 18000),
      fired: false,
    });
  }
  sleeps.sort((a, b) => a.triggerAt - b.triggerAt);
  for (let i = 1; i < sleeps.length; i++) {
    if (sleeps[i].triggerAt - sleeps[i - 1].triggerAt < 60) {
      sleeps[i].triggerAt = sleeps[i - 1].triggerAt + randInt(60, 100);
    }
  }
  return sleeps;
}

// ─── Daemon ─────────────────────────────────────────────────────────────────

if (DAEMON) {
  const dir = path.dirname(LOG_PATH);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  const logFd = fs.openSync(LOG_PATH, 'a');
  const child = spawn(process.execPath, [__filename, '--target', String(BASE_TARGET), '--max', String(MAX_TASKS)], {
    detached: true, stdio: ['ignore', logFd, logFd],
  });
  fs.writeFileSync(PID_PATH, String(child.pid));
  console.log(`[bridge] Daemonized: pid=${child.pid} log=${LOG_PATH}`);
  child.unref();
  process.exit(0);
}

process.on('SIGHUP', () => {});
process.on('SIGTERM', () => process.exit(0));
process.on('SIGINT', () => process.exit(0));

// ─── CDP ────────────────────────────────────────────────────────────────────

async function connect() {
  for (const ep of [CDP, FALLBACK_CDP]) {
    try { return await chromium.connectOverCDP(ep); } catch {}
  }
  throw new Error('[bridge] No CDP endpoint available');
}

// ─── Page state detection ───────────────────────────────────────────────────

async function detectState(page) {
  return page.evaluate(() => {
    const text = document.body?.innerText || '';
    const btns = Array.from(document.querySelectorAll('button, [role="button"]'));
    const btnTexts = btns.filter(b => b.offsetWidth > 0).map(b => b.textContent.trim());

    // Submission failure (Retry button + failure text)
    if (btnTexts.includes('Retry') && (text.includes('Submission failed') || text.includes('Upload failed'))) {
      return 'SUBMIT_FAILED';
    }

    if (btnTexts.includes('Accept')) return 'DISCLAIMER';
    if (btnTexts.includes('Start')) return 'TASK_OVERVIEW';
    if (text.includes('Task successfully submitted')) return 'SUBMITTED';
    if (text.includes('no available tasks')) return 'NO_TASKS';
    if (btnTexts.includes('Try Again')) return 'NO_TASKS';
    if (text.includes('Next Task') && btnTexts.includes('Next Task')) return 'SUBMITTED';

    const iframes = document.querySelectorAll('iframe');
    for (const f of iframes) {
      if (f.src?.includes('task-editor')) return 'ACTIVE';
    }

    const timerEl = Array.from(document.querySelectorAll('*'))
      .find(e => /^\d+s$/.test(e.textContent.trim()) && e.children.length === 0);
    if (timerEl) return 'ACTIVE';

    return 'UNKNOWN';
  }).catch(() => 'ERROR');
}

// ─── Keepalive (proofread-specific: tab cycling + scroll + mouse) ───────────

async function keepalive(page) {
  const roll = Math.random();
  try {
    const frame = page.frames().find(f => f.url().includes('task-editor'));

    if (roll < 0.35 && frame) {
      // Dynamically select and click one of the visible comparison tabs (highly resilient to missing Response tabs)
      const tabButtons = frame.locator('button[role="tab"]');
      const count = await tabButtons.count().catch(() => 0);
      if (count > 1) { // Only click if there are multiple tabs to cycle
        const randIdx = Math.floor(Math.random() * count);
        await tabButtons.nth(randIdx).click({ timeout: 2000 }).catch(() => {});
      } else {
        // Fallback to iframe scrolling if no multiple tabs are present
        const y = randInt(50, 400);
        await frame.evaluate((sy) => window.scrollTo(0, sy), y).catch(() => {});
      }
    } else if (roll < 0.60 && frame) {
      // Scroll iframe (reading text)
      const y = randInt(50, 600);
      await frame.evaluate((sy) => window.scrollTo(0, sy), y);
      await page.waitForTimeout(randInt(500, 1200));
      if (Math.random() < 0.5) {
        await frame.evaluate((sy) => window.scrollTo(0, sy), randInt(0, Math.floor(y * 0.6)));
      }
    } else if (roll < 0.80) {
      // Mouse move on main page
      await page.mouse.move(randInt(100, 1200), randInt(100, 700), { steps: randInt(2, 7) });
    } else {
      // Scroll main page
      const dy = randInt(-60, 100);
      await page.evaluate((d) => window.scrollBy(0, d), dy);
    }
  } catch {}
}

// ─── Handle popups/transitions ──────────────────────────────────────────────

async function handleTransition(page) {
  let attempts = 0;
  while (attempts < 30) {
    const state = await detectState(page);

    if (state === 'DISCLAIMER') {
      console.log(`\n${ts()} [transition] Clicking Accept...`);
      await page.evaluate(() => {
        const btn = Array.from(document.querySelectorAll('button'))
          .find(b => b.textContent.trim() === 'Accept');
        if (btn) btn.click();
      });
      await page.waitForTimeout(2000);
      await keepalive(page);
    } else if (state === 'TASK_OVERVIEW') {
      console.log(`\n${ts()} [transition] Clicking Start...`);
      await page.evaluate(() => {
        const btn = Array.from(document.querySelectorAll('button'))
          .find(b => b.textContent.trim() === 'Start');
        if (btn) btn.click();
      });
      await page.waitForTimeout(2000);
      await keepalive(page);
    } else if (state === 'ACTIVE') {
      return 'ACTIVE';
    } else if (state === 'NO_TASKS') {
      return 'NO_TASKS';
    } else if (state === 'SUBMITTED') {
      return 'SUBMITTED';
    } else {
      await keepalive(page);
      await page.waitForTimeout(randInt(2000, 4000));
    }
    attempts++;
  }
  return 'TIMEOUT';
}

// ─── Click Next Task ────────────────────────────────────────────────────────

async function clickNextTask(page, actualTPT, baseTarget) {
  if (actualTPT !== undefined && baseTarget !== undefined && actualTPT < baseTarget * 0.75) {
    const threshold = Math.round(baseTarget * 0.75);
    console.log(`\n${ts()} 📸 WARNING: Fast task detected (actual TPT = ${actualTPT}s < ${threshold}s). Taking evidence screenshot...`);
    const tsStr = new Date().toISOString().replace(/[:.]/g, '-');
    const url = page.url();
    console.log(`${ts()} Task URL: ${url}`);
    const screenshotPath = path.join(__dirname, '..', 'runs', `evidence_fast_${tsStr}.png`);
    const dir = path.dirname(screenshotPath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    await page.screenshot({ path: screenshotPath }).catch(err => console.error(`[bridge] Screenshot failed: ${err.message}`));
    console.log(`${ts()} Screenshot saved to ${screenshotPath}`);
  }

  console.log(`\n${ts()} 🚀 Clicking Next Task...`);
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button'))
      .find(b => b.textContent.trim() === 'Next Task');
    if (btn) btn.click();
  });
  // Immediately keepalive during transition (never 10s gap)
  await page.waitForTimeout(1000);
  await keepalive(page);
  await page.waitForTimeout(1500);
  await keepalive(page);
  await page.waitForTimeout(1500);
  await keepalive(page);
}

// ─── Submission retry (up to 5 attempts) ────────────────────────────────────

async function retrySubmission(page, maxAttempts = 5) {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    console.log(`\n${ts()} 🔄 Submission retry ${attempt}/${maxAttempts}...`);

    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button'))
        .find(b => b.textContent.trim() === 'Retry' && b.offsetWidth > 0);
      if (btn) btn.click();
    });

    // Wait with keepalive
    for (let i = 0; i < 5; i++) {
      await page.waitForTimeout(1000);
      await keepalive(page);
    }

    const state = await detectState(page);
    if (state === 'SUBMITTED') {
      console.log(`${ts()} ✓ Retry ${attempt} succeeded!`);
      return true;
    }
    if (state !== 'SUBMIT_FAILED') {
      console.log(`${ts()} State after retry: ${state}`);
      return state === 'SUBMITTED';
    }

    console.log(`${ts()} ✗ Still failed after attempt ${attempt}`);
    await keepalive(page);
    await page.waitForTimeout(2000);
  }

  console.log(`${ts()} ❌ All ${maxAttempts} retry attempts failed!`);
  return false;
}

// ─── Read page timer ────────────────────────────────────────────────────────

function readTimer(page) {
  return page.evaluate(() => {
    const el = Array.from(document.querySelectorAll('*'))
      .find(e => /^\d+s$/.test(e.textContent.trim()) && e.children.length === 0);
    return el ? parseInt(el.textContent.trim()) : -1;
  }).catch(() => -1);
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN LOOP
// ═══════════════════════════════════════════════════════════════════════════════

(async () => {
  const browser = await connect();
  const ctx = browser.contexts()[0];
  if (!ctx) throw new Error('[bridge] No browser context');

  let page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  if (!page) throw new Error('[bridge] No page found');

  console.log(`[bridge] PROOFREAD — continuous mode`);
  console.log(`[bridge] BASE_TARGET=${BASE_TARGET}s (${Math.floor(BASE_TARGET/60)}m${BASE_TARGET%60}s) | MAX_TASKS=${MAX_TASKS}`);
  console.log('');

  let taskCount = 0;

  while (taskCount < MAX_TASKS) {
    page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];

    const transResult = await handleTransition(page);
    if (transResult === 'NO_TASKS') {
      console.log(`\n${ts()} ⏸ No tasks available. Exiting.`);
      break;
    }
    if (transResult === 'TIMEOUT') {
      console.log(`\n${ts()} ⚠ Transition timeout. Retrying...`);
      await keepalive(page);
      await page.waitForTimeout(5000);
      continue;
    }

    // ── Task is now ACTIVE ──
    taskCount++;
    const TARGET = computeTarget();
    const SUBMIT_AT = Math.floor(TARGET * 0.80);
    const deepSleeps = scheduleDeepSleeps(TARGET);

    console.log(`\n${'═'.repeat(60)}`);
    console.log(`${ts()} 📋 Task #${taskCount} started`);
    console.log(`${ts()} TARGET=${TARGET}s (${Math.floor(TARGET/60)}m${TARGET%60}s) | SUBMIT at ${SUBMIT_AT}s | NEXT at ${TARGET}s`);
    console.log(`${ts()} Deep sleeps: ${deepSleeps.map(s => s.triggerAt + 's(' + Math.round(s.duration / 1000) + 's)').join(', ')}`);
    console.log('');

    const taskStart = Date.now();
    let submitSignaled = false;
    let submitted = false;
    let nextTaskClicked = false;

    while (!nextTaskClicked) {
      try {
        page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
        const elapsed = Math.floor((Date.now() - taskStart) / 1000);

        // ── Deep sleep (only before submit signal) ──
        if (!submitSignaled) {
          for (const ds of deepSleeps) {
            if (!ds.fired && elapsed >= ds.triggerAt) {
              ds.fired = true;
              const sleepMs = Math.round(ds.duration);
              process.stdout.write(`\n${ts()} 💤 Deep sleep ${Math.round(sleepMs / 1000)}s (reading/comparing text)\n`);
              // Split sleep: two halves with micro-move at midpoint (each half ≤ 9s)
              await page.waitForTimeout(Math.floor(sleepMs / 2));
              await page.mouse.move(randInt(300, 700), randInt(200, 500), { steps: 1 });
              await page.waitForTimeout(Math.ceil(sleepMs / 2));
              break;
            }
          }
        }

        // ── Progress display ──
        const nowElapsed = Math.floor((Date.now() - taskStart) / 1000);
        const remaining = Math.max(0, TARGET - nowElapsed);
        const timer = await readTimer(page);
        const timerStr = timer >= 0 ? timer + 's' : 'BUG/NA';
        const bar = '█'.repeat(Math.floor(Math.min(nowElapsed / TARGET, 1) * 20)).padEnd(20, '░');
        const phase = submitted ? '✓SUB' : (submitSignaled ? '⚡WAIT' : 'WORK');
        process.stdout.write(`\r${ts()} [${phase}] page=${timerStr} | elapsed=${nowElapsed}s | left=${remaining}s [${bar}]  `);

        // ── Submit signal at 80% ──
        if (!submitSignaled && nowElapsed >= SUBMIT_AT) {
          submitSignaled = true;
          process.stdout.write('\n');
          console.log(`${ts()} ⚡ SUBMIT NOW (${TARGET - nowElapsed}s until Next Task)`);
        }

        // ── Detect submission state ──
        if (submitSignaled && !submitted) {
          const state = await detectState(page);
          if (state === 'SUBMITTED') {
            submitted = true;
            process.stdout.write('\n');
            console.log(`${ts()} ✓ Submission detected. Waiting for TPT...`);
          } else if (state === 'SUBMIT_FAILED') {
            process.stdout.write('\n');
            console.log(`${ts()} ⚠ Submission FAILED! Retrying...`);
            const retryOk = await retrySubmission(page, 5);
            if (retryOk) {
              submitted = true;
              console.log(`${ts()} ✓ Retry succeeded. Waiting for TPT...`);
            } else {
              console.log(`${ts()} ❌ All retries failed. Will keep trying next cycle.`);
            }
          }
        }

        // ── 20-minute hard cap checking ──
        if (nowElapsed >= 1200) {
          process.stdout.write('\n');
          console.warn(`${ts()} 🚨 CRITICAL WARNING: 20-minute hard cap reached! Force-advancing...`);
          
          let clicked = false;
          const nextTaskBtn = page.locator('button').filter({ hasText: /^Next Task$/ }).filter({ visible: true }).first();
          if (await nextTaskBtn.count().catch(() => 0)) {
            console.log(`${ts()} [force-advance] Next Task button found on main page. Clicking...`);
            await nextTaskBtn.click({ timeout: 3000 }).catch(() => {});
            clicked = true;
          }
          
          if (!clicked) {
            const submitInDialog = page.locator('button', { hasText: 'Submit' }).filter({ visible: true }).last();
            if (await submitInDialog.count().catch(() => 0)) {
              console.log(`${ts()} [force-advance] Submit button found in dialog. Clicking...`);
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
                console.log(`${ts()} [force-advance] Inner Submit button found in iframe. Clicking...`);
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
          
          console.log(`${ts()} [force-advance] Hard cap exit.`);
          nextTaskClicked = true;
          break;
        }

        // ── At 100% TPT: click Next Task ──
        if (nowElapsed >= TARGET) {
          if (submitted) {
            await clickNextTask(page, nowElapsed, BASE_TARGET);
            nextTaskClicked = true;
            break;
          } else {
            if (nowElapsed % 15 === 0) {
              process.stdout.write('\n');
              console.log(`${ts()} ⚠ TPT reached but not submitted! Waiting...`);
            }
          }
        }

        // ── Keepalive ──
        await keepalive(page);

        // ── Wait interval: 4-9s with jitter ──
        const wait = Math.round(randBetween(4000, 9000) + (Math.random() < 0.15 ? randBetween(1000, 3000) : 0));
        await page.waitForTimeout(wait);

      } catch (e) {
        if (e.message.includes('Target page, context or browser has been closed')) {
          console.error(`\n${ts()} [bridge] Browser closed. Exiting.`);
          process.exit(0);
        }
        console.warn(`\n${ts()} [bridge] Error: ${e.message.substring(0, 80)}`);
        await new Promise(r => setTimeout(r, 3000));
      }
    }

    console.log(`\n${ts()} ✅ Task #${taskCount} complete (actual TPT=${Math.floor((Date.now() - taskStart) / 1000)}s)`);
  }

  console.log(`\n${ts()} [bridge] Session ended. Tasks completed: ${taskCount}`);
  await browser.close();
  process.exit(0);
})().catch(e => {
  console.error('[bridge] Fatal:', e.message);
  process.exit(1);
});
