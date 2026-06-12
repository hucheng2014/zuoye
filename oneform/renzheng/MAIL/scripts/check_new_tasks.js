const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const CDP_ENDPOINTS = [
  process.env.MAIL_CDP_ENDPOINT || 'http://127.0.0.1:9233',
  'http://127.0.0.1:9232',
];

const RUNS_DIR = path.resolve(__dirname, '..', 'runs');
const ALERT_FILE = path.join(RUNS_DIR, 'task_alert.flag');
const STATUS_FILE = path.join(RUNS_DIR, 'task_check_status.json');

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

async function getText(locator, timeout = 750) {
  return locator.innerText({ timeout }).catch(() => '');
}

async function clickIfVisible(locator, timeout = 750) {
  if (!(await locator.count().catch(() => 0))) return false;
  const target = locator.first();
  if (!(await target.isVisible({ timeout }).catch(() => false))) return false;
  await target.click({ timeout });
  return true;
}

async function findTaskFrame(page) {
  const editor = page.frames().find((frame) => frame.url().includes('/task-editor/'));
  if (editor) return editor;
  for (const frame of page.frames()) {
    const text = await getText(frame.locator('body'), 300);
    if (text.includes('Prompt') && text.includes('Response A')) return frame;
  }
  return null;
}

function statusFromText(text) {
  if (/Session expired|Error: 440/i.test(text)) return 'session_expired';
  if (/there are no available tasks/i.test(text)) return 'no_tasks';
  if (/Task successfully submitted/i.test(text)) return 'submitted';
  if (/Submission failed/i.test(text)) return 'submission_failed';
  if (/Invalid Answers|An answer is required/i.test(text)) return 'needs_fix';
  if (text.includes('Prompt') && text.includes('Response A') && text.includes('Response B')) return 'task_available';
  return 'unknown';
}

async function main() {
  fs.mkdirSync(RUNS_DIR, { recursive: true });
  const now = new Date().toISOString();
  const { browser, endpoint } = await connect();
  const result = {
    checkedAt: now,
    cdpEndpoint: endpoint,
    status: 'unknown',
    url: '',
    title: '',
    clickedTryAgain: false,
    bodyPreview: '',
    taskPreview: '',
  };

  try {
    const context = browser.contexts()[0];
    if (!context) throw new Error('No browser context found');
    const page = context.pages().find((p) => p.url().includes('starshot.scilliance.com')) || context.pages()[0];
    if (!page) throw new Error('No page found');
    page.setDefaultTimeout(1000);

    result.url = page.url();
    result.title = await page.title().catch(() => '');

    let body = await getText(page.locator('body'), 750);
    result.bodyPreview = body.slice(0, 1000);

    let status = statusFromText(body);

    if (status === 'session_expired') {
      console.log(`[${now}] Session expired (Error 440) detected! Performing self-healing page reload...`);
      await page.reload();
      await page.waitForTimeout(5000); // Wait 5s for silent OIDC auth redirect to complete
      body = await getText(page.locator('body'), 750);
      result.bodyPreview = body.slice(0, 1000);
      status = statusFromText(body);
      console.log(`[${now}] Page reloaded successfully. New status: ${status}`);
    }

    if (/there are no available tasks/i.test(body)) {
      result.clickedTryAgain = await clickIfVisible(page.locator('button', { hasText: 'Try Again' }), 1000);

      if (result.clickedTryAgain) {
        await page.waitForTimeout(Number(process.env.MAIL_CHECK_WAIT_MS || 3000));
        body = await getText(page.locator('body'), 750);
        result.bodyPreview = body.slice(0, 1000);
      }
    }

    status = statusFromText(body);
    const taskFrame = await findTaskFrame(page);
    if (taskFrame) {
      const taskText = await getText(taskFrame.locator('body'), 750);
      result.taskPreview = taskText.slice(0, 2000);
      const taskStatus = statusFromText(taskText);
      if (taskStatus === 'task_available') status = taskStatus;
    }

    result.status = status;
  } catch (error) {
    result.status = 'error';
    result.error = error.stack || error.message;
  } finally {
    await browser.close().catch(() => {});
  }

  fs.writeFileSync(STATUS_FILE, JSON.stringify(result, null, 2));
  if (result.status === 'task_available') {
    fs.writeFileSync(ALERT_FILE, `${result.checkedAt}|task_available\n`);
    console.log(`[${result.checkedAt}] NEW TASK AVAILABLE`);
    console.log(result.taskPreview.slice(0, 600));
    process.exitCode = 2;
  } else {
    if (fs.existsSync(ALERT_FILE)) fs.unlinkSync(ALERT_FILE);
    console.log(`[${result.checkedAt}] ${result.status}`);
    if (result.status === 'error') console.log(result.error);
  }
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
