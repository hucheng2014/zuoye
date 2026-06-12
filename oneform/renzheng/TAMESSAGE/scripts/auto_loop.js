/**
 * auto_loop.js — 闭环机械流程（单 CDP 连接，永不空转等待）
 *
 * ⚠️ 本脚本不做判分。每道题必须由 agent 独立阅读对话/画像/回复后
 *    写入 runs/current-answers.json（含 fingerprint 字段）。禁止硬规则/template 打分。
 *
 * 每 15s 一轮，始终保活：
 *   1. 检测 fingerprint → 新题写 needs_grading.json，清除旧 filled 标记
 *   2. 有 agent 写入的匹配答案且未填 → 短暂断开填表
 *   3. 已填且 TPT≥540（9min）→ 提交 + Next Task
 *
 * 等答案期间也持续保活，不会停止。
 */
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { chromium } = require('playwright');
const {
  RUNS,
  connect,
  extractFromPage,
  saveActiveFingerprint,
  answersMatchFingerprint,
  writeNeedsGrading,
} = require('./task_utils');
const { submitAndNext, readTimer } = require('./submit_task');
const { dismissPopups } = require('./dismiss_popups');

const CDP_URL = 'http://127.0.0.1:9233';
const { SUBMIT_AT_SEC: SUBMIT_AT } = require('./config');
const CYCLE_MS = 15000;
const LOG_FILE = path.join(RUNS, 'auto_loop.log');
const PID_FILE = path.join(RUNS, 'auto_loop.pid');
const FILLED_FILE = path.join(RUNS, 'filled-fingerprint.txt');
const STATE_FILE = path.join(RUNS, 'loop-state.json');

let running = true;

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  process.stdout.write(line);
  fs.appendFileSync(LOG_FILE, line, { flag: 'a' });
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function loadState() {
  try {
    return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
  } catch {
    return { fingerprint: null, filled: false };
  }
}

function saveState(state) {
  fs.mkdirSync(RUNS, { recursive: true });
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

function runFill() {
  const root = path.resolve(__dirname, '..', '..');
  const answers = path.join(RUNS, 'current-answers.json');
  const r = spawnSync(
    'node',
    [path.join(__dirname, 'fill_task.js'), '--answers', answers],
    { cwd: root, encoding: 'utf8', timeout: 120000 }
  );
  if (r.status !== 0) {
    throw new Error(`fill failed: ${(r.stderr || r.stdout || '').slice(0, 400)}`);
  }
  const check = spawnSync(
    'node',
    [path.join(__dirname, 'check_form.js'), '--answers', answers],
    { cwd: root, encoding: 'utf8', timeout: 60000 }
  );
  if (check.stdout) log(check.stdout.trim());
  if (check.status !== 0) {
    throw new Error(`verify failed: ${(check.stderr || check.stdout || '').slice(0, 400)}`);
  }
}

async function doActivity(page, taskFrame) {
  const x = 400 + Math.floor(Math.random() * 300);
  const y = 300 + Math.floor(Math.random() * 300);
  await page.mouse.move(x, y).catch(() => {});
  await page.evaluate(() => {
    window.scrollBy(0, 10);
    setTimeout(() => window.scrollBy(0, -10), 100);
  }).catch(() => {});
  await taskFrame.evaluate(() => window.scrollBy(0, 10)).catch(() => {});
}

async function hasTaskOnPage(page) {
  const parts = [await page.locator('body').innerText({ timeout: 2000 }).catch(() => '')];
  for (const f of page.frames()) {
    try {
      const t = await f.locator('body').innerText({ timeout: 400 });
      if (t) parts.push(t);
    } catch {}
  }
  const joined = parts.join('\n');
  // 仅 Message Smart Reply / Personalized Smart Replies；排除 Preference Ranking 等含 Response A/B 的其他题型
  if (/Preference Ranking|Instruction Fine-Tuning/i.test(joined)) return false;
  if (/Message Smart Reply|Personalized Smart Replies/i.test(joined)) return true;
  return /Response A1/i.test(joined) && /Pairwise Comparison/i.test(joined);
}

async function unifiedLoop() {
  fs.mkdirSync(RUNS, { recursive: true });

  if (fs.existsSync(PID_FILE)) {
    const old = parseInt(fs.readFileSync(PID_FILE, 'utf8').trim(), 10);
    if (old && old !== process.pid) {
      try {
        process.kill(old, 0);
        log(`Another auto_loop alive (pid ${old}), exit.`);
        process.exit(0);
      } catch {}
    }
  }
  fs.writeFileSync(PID_FILE, String(process.pid));
  log(`=== Closed-loop started (TPT target ${SUBMIT_AT}s, cycle ${CYCLE_MS / 1000}s) ===`);

  let state = loadState();
  let browser = null;
  let page = null;
  let taskFrame = null;
  let cycle = 0;

  while (running) {
    try {
      if (!browser || !browser.isConnected()) {
        if (browser) await browser.close().catch(() => {});
        browser = await chromium.connectOverCDP(CDP_URL);
        page = browser.contexts()[0].pages().find((p) => p.url().includes('starshot')) || browser.contexts()[0].pages()[0];
        await page.setViewportSize({ width: 1919, height: 1079 }).catch(() => {});
        taskFrame = page.frames().find((f) => f.url().includes('/task-editor/')) || page;
        log('CDP connected.');
      }

      await dismissPopups(page, log);

      if (!(await hasTaskOnPage(page))) {
        if (cycle % 4 === 0) log('No task visible — waiting...');
        await sleep(CYCLE_MS);
        cycle++;
        continue;
      }

      await doActivity(page, taskFrame);

      const task = await extractFromPage(page);
      const fp = task.fingerprint;
      const timerSec = task.timerSec || (await readTimer(page));

      // --- 新题检测 ---
      if (fp !== state.fingerprint) {
        log(`NEW TASK: ${state.fingerprint || '(none)'} → ${fp}  TPT=${timerSec}s`);
        state = { fingerprint: fp, filled: false };
        saveState(state);
        saveActiveFingerprint(fp);
        try { fs.unlinkSync(FILLED_FILE); } catch {}
        writeNeedsGrading(task);
      }

      const hasAnswers = answersMatchFingerprint(fp);

      // --- 填表（有答案且未填）---
      if (hasAnswers && !state.filled) {
        log(`Answers ready — filling (fp=${fp})`);
        await browser.close().catch(() => {});
        browser = null;
        runFill();
        fs.writeFileSync(FILLED_FILE, fp);
        state.filled = true;
        saveState(state);
        log('Fill done — resuming keepalive.');
        await sleep(2000);
        continue;
      }

      if (!hasAnswers && cycle % 4 === 0) {
        log(`TPT=${timerSec}s/${SUBMIT_AT}s  waiting answers fp=${fp}  (keepalive ON)`);
      } else if (state.filled && cycle % 4 === 0) {
        log(`TPT=${timerSec}s/${SUBMIT_AT}s  filled  fp=${fp}`);
      }

      // --- 到点提交 ---
      if (state.filled && timerSec >= SUBMIT_AT) {
        const pre = await extractFromPage(page);
        if (pre.fingerprint !== fp) {
          log(`Task changed before submit (${fp}→${pre.fingerprint}), skip.`);
          state = { fingerprint: pre.fingerprint, filled: false };
          saveState(state);
          continue;
        }
        log(`TPT ${timerSec}s >= ${SUBMIT_AT}s — verify then SUBMIT + Next Task`);
        await browser.close().catch(() => {});
        browser = null;
        const check = spawnSync(
          'node',
          [path.join(__dirname, 'check_form.js'), '--answers', path.join(RUNS, 'current-answers.json')],
          { cwd: path.resolve(__dirname, '..', '..'), encoding: 'utf8', timeout: 60000 }
        );
        if (check.stdout) log(check.stdout.trim());
        if (check.status !== 0) {
          throw new Error(`pre-submit verify failed: ${(check.stderr || check.stdout || '').slice(0, 400)}`);
        }
        browser = await chromium.connectOverCDP(CDP_URL);
        page = browser.contexts()[0].pages().find((p) => p.url().includes('starshot')) || browser.contexts()[0].pages()[0];
        taskFrame = page.frames().find((f) => f.url().includes('/task-editor/')) || page;
        const result = await submitAndNext(page, taskFrame, { logger: log, clickNext: true });
        log(`Submit result: submitted=${result.submitted} nextTask=${result.nextTask}`);
        state = { fingerprint: null, filled: false };
        saveState(state);
        try { fs.unlinkSync(FILLED_FILE); } catch {}
        await sleep(5000);
        cycle = 0;
        continue;
      }

      cycle++;
      await sleep(CYCLE_MS);
    } catch (e) {
      log(`ERROR: ${e.message}`);
      if (browser) {
        await browser.close().catch(() => {});
        browser = null;
      }
      await sleep(5000);
    }
  }

  if (browser) await browser.close().catch(() => {});
  try { fs.unlinkSync(PID_FILE); } catch {}
}

process.on('SIGINT', () => { running = false; });
process.on('SIGTERM', () => { running = false; });

unifiedLoop().catch((e) => {
  log(`FATAL: ${e.message}`);
  process.exit(1);
});
