const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const CDP_ENDPOINTS = ['http://127.0.0.1:9233', 'http://127.0.0.1:9232'];
const RUNS = path.resolve(__dirname, '..', 'runs');

async function connect() {
  let lastError;
  for (const endpoint of CDP_ENDPOINTS) {
    try {
      return { browser: await chromium.connectOverCDP(endpoint), endpoint };
    } catch (e) {
      lastError = e;
    }
  }
  throw lastError || new Error('No CDP');
}

function cleanText(t) {
  return (t || '').replace(/\u00a0/g, ' ').trim();
}

function parseTaskData(frames) {
  const convFrame = frames.find((f) => /^Conversation\n/.test(f.text));
  const profileFrame = frames.find((f) => f.text.includes('Common phrases') && f.text.includes('Hide Profile'));
  const getResponse = (label) => {
    const f = frames.find((x) => x.text.startsWith(`${label}\n`) && !x.text.includes('Your ratings'));
    if (!f) return '';
    return f.text.replace(new RegExp(`^${label}\\n`), '').trim();
  };
  return {
    conversation: convFrame ? convFrame.text : '',
    profile: profileFrame ? profileFrame.text.slice(0, 2000) : '',
    responseA1: getResponse('Response A1'),
    responseA2: getResponse('Response A2'),
    responseB1: getResponse('Response B1'),
    responseB2: getResponse('Response B2'),
  };
}

function fingerprintFromData(data) {
  const payload = [
    data.conversation,
    data.responseA1,
    data.responseA2,
    data.responseB1,
    data.responseB2,
  ].join('|||');
  return crypto.createHash('sha256').update(payload).digest('hex').slice(0, 16);
}

async function collectFrames(page) {
  const frames = [];
  for (const frame of page.frames()) {
    let text = '';
    try {
      text = cleanText(await frame.locator('body').innerText({ timeout: 800 }));
    } catch {}
    if (text) frames.push({ url: frame.url(), text });
  }
  return frames;
}

async function extractFromPage(page) {
  const frames = await collectFrames(page);
  const data = parseTaskData(frames);
  const fingerprint = fingerprintFromData(data);
  const timerBody = await page.locator('body').innerText({ timeout: 2000 }).catch(() => '');
  const timerMatch = timerBody.match(/(\d+)s/);
  const timerSec = timerMatch ? parseInt(timerMatch[1], 10) : 0;
  return {
    extractedAt: new Date().toISOString(),
    fingerprint,
    timerSec,
    data,
    frames,
  };
}

async function extractTask() {
  const { browser, endpoint } = await connect();
  try {
    const page = browser.contexts()[0].pages().find((p) => p.url().includes('starshot')) || browser.contexts()[0].pages()[0];
    const task = await extractFromPage(page);
    return { ...task, cdpEndpoint: endpoint };
  } finally {
    await browser.close();
  }
}

function loadActiveFingerprint() {
  const f = path.join(RUNS, 'active-fingerprint.txt');
  return fs.existsSync(f) ? fs.readFileSync(f, 'utf8').trim() : '';
}

function saveActiveFingerprint(fp) {
  fs.mkdirSync(RUNS, { recursive: true });
  fs.writeFileSync(path.join(RUNS, 'active-fingerprint.txt'), fp);
}

function loadAnswers() {
  const p = path.join(RUNS, 'current-answers.json');
  if (!fs.existsSync(p)) return null;
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch {
    return null;
  }
}

function answersMatchFingerprint(fp) {
  const a = loadAnswers();
  return a && a.fingerprint === fp;
}

function writeNeedsGrading(task) {
  fs.mkdirSync(RUNS, { recursive: true });
  fs.writeFileSync(path.join(RUNS, 'current-task.json'), JSON.stringify(task, null, 2));
  fs.writeFileSync(
    path.join(RUNS, 'needs_grading.json'),
    JSON.stringify({
      fingerprint: task.fingerprint,
      requestedAt: new Date().toISOString(),
      conversation: task.data.conversation,
      responses: {
        A1: task.data.responseA1,
        A2: task.data.responseA2,
        B1: task.data.responseB1,
        B2: task.data.responseB2,
      },
    }, null, 2)
  );
}

module.exports = {
  RUNS,
  connect,
  extractTask,
  extractFromPage,
  collectFrames,
  fingerprintFromData,
  parseTaskData,
  loadActiveFingerprint,
  saveActiveFingerprint,
  loadAnswers,
  answersMatchFingerprint,
  writeNeedsGrading,
};
