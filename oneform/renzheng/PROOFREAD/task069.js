const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const CDP_ENDPOINTS = [
  process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233',
  'http://127.0.0.1:9232',
];

async function connect() {
  for (const ep of CDP_ENDPOINTS) {
    try {
      return { browser: await chromium.connectOverCDP(ep), endpoint: ep };
    } catch {}
  }
  throw new Error('No CDP endpoint available');
}

function formatRemain(ms) {
  const s = Math.max(0, Math.ceil(ms / 1000));
  const mm = String(Math.floor(s / 60)).padStart(2, '0');
  const ss = String(s % 60).padStart(2, '0');
  return `${mm}:${ss}`;
}

async function maybeClickStart(page) {
  const btn = page.locator('[aria-label="Task Overview"] button:has-text("Start")');
  if (await btn.count().catch(() => 0)) {
    try {
      await btn.first().click({ timeout: 1500 });
      await page.waitForTimeout(500);
    } catch {}
  }
}

async function getTaskFrame(page) {
  const f = page.frames().find(fr => fr.url().includes('task-editor'));
  if (!f) throw new Error('task-editor frame not found');
  return f;
}

async function reactSet(frame, selector) {
  return frame.evaluate(sel => {
    const el = document.querySelector(sel);
    if (!el) return false;
    el.focus();
    el.click();
    const descriptor = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'checked');
    if (descriptor && descriptor.set) descriptor.set.call(el, true);
    el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
    el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    return el.checked;
  }, selector);
}

async function checkRadio(frame, value, page) {
  const all = frame.locator(`input[type="radio"][value="${value}"]`);
  const count = await all.count();
  for (let i = 0; i < count; i++) {
    const el = all.nth(i);
    const visible = await el.isVisible().catch(() => false);
    if (!visible) continue;
    try {
      await el.click({ force: true, timeout: 2000 });
    } catch {}
    const name = await el.getAttribute('name').catch(() => null);
    const sel = name
      ? `input[type="radio"][name="${name}"][value="${value}"]`
      : `input[type="radio"][value="${value}"]`;
    await reactSet(frame, sel);
    await page.waitForTimeout(250);
    return;
  }
  if (count > 0) {
    const el = all.first();
    try {
      await el.click({ force: true, timeout: 2000 });
    } catch {}
    const name = await el.getAttribute('name').catch(() => null);
    const sel = name
      ? `input[type="radio"][name="${name}"][value="${value}"]`
      : `input[type="radio"][value="${value}"]`;
    await reactSet(frame, sel);
    await page.waitForTimeout(250);
    return;
  }
  throw new Error(`Radio value "${value}" not found`);
}

async function checkCheckbox(frame, value, shouldCheck, page) {
  const all = frame.locator(`input[type="checkbox"][value="${value}"]`);
  const count = await all.count();
  for (let i = 0; i < count; i++) {
    const el = all.nth(i);
    const visible = await el.isVisible().catch(() => false);
    if (!visible) continue;
    if (shouldCheck) {
      try {
        await el.check({ force: true });
      } catch {
        const name = await el.getAttribute('name').catch(() => null);
        const sel = name
          ? `input[type="checkbox"][name="${name}"][value="${value}"]`
          : `input[type="checkbox"][value="${value}"]`;
        await reactSet(frame, sel);
      }
      await page.waitForTimeout(200);
    } else {
      await el.uncheck({ force: true }).catch(() => {});
    }
    return;
  }
  if (count > 0) {
    const el = all.first();
    if (shouldCheck) {
      try {
        await el.check({ force: true });
      } catch {
        const name = await el.getAttribute('name').catch(() => null);
        const sel = name
          ? `input[type="checkbox"][name="${name}"][value="${value}"]`
          : `input[type="checkbox"][value="${value}"]`;
        await reactSet(frame, sel);
      }
      await page.waitForTimeout(200);
    } else {
      await el.uncheck({ force: true }).catch(() => {});
    }
  }
}

async function clickTab(frame, name, page) {
  const clicked = await frame.evaluate(tabName => {
    const tab = Array.from(document.querySelectorAll('[role="tab"]'))
      .find(t => t.textContent.trim().includes(tabName));
    if (tab) {
      tab.click();
      return true;
    }
    return false;
  }, name);
  if (clicked) await page.waitForTimeout(300);
}

async function fillResponse(frame, page, tabName, resp, q1) {
  await clickTab(frame, tabName, page);
  await checkRadio(frame, resp.q2, page);

  if (resp.q2 === 'has_edits') {
    if (q1 === 'has_grammar_errors') {
      await checkRadio(frame, resp.correctness, page);

      if (resp.correctness === 'all_necessary') {
        await checkRadio(frame, resp.editsCorrect || 'all_correct', page);
      } else if (resp.correctness === 'some_unnecessary' || resp.correctness === 'all_unnecessary') {
        if (resp.editsCorrect) await checkRadio(frame, resp.editsCorrect, page);
        if (resp.unnecessaryImpact) await checkRadio(frame, resp.unnecessaryImpact, page);
      }

      if (resp.correctnessErrors && resp.correctnessErrors.length) {
        for (const v of resp.correctnessErrors) await checkCheckbox(frame, v, true, page);
      }

      if (resp.unnecessaryEdits && resp.unnecessaryEdits.length) {
        for (const v of resp.unnecessaryEdits) await checkCheckbox(frame, v, true, page);
      }

      if (resp.completeness) await checkRadio(frame, resp.completeness, page);

      if (resp.missedErrors && resp.missedErrors.length) {
        for (const v of resp.missedErrors) await checkCheckbox(frame, v, true, page);
      }
    } else if (q1 === 'no_grammar_errors') {
      if (resp.alteredMeaning !== undefined) await checkRadio(frame, resp.alteredMeaning, page);
    }
  }
}

async function keepAlive(frame, page, minutes) {
  const tabs = ['Response A', 'Response B', 'Response C', 'A and B', 'A and C', 'B and C'];
  const endAt = Date.now() + minutes * 60 * 1000;
  let i = 0;

  while (Date.now() < endAt) {
    const remain = endAt - Date.now();
    try {
      const tabName = tabs[i % tabs.length];
      await clickTab(frame, tabName, page);
      await frame.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(2500);
      await frame.evaluate(() => window.scrollTo(0, 0));
      await page.waitForTimeout(2500);
      i += 1;

      if (i % 6 === 0) {
        console.log(`Keepalive countdown: ${formatRemain(remain)} (cycle ${Math.floor(i / 6)})`);
      }
    } catch (e) {
      console.log('Keepalive loop stopped:', e.message);
      break;
    }
  }
}

async function submit(page, frame) {
  const submitBtn = frame.getByRole('button', { name: 'Submit' }).first();
  await submitBtn.click({ force: true, timeout: 3000 });
  await page.waitForTimeout(2000);

  const confirm = page.locator('#starshot_submit_task_button');
  if (await confirm.count().catch(() => 0)) {
    try {
      await confirm.click({ force: true, timeout: 3000 });
      await page.waitForTimeout(4000);
    } catch {}
  }

  const nextTask = page.locator('button:has-text("Next Task")');
  if (await nextTask.count().catch(() => 0)) {
    try {
      await nextTask.first().click({ force: true, timeout: 3000 });
      await page.waitForTimeout(4000);
    } catch {}
  }
}

async function main() {
  const answers = JSON.parse(fs.readFileSync(path.resolve(__dirname, 'runs/task-069-answers.json'), 'utf8'));
  const { browser, endpoint } = await connect();
  try {
    const ctx = browser.contexts()[0];
    if (!ctx) throw new Error('No browser context');
    const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
    if (!page) throw new Error('No page');

    console.log('Connected to', endpoint);
    await maybeClickStart(page);
    const frame = await getTaskFrame(page);

    await checkRadio(frame, answers.formality, page);
    await checkRadio(frame, answers.q1, page);

    const respNames = ['A', 'B', 'C'];
    const tabNames = ['Response A', 'Response B', 'Response C'];
    for (let i = 0; i < respNames.length; i++) {
      const resp = answers.responses[respNames[i]];
      if (!resp) continue;
      await fillResponse(frame, page, tabNames[i], resp, answers.q1);
    }

    const pairTabs = [
      { tabs: ['B and A', 'A and B'], key: 'BvsA' },
      { tabs: ['C and A', 'A and C'], key: 'CvsA' },
      { tabs: ['C and B', 'B and C'], key: 'CvsB' },
    ];
    for (const { tabs, key } of pairTabs) {
      const val = answers.pairwise[key];
      if (!val) continue;
      let clicked = false;
      for (const tabName of tabs) {
        const found = await frame.evaluate(name => {
          const tab = Array.from(document.querySelectorAll('[role="tab"]'))
            .find(t => t.textContent.trim().includes(name));
          if (tab) {
            tab.click();
            return true;
          }
          return false;
        }, tabName);
        if (found) {
          await page.waitForTimeout(300);
          clicked = true;
          break;
        }
      }
      if (clicked) await checkRadio(frame, val, page);
    }

    if (answers.observation) await frame.locator('textarea').first().fill(answers.observation);

    const bodyText = await frame.locator('body').innerText({ timeout: 2000 }).catch(() => '');
    const complete = bodyText.match(/(\d+\/\d+) Complete/g) || [];
    console.log('Completion status:', complete.join(', ') || 'unknown');

    await keepAlive(frame, page, 12);
    await submit(page, frame);
    console.log('Submitted task-069');
  } finally {
    // Keep external browser alive.
  }
}

main().catch(e => {
  console.error(e.stack || e.message);
  process.exit(1);
});
