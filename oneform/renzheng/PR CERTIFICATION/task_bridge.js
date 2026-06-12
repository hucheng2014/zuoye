/**
 * task_bridge.js — 单进程可靠闭环
 * 流程：extract → 判分 → fill+复检（<720s）→ 保活 → 720s 仅提交
 * 填表必须在 720s 前完成，到点只点 Submit，避免超时后填表失败时间一直走。
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { chromium } = require('playwright');
const { SUBMIT_AT_SEC, CDP_URL, CDP_FALLBACK } = require('./config');
const {
  RUNS,
  saveTask,
  loadTaskFile,
  ratingsReadyStrict,
  extractTaskFromPage,
  invalidateRatings,
  NEEDS_GRADING,
} = require('./task_utils');

const ROOT = __dirname;
const LOG_FILE = path.join(RUNS, 'bridge.log');
const PID_FILE = path.join(RUNS, 'bridge.pid');
const FORM_FILLED = path.join(RUNS, 'form_filled.flag');
const SUBMITTABLE = path.join(RUNS, 'submittable.flag');

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  process.stdout.write(line);
  fs.appendFileSync(LOG_FILE, line, { flag: 'a' });
}

async function connect() {
  for (const ep of [CDP_URL, CDP_FALLBACK]) {
    try { return await chromium.connectOverCDP(ep); } catch (e) { log(`CDP ${ep}: ${e.message}`); }
  }
  throw new Error('No CDP');
}

function getPage(browser) {
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find((p) => p.url().includes('starshot')) || ctx.pages()[0];
  const frm = page.frames().find((f) => f.url().includes('task-editor'));
  return { page, frm };
}

async function readPageTPT(page) {
  return page.evaluate(() => {
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
}

async function dismissBlockingDialogs(page) {
  const dismissed = await page.evaluate(() => {
    const visible = (el) => {
      if (!el) return false;
      const s = window.getComputedStyle(el);
      if (s.display === 'none' || s.visibility === 'hidden' || s.opacity === '0') return false;
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    };
    const body = document.body?.innerText || '';
    for (const el of document.querySelectorAll('button, [role="button"]')) {
      const t = (el.textContent || '').trim();
      if (/^accept$/i.test(t) && visible(el)) {
        const ctx = el.closest('dialog,[role=dialog],div')?.textContent || body;
        if (/disclaimer|terms|privacy|enroll/i.test(ctx)) {
          el.click();
          return 'Disclaimer Accept';
        }
      }
    }
    return null;
  }).catch(() => null);
  if (dismissed) {
    log(`Dismissed dialog: ${dismissed}`);
    await new Promise((r) => setTimeout(r, 1500));
  }
}

async function clickStartIfNeeded(page) {
  await dismissBlockingDialogs(page);
  for (let i = 0; i < 3; i++) {
    const clicked = await page.evaluate(() => {
      const visible = (el) => {
        if (!el) return false;
        const s = window.getComputedStyle(el);
        if (s.display === 'none' || s.visibility === 'hidden' || s.opacity === '0') return false;
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
      };
      for (const el of document.querySelectorAll('button, [role="button"], a')) {
        const t = (el.textContent || '').trim();
        if (/^start$/i.test(t) && visible(el)) {
          el.click();
          return 'Start';
        }
      }
      return null;
    });
    if (!clicked) break;
    log(`Clicked ${clicked} — waiting for task to activate`);
    await new Promise((r) => setTimeout(r, 3000));
  }
}

async function extractTaskOnly(page) {
  await clickStartIfNeeded(page);
  const onSuccess = await page.evaluate(() => /successfully submitted/i.test(document.body.innerText));
  if (onSuccess) {
    log('On success screen — clicking Next Task before extract');
    await page.evaluate(() => {
      const btn = [...document.querySelectorAll('button,a,[role=button]')].find(
        (b) => /next task/i.test(b.textContent) && b.offsetParent
      );
      if (btn) btn.click();
    });
    await new Promise((r) => setTimeout(r, 5000));
  }
  log('Extracting current task (fingerprint) ...');
  const prevFp = (() => { try { return loadTaskFile()?.fingerprint; } catch { return null; } })();
  const task = await extractTaskFromPage(page);
  saveTask(task);
  fs.writeFileSync(NEEDS_GRADING, task.fingerprint);
  if (prevFp && prevFp !== task.fingerprint) clearFormFlags();
  log(`Task saved fingerprint=${task.fingerprint} locale=${task.locale} responses=${task.responseCount || Object.keys(task.responses || {}).length} comparisons=${task.comparisonCount || task.comparisonKeys?.length || '?'}`);

  await page.context().browser().close();

  if (ratingsReadyStrict()) {
    log('Ratings already valid for this fingerprint');
  } else {
    log('Ratings missing — agent must grade now (see runs/GRADE_NOW.json)');
    try {
      execSync(`node "${path.join(ROOT, 'ensure_ratings.js')}"`, {
        cwd: ROOT,
        stdio: ['ignore', 'pipe', 'pipe'],
        timeout: 15000,
      });
    } catch {
      log('Awaiting agent manual grade → current_ratings.json + validate_ratings.js');
    }
  }
}

function clearFormFlags() {
  try { fs.unlinkSync(FORM_FILLED); } catch {}
  try { fs.unlinkSync(SUBMITTABLE); } catch {}
}

function isFormFilledForCurrentTask() {
  const task = loadTaskFile();
  if (!task?.fingerprint) return false;
  if (!fs.existsSync(SUBMITTABLE) || !fs.existsSync(FORM_FILLED)) return false;
  try {
    const flag = JSON.parse(fs.readFileSync(FORM_FILLED, 'utf8'));
    return flag.fingerprint === task.fingerprint;
  } catch {
    return false;
  }
}

function runFillFromRatings(reason) {
  log(`fill_from_ratings.js (${reason}) ...`);
  try {
    execSync(`node "${path.join(ROOT, 'fill_from_ratings.js')}"`, {
      cwd: ROOT,
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 180000,
    });
    const ok = isFormFilledForCurrentTask();
    log(ok ? 'fill+verify OK — form ready for 720s submit' : 'fill finished but form_filled.flag missing');
    return ok;
  } catch (e) {
    const detail = (e.stderr || e.stdout || e.message || '').toString().slice(0, 500);
    log(`fill_from_ratings failed: ${detail}`);
    return false;
  }
}

function tryEnsureRatings(reason) {
  log(`ensure_ratings (${reason}) ...`);
  try {
    execSync(`node "${path.join(ROOT, 'ensure_ratings.js')}"`, {
      cwd: ROOT,
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 320000,
    });
    return ratingsReadyStrict();
  } catch (e) {
    log(`ensure_ratings failed: ${(e.stderr || e.message || '').toString().slice(0, 300)}`);
    return false;
  }
}

async function writeOverdueAlert(tpt, reason) {
  const task = (() => { try { return JSON.parse(fs.readFileSync(path.join(ROOT, 'current_task.json'), 'utf8')); } catch { return null; } })();
  const alert = {
    at: new Date().toISOString(),
    tpt,
    target: SUBMIT_AT_SEC,
    overdue: tpt - SUBMIT_AT_SEC,
    fingerprint: task?.fingerprint || null,
    reason,
    action: 'Write current_ratings.json and run validate_ratings.js immediately',
  };
  fs.writeFileSync(path.join(RUNS, 'OVERDUE_ALERT.json'), JSON.stringify(alert, null, 2));
  fs.appendFileSync(path.join(RUNS, 'overdue.log'), `[${alert.at}] TPT=${tpt}s overdue=${alert.overdue}s fp=${alert.fingerprint} ${reason}\n`);
}

async function ensureFormFilled(browser, tpt, reason) {
  if (!ratingsReadyStrict()) return { browser, filled: false };
  if (isFormFilledForCurrentTask()) return { browser, filled: true };
  log(`Form not filled at TPT=${tpt}s — pause keepalive for ${reason}`);
  await browser.close();
  const ok = runFillFromRatings(reason);
  const reconnected = await connect();
  const { page } = getPage(reconnected);
  await page.setViewportSize({ width: 1919, height: 1079 }).catch(() => {});
  return { browser: reconnected, filled: ok };
}

async function keepaliveUntil720(browser) {
  let lastLog = 0;
  let lastFillCheck = 0;
  let wallStart = null;
  let blockedSince = null;
  let lastOverdueAlert = 0;
  let prevTpt = -1;

  if (ratingsReadyStrict() && !isFormFilledForCurrentTask()) {
    const r = await ensureFormFilled(browser, 0, 'post-grade pre-720 fill');
    browser = r.browser;
  }

  while (true) {
    const { page, frm } = getPage(browser);
    await clickStartIfNeeded(page);
    await page.mouse.move(450 + Math.random() * 200, 350 + Math.random() * 200).catch(() => {});
    await page.evaluate(() => { window.scrollBy(0, 10); setTimeout(() => window.scrollBy(0, -10), 80); }).catch(() => {});
    if (frm) await frm.evaluate(() => window.scrollBy(0, 8)).catch(() => {});

    let tpt = await readPageTPT(page);
    if (tpt < 0) {
      if (!wallStart) wallStart = Date.now();
      tpt = Math.floor((Date.now() - wallStart) / 1000);
    } else {
      wallStart = null;
      // 刷新/Start 后页面 TPT 归零 — 保活从 0 重计，清除旧填表标记
      if (prevTpt >= 90 && tpt < prevTpt - 60 && tpt < 90) {
        log(`TPT RESET ${prevTpt}s→${tpt}s — page refreshed or task restarted, 720s clock resets`);
        clearFormFlags();
        try { fs.unlinkSync(path.join(RUNS, 'ready.flag')); } catch {}
        fs.appendFileSync(path.join(RUNS, 'tpt_reset.log'),
          `[${new Date().toISOString()}] ${prevTpt}s→${tpt}s fp=${loadTaskFile()?.fingerprint || '?'}\n`);
        lastFillCheck = 0;
      }
      prevTpt = tpt;
    }
    const now = Date.now();
    const advanced = await page.evaluate(() => {
      const body = document.body.innerText;
      if (!/successfully submitted/i.test(body)) return false;
      const btn = [...document.querySelectorAll('button,a,[role=button]')].find(
        (b) => /next task/i.test(b.textContent) && b.offsetParent
      );
      if (btn) { btn.click(); return true; }
      return false;
    }).catch(() => false);
    if (advanced) {
      log('Clicked Next Task on success screen — will re-extract new task');
      invalidateRatings('advanced to next task on success screen');
      fs.writeFileSync(path.join(RUNS, 'needs_grading.flag'), '1');
      await new Promise((r) => setTimeout(r, 5000));
      return 'NEXT_TASK';
    }
    if (ratingsReadyStrict() && !isFormFilledForCurrentTask() && tpt < SUBMIT_AT_SEC - 30) {
      if (now - lastFillCheck > 90000 || (tpt >= SUBMIT_AT_SEC - 300 && now - lastFillCheck > 30000)) {
        lastFillCheck = now;
        const r = await ensureFormFilled(browser, tpt, 'scheduled pre-720 fill');
        browser = r.browser;
      }
    }
    if (now - lastLog > 30000) {
      const ready = ratingsReadyStrict();
      const filled = isFormFilledForCurrentTask();
      log(`保活 pageTPT=${tpt}s/${SUBMIT_AT_SEC}s ratingsReady=${ready} formFilled=${filled}`);
      if (ready && !filled && tpt < SUBMIT_AT_SEC) {
        log(`WARN: ratings ready but form not filled — will fill before 720s`);
      }
      if (!ready && tpt >= SUBMIT_AT_SEC - 120) {
        log(`WARN: TPT approaching ${SUBMIT_AT_SEC}s but ratings not ready`);
      }
      lastLog = now;
    }
    if (ratingsReadyStrict() && !isFormFilledForCurrentTask() && tpt < SUBMIT_AT_SEC - 30) {
      if (now - lastFillCheck > 60000 || (tpt >= SUBMIT_AT_SEC - 180 && now - lastFillCheck > 20000)) {
        lastFillCheck = now;
        const r = await ensureFormFilled(browser, tpt, 'retry fill before deadline');
        browser = r.browser;
      }
    }
    if (tpt >= SUBMIT_AT_SEC) {
      if (!ratingsReadyStrict()) {
        if (!blockedSince) blockedSince = Date.now();
        const overdue = tpt - SUBMIT_AT_SEC;
        const blockedSec = Math.floor((Date.now() - blockedSince) / 1000);

        // Auto-grade retry: don't let TPT run to 1600s idle
        const gradeEvery = overdue >= 300 ? 15000 : overdue >= 60 ? 30000 : 60000;
        if (Date.now() - lastOverdueAlert > gradeEvery) {
          lastOverdueAlert = Date.now();
          if (overdue >= 60) {
            const msg = `CRITICAL: TPT=${tpt}s (${overdue}s past target) — attempting ensure_ratings`;
            log(msg);
            writeOverdueAlert(tpt, msg);
          }
          try {
            const task = await extractTaskFromPage(page);
            saveTask(task);
            fs.writeFileSync(NEEDS_GRADING, task.fingerprint);
          } catch (e) {
            log(`re-extract failed: ${e.message}`);
          }
          if (tryEnsureRatings(`TPT=${tpt}s overdue=${overdue}s`)) {
            blockedSince = null;
            const r = await ensureFormFilled(browser, tpt, 'overdue fill after grade');
            browser = r.browser;
            if (!r.filled) {
              log('ratings OK but fill failed — retry fill before submit');
              await new Promise((res) => setTimeout(res, 10000));
              continue;
            }
            try { fs.unlinkSync(path.join(RUNS, 'OVERDUE_ALERT.json')); } catch {}
            fs.writeFileSync(path.join(RUNS, 'ready.flag'), String(tpt));
            log(`TPT=${tpt}s — ratings+form ready, trigger submit`);
            return { tpt, browser };
          }
        }

        log(`BLOCKED: TPT=${tpt}s ratings not ready (blocked ${blockedSec}s) — retry in ${Math.round(gradeEvery / 1000)}s`);
        await new Promise((r) => setTimeout(r, Math.min(gradeEvery, 15000)));
        continue;
      }
      if (!isFormFilledForCurrentTask()) {
        const r = await ensureFormFilled(browser, tpt, 'last-chance fill at 720s');
        browser = r.browser;
        if (!r.filled) {
          log(`BLOCKED at 720s: form fill failed — retry in 10s`);
          await new Promise((res) => setTimeout(res, 10000));
          continue;
        }
      }
      blockedSince = null;
      try { fs.unlinkSync(path.join(RUNS, 'OVERDUE_ALERT.json')); } catch {}
      fs.writeFileSync(path.join(RUNS, 'ready.flag'), String(tpt));
      log(`TPT=${tpt}s — 触发提交 (form pre-filled, submit-only)`);
      return { tpt, browser };
    }
    const poll = tpt >= SUBMIT_AT_SEC - 30 ? 2000 : tpt >= SUBMIT_AT_SEC - 120 ? 5000 : 12000;
    await new Promise((r) => setTimeout(r, poll));
  }
}

function runSubmit() {
  log('validate_ratings.js pre-check ...');
  execSync(`node "${path.join(ROOT, 'validate_ratings.js')}"`, {
    cwd: ROOT,
    stdio: ['ignore', 'pipe', 'pipe'],
    timeout: 15000,
  });
  if (!isFormFilledForCurrentTask()) {
    log('WARN: submittable flag missing — running fill before submit');
    if (!runFillFromRatings('pre-submit safety fill')) {
      throw new Error('form not filled before submit');
    }
  }
  log('执行 submit_from_ratings.js --submit-only (720s click Submit) ...');
  try {
    execSync(`node "${path.join(ROOT, 'submit_from_ratings.js')}" --submit-only`, {
      cwd: ROOT,
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 180000,
    });
  } catch (e) {
    const detail = (e.stderr || e.stdout || e.message || '').toString().slice(0, 800);
    log(`submit_from_ratings.js failed:\n${detail}`);
    throw e;
  }
  // Do NOT delete ratings here — next loop extract+saveTask invalidates on fingerprint change only.
}

async function main() {
  fs.mkdirSync(RUNS, { recursive: true });
  if (fs.existsSync(PID_FILE)) {
    const old = parseInt(fs.readFileSync(PID_FILE, 'utf8'), 10);
    try { process.kill(old, 0); log(`bridge already pid=${old}`); process.exit(0); } catch {}
  }
  fs.writeFileSync(PID_FILE, String(process.pid));
  log(`task_bridge pid=${process.pid} targetTPT=${SUBMIT_AT_SEC}s [fingerprint guard ON]`);

  while (true) {
    let browser;
    try {
      try { fs.unlinkSync(path.join(RUNS, 'ready.flag')); } catch {}
      try { fs.unlinkSync(path.join(RUNS, 'submitted.flag')); } catch {}

      browser = await connect();
      const { page } = getPage(browser);
      await page.setViewportSize({ width: 1919, height: 1079 }).catch(() => {});
      await clickStartIfNeeded(page);

      await extractTaskOnly(page);
      browser = null;

      if (ratingsReadyStrict()) {
        runFillFromRatings('after extract ratings ready');
      }

      browser = await connect();
      const { page: page2 } = getPage(browser);
      await page2.setViewportSize({ width: 1919, height: 1079 }).catch(() => {});
      await clickStartIfNeeded(page2);

      let keepResult = await keepaliveUntil720(browser);
      if (typeof keepResult === 'object' && keepResult.browser) {
        browser = keepResult.browser;
      }
      const tptBefore = typeof keepResult === 'object' ? keepResult.tpt : keepResult;
      await browser.close();
      browser = null;

      if (tptBefore === 'NEXT_TASK') {
        log('Next task loaded — re-extract + grade, skip submit');
        browser = await connect();
        const { page: pageRe } = getPage(browser);
        await pageRe.setViewportSize({ width: 1919, height: 1079 }).catch(() => {});
        await extractTaskOnly(pageRe);
        await browser.close();
        browser = null;
        continue;
      }

      runSubmit();

      browser = await connect();
      const tptAfter = await readPageTPT(getPage(browser).page);
      log(`提交完成 TPT ${tptBefore}s → ${tptAfter}s`);
      await browser.close();
      await new Promise((r) => setTimeout(r, 3000));
    } catch (e) {
      log(`ERROR: ${e.message}`);
      if (browser) await browser.close().catch(() => {});
      await new Promise((r) => setTimeout(r, 8000));
    }
  }
}

process.on('SIGTERM', () => { try { fs.unlinkSync(PID_FILE); } catch {}; process.exit(0); });
main().catch((e) => { log(`FATAL: ${e.message}`); process.exit(1); });
