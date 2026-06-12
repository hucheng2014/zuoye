/**
 * After start: wait for current task submit → rate next task → wait for 2nd submit → stop bridge + close tab.
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const puppeteer = require('puppeteer-core');
const { CDP_URL } = require('./config');

const ROOT = __dirname;
const LOG = path.join(ROOT, 'runs', 'finish.log');
const SUBMIT_LOG = path.join(ROOT, 'runs', 'submit.log');

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  fs.mkdirSync(path.join(ROOT, 'runs'), { recursive: true });
  fs.appendFileSync(LOG, line + '\n', { flag: 'a' });
}

function successCountSince(mark) {
  if (!fs.existsSync(SUBMIT_LOG)) return 0;
  return fs.readFileSync(SUBMIT_LOG, 'utf8')
    .split('\n')
    .filter((l) => l.includes('SUCCESS total') && l.slice(1, 25) > mark.slice(0, 24))
    .length;
}

function getSubmitLogTail() {
  if (!fs.existsSync(SUBMIT_LOG)) return '';
  const lines = fs.readFileSync(SUBMIT_LOG, 'utf8').split('\n');
  return lines.slice(-3).join('\n');
}

async function waitForSuccess(sinceMark, label, maxMin = 25) {
  for (let i = 0; i < maxMin * 2; i++) {
    await new Promise((r) => setTimeout(r, 30000));
    const n = successCountSince(sinceMark);
    if (n >= 1) {
      log(`${label} submit OK`);
      return true;
    }
    if (i % 4 === 0) log(`${label} waiting... tail: ${getSubmitLogTail().slice(-120)}`);
  }
  log(`${label} TIMEOUT`);
  return false;
}

async function closeStarshotTab() {
  const browser = await puppeteer.connect({ browserURL: CDP_URL, defaultViewport: null });
  const page = (await browser.pages()).find((p) => p.url().includes('starshot'));
  if (page) {
    log(`Closing: ${page.url().slice(0, 100)}`);
    await page.close();
  }
  await browser.disconnect();
}

async function main() {
  const t0 = new Date().toISOString();
  log('=== finish_two_and_stop: current(纪念品) + 1 more ===');

  // 1) Wait current task (纪念品) submit
  await waitForSuccess(t0, 'Task1-纪念品');

  // 2) Next task: click Next if needed, extract, agent must have rated — run pipeline for logging
  await new Promise((r) => setTimeout(r, 8000));
  try {
    execSync(`node "${path.join(ROOT, 'run_pipeline.js')}"`, { cwd: ROOT, stdio: 'pipe' });
    log('Extracted task2 — ratings must be in current_ratings.json (updated by agent)');
  } catch (e) {
    log(`extract warn: ${e.message}`);
  }

  const t1 = new Date().toISOString();
  // 3) Wait second task submit
  await waitForSuccess(t1, 'Task2-final');

  try { execSync('pkill -f "task_bridge.js"', { stdio: 'ignore' }); } catch {}
  log('bridge stopped');
  await new Promise((r) => setTimeout(r, 2000));
  await closeStarshotTab();
  log('=== ALL DONE ===');
}

main().catch((e) => { log(`FATAL: ${e.message}`); process.exit(1); });
