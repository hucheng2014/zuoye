require('./_timeout');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const CDP_ENDPOINTS = [
  process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233',
  'http://127.0.0.1:9232',
];

function parseArgs() {
  const args = process.argv.slice(2);
  const out = { dryRun: false, submit: false };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--answers') out.answersPath = args[++i];
    else if (args[i] === '--dry-run') out.dryRun = true;
    else if (args[i] === '--submit') out.submit = true;
    else throw new Error(`Unknown arg: ${args[i]}`);
  }
  if (!out.answersPath) throw new Error('Usage: node fill_task.js --answers FILE [--dry-run|--submit]');
  return out;
}

async function connect() {
  for (const ep of CDP_ENDPOINTS) {
    try { return { browser: await chromium.connectOverCDP(ep), endpoint: ep }; } catch {}
  }
  throw new Error('No CDP endpoint available');
}

async function getTaskFrame(page) {
  const f = page.frames().find(f => f.url().includes('task-editor'));
  if (!f) throw new Error('task-editor frame not found');
  return f;
}

async function reactSet(frame, selector) {
  return frame.evaluate(sel => {
    const all = Array.from(document.querySelectorAll(sel));
    const el = all.find(e => e.offsetParent !== null) || all[0];
    if (!el) return false;
    // Simulate a full click sequence that React can intercept
    el.focus();
    el.click();
    const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'checked').set;
    nativeSetter.call(el, true);
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
  // Prefer visible radio buttons (active tab)
  for (let i = 0; i < count; i++) {
    const el = all.nth(i);
    const visible = await el.isVisible().catch(() => false);
    if (visible) {
      // Try native click first (works when Playwright can interact)
      try {
        await el.click({ force: true, timeout: 2000 });
      } catch {}
      // Always also fire React events via evaluate as fallback
      const name = await el.getAttribute('name').catch(() => null);
      const sel = name
        ? `input[type="radio"][name="${name}"][value="${value}"]`
        : `input[type="radio"][value="${value}"]`;
      await reactSet(frame, sel);
      await page.waitForTimeout(400);
      return;
    }
  }
  // Fallback: force-check the first one
  if (count > 0) {
    const el = all.first();
    try { await el.click({ force: true, timeout: 2000 }); } catch {}
    const name = await el.getAttribute('name').catch(() => null);
    const sel = name
      ? `input[type="radio"][name="${name}"][value="${value}"]`
      : `input[type="radio"][value="${value}"]`;
    await reactSet(frame, sel);
    await page.waitForTimeout(400);
    return;
  }
  throw new Error(`Radio value "${value}" not found`);
}

async function clickTab(frame, name, page) {
  // Use JS click for React tab navigation (Playwright pointer events don't reliably toggle aria-selected)
  const clicked = await frame.evaluate(tabName => {
    const tab = Array.from(document.querySelectorAll('[role="tab"]'))
      .find(t => t.textContent.trim().includes(tabName));
    if (tab) { tab.click(); return true; }
    return false;
  }, name);
  if (clicked) await page.waitForTimeout(400);
}

async function checkCheckbox(frame, value, shouldCheck) {
  const all = frame.locator(`input[type="checkbox"][value="${value}"]`);
  const count = await all.count();
  for (let i = 0; i < count; i++) {
    const el = all.nth(i);
    const visible = await el.isVisible().catch(() => false);
    if (visible) {
      if (shouldCheck) {
        try { await el.check({ force: true }); } catch {
          const name = await el.getAttribute('name').catch(() => null);
          const sel = name
            ? `input[type="checkbox"][name="${name}"][value="${value}"]`
            : `input[type="checkbox"][value="${value}"]`;
          await reactSet(frame, sel, true);
        }
        await new Promise(r => setTimeout(r, 400));
      } else { await el.uncheck({ force: true }).catch(() => {}); }
      return;
    }
  }
  // Fallback to first
  if (count > 0) {
    const el = all.first();
    if (shouldCheck) {
      try { await el.check({ force: true }); } catch {
        const name = await el.getAttribute('name').catch(() => null);
        const sel = name
          ? `input[type="checkbox"][name="${name}"][value="${value}"]`
          : `input[type="checkbox"][value="${value}"]`;
        await reactSet(frame, sel, true);
      }
      await new Promise(r => setTimeout(r, 400));
    } else { await el.uncheck({ force: true }).catch(() => {}); }
  }
}

// Check a value in the 5-item unnecessary edits group (skip the 12-item group)
async function checkUnnecessaryEditBox(frame, value) {
  const all = frame.locator(`input[type="checkbox"][value="${value}"]`);
  const count = await all.count();
  // Find visible checkbox that belongs to a group with only 5 options
  for (let i = 0; i < count; i++) {
    const el = all.nth(i);
    const visible = await el.isVisible().catch(() => false);
    if (!visible) continue;
    const groupSize = await el.evaluate(cb => {
      const name = cb.name;
      return document.querySelectorAll(`input[type="checkbox"][name="${name}"]`).length;
    });
    if (groupSize <= 5) {
      await el.check({ force: true });
      return;
    }
  }
  // Fallback: just check any visible one
  for (let i = 0; i < count; i++) {
    const el = all.nth(i);
    const visible = await el.isVisible().catch(() => false);
    if (visible) { await el.check({ force: true }); return; }
  }
}

async function fillResponse(frame, page, tabName, resp, q1) {
  await clickTab(frame, tabName, page);

  // Q2: has_edits or no_edits
  await checkRadio(frame, resp.q2, page);

  if (resp.q2 === 'has_edits') {
    if (q1 === 'has_grammar_errors') {
      // Correctness: all_necessary / some_unnecessary / all_unnecessary
      await checkRadio(frame, resp.correctness, page);

      if (resp.correctness === 'all_necessary') {
        // Sub-question: are all necessary edits correct?
        await checkRadio(frame, resp.editsCorrect || 'all_correct', page);
      } else if (resp.correctness === 'some_unnecessary' || resp.correctness === 'all_unnecessary') {
        // Sub-question: are the necessary edits correct? (same question)
        if (resp.editsCorrect) await checkRadio(frame, resp.editsCorrect, page);
        // Sub-question: type of unnecessary edits (formatting/mechanical/core_content)
        if (resp.unnecessaryEditType) await checkRadio(frame, resp.unnecessaryEditType, page);
      }

      // If some_unnecessary or all_unnecessary, may need to check error type boxes
      if (resp.correctnessErrors && resp.correctnessErrors.length) {
        for (const v of resp.correctnessErrors) {
          await checkCheckbox(frame, v, true);
        }
      }
      if (resp.unnecessaryEdits && resp.unnecessaryEdits.length) {
        for (const v of resp.unnecessaryEdits) {
          await checkUnnecessaryEditBox(frame, v);
        }
      }

      // Completeness (only when input has errors)
      if (resp.completeness) {
        await checkRadio(frame, resp.completeness, page);
      }

      // If not complete, may need missed error types
      if (resp.missedErrors && resp.missedErrors.length) {
        for (const v of resp.missedErrors) {
          await checkCheckbox(frame, v, true);
        }
      }
    } else if (q1 === 'no_grammar_errors') {
      // "Did any edit alter original meaning, tone, style, or register?"
      if (resp.alteredMeaning !== undefined) {
        // Wait for alteredMeaning radio to render after Q2 click
        try {
          await frame.waitForSelector(`input[type="radio"][value="${resp.alteredMeaning}"]`, { timeout: 5000 });
        } catch (e) {
          await page.waitForTimeout(1500);
        }
        await checkRadio(frame, resp.alteredMeaning, page);
      }
    }
  }
}

async function main() {
  const args = parseArgs();
  const answers = JSON.parse(fs.readFileSync(path.resolve(args.answersPath), 'utf8'));
  
  console.log(JSON.stringify({ dryRun: args.dryRun, answers }, null, 2));
  if (args.dryRun) return;

  const { browser, endpoint } = await connect();

  try {
    const ctx = browser.contexts()[0];
    const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
    const frame = await getTaskFrame(page);

    // Step 1: Formality
    await checkRadio(frame, answers.formality, page);

    // Step 2: Q1
    await checkRadio(frame, answers.q1, page);

    // Step 3: Fill each response
    const respNames = ['A', 'B', 'C'];
    const tabNames = ['Response A', 'Response B', 'Response C'];
    for (let i = 0; i < respNames.length; i++) {
      const resp = answers.responses[respNames[i]];
      if (!resp) continue;
      await fillResponse(frame, page, tabNames[i], resp, answers.q1);
    }

    // Step 4: Pairwise comparisons - handle varying tab name order
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
          if (tab) { tab.click(); return true; }
          return false;
        }, tabName);
        if (found) {
          await page.waitForTimeout(400);
          clicked = true;
          break;
        }
      }
      if (clicked) await checkRadio(frame, val, page);
    }

    // Step 5: Observation
    if (answers.observation) {
      await frame.locator('textarea').first().fill(answers.observation);
    }

    // Step 6: Submit
    if (args.submit) {
      await frame.locator('button:has-text("Submit")').first().click({ timeout: 3000 }).catch(async () => {
        await page.getByLabel('Submit Task').click({ timeout: 3000 });
      });
      await page.waitForTimeout(2000);
      console.log('Submitted.');
    }

    console.log('Done.');
  } finally {
    // Do not close — CDP browser.close() sends Browser.close command and kills the process
  }
}

main().catch(e => { console.error(e.stack || e.message); process.exit(1); });
