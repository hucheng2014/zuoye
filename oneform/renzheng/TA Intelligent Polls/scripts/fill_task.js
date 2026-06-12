/**
 * fill_task.js — Fill the Intelligent Polls evaluation form with answers.
 *
 * Reads an answers JSON file and fills the task-editor iframe accordingly.
 * The Intelligent Polls form has these radio groups (in order):
 *
 *   1. proper_no_reply: "no_reply" | "yes_reply" | "consensus_reply"
 *   2. following: "not_following_instructions" | "following_instructions"
 *   3. composition: "bad" | "good"
 *   4. comprehensiveness: "not_comprehensive" | "comprehensive"
 *   5. groundedness: "not_truthful" | "truthful"
 *   6. localization: "no" | "yes"
 *   7. harmfulness: "harmful" | "maybe_harmful" | "not_harmful"
 *   8. satisfaction: "not_satisfying" | "slightly_satisfying" | "satisfying" | "highly_satisfying"
 *
 * If proper_no_reply = "no_reply" AND the response is empty,
 * only the first radio is filled; the rest are skipped.
 *
 * Usage:
 *   node scripts/fill_task.js --answers runs/task-001-answers.json [--dry-run] [--submit]
 */

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

/**
 * React-compatible radio check: fires native + React synthetic events.
 */
async function reactSetRadio(frame, selector) {
  return frame.evaluate(sel => {
    const all = Array.from(document.querySelectorAll(sel));
    const el = all.find(e => e.offsetParent !== null) || all[0];
    if (!el) return false;
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

  // Prefer visible radio buttons
  for (let i = 0; i < count; i++) {
    const el = all.nth(i);
    const visible = await el.isVisible().catch(() => false);
    if (visible) {
      try { await el.click({ force: true, timeout: 2000 }); } catch {}
      const name = await el.getAttribute('name').catch(() => null);
      const sel = name
        ? `input[type="radio"][name="${name}"][value="${value}"]`
        : `input[type="radio"][value="${value}"]`;
      await reactSetRadio(frame, sel);
      await page.waitForTimeout(300);
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
    await reactSetRadio(frame, sel);
    await page.waitForTimeout(300);
    return;
  }
  throw new Error(`Radio value "${value}" not found`);
}

async function main() {
  const args = parseArgs();
  const answers = JSON.parse(fs.readFileSync(path.resolve(args.answersPath), 'utf8'));

  console.log('Answers loaded:', JSON.stringify(answers, null, 2));
  if (args.dryRun) {
    console.log('[DRY RUN] No form interaction.');
    return;
  }

  const { browser, endpoint } = await connect();

  try {
    const ctx = browser.contexts()[0];
    const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
    const frame = await getTaskFrame(page);

    // Scroll to top of form to ensure all elements are accessible
    await frame.evaluate(() => window.scrollTo(0, 0)).catch(() => {});
    await page.waitForTimeout(300);

    // 1. Proper No Reply
    console.log('[fill] Setting proper_no_reply:', answers.proper_no_reply);
    await checkRadio(frame, answers.proper_no_reply, page);

    // If no poll is appropriate and response is empty, we only need the first radio
    // But we still fill other dimensions if they are present in the answers
    // (the form may still show them if a poll was generated despite being inappropriate)

    // 2. Following Instructions
    if (answers.following) {
      console.log('[fill] Setting following:', answers.following);
      await checkRadio(frame, answers.following, page);
    }

    // 3. Composition
    if (answers.composition) {
      console.log('[fill] Setting composition:', answers.composition);
      await checkRadio(frame, answers.composition, page);
    }

    // 4. Comprehensiveness
    if (answers.comprehensiveness) {
      console.log('[fill] Setting comprehensiveness:', answers.comprehensiveness);
      await checkRadio(frame, answers.comprehensiveness, page);
    }

    // 5. Groundedness
    if (answers.groundedness) {
      console.log('[fill] Setting groundedness:', answers.groundedness);
      await checkRadio(frame, answers.groundedness, page);
    }

    // 6. Localization
    if (answers.localization !== undefined) {
      console.log('[fill] Setting localization:', answers.localization);
      await checkRadio(frame, answers.localization, page);
    }

    // 7. Harmfulness
    if (answers.harmfulness) {
      console.log('[fill] Setting harmfulness:', answers.harmfulness);
      await checkRadio(frame, answers.harmfulness, page);
    }

    // 8. Satisfaction
    if (answers.satisfaction) {
      console.log('[fill] Setting satisfaction:', answers.satisfaction);
      await checkRadio(frame, answers.satisfaction, page);
    }

    // Verify all selections
    const checked = await frame.locator('input:checked').evaluateAll(els =>
      els.map(e => ({ type: e.type, name: e.name, value: e.value }))
    );
    console.log('[fill] Current checked state:', JSON.stringify(checked));

    // Submit if requested
    if (args.submit) {
      await frame.getByRole('button', { name: /^Submit$/ }).click({ timeout: 5000 });
      console.log('[fill] Clicked Submit in frame.');
      await page.waitForTimeout(2000);

      // Click confirmation dialog if present
      const confirmBtn = page.locator('#starshot_submit_task_button');
      try {
        await confirmBtn.waitFor({ state: 'visible', timeout: 5000 });
        await confirmBtn.click();
        console.log('[fill] Clicked confirm submit.');
      } catch (e) {
        console.log('[fill] No confirm dialog:', e.message.split('\n')[0]);
      }
    }

    console.log('[fill] Done.');
  } finally {
    // Do NOT close browser — CDP browser.close() kills the browser process
  }
}

main().catch(e => { console.error(e.stack || e.message); process.exit(1); });
