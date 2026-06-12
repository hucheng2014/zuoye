#!/usr/bin/env node
/** Proven: ElementHandle.click() on .radio-button updates React 2/2 (conversation 08:22+) */
const fs = require('fs');
const path = require('path');
const { getFrame, sleep, scrollTaskEditorToResponses } = require('./pr_automation_helper');
const { assertRatingsReady } = require('./task_utils');
const { verifyFormSubmittableOn } = require('./verify_task');

const VALUE_MAP = {
  'Not following': 'not_following_instructions',
  'Partially following': 'partially_following_instructions',
  'Fully following': 'following_instructions',
  'Yes (issues present)': 'issues',
  'No (no issues)': 'no_issues',
  Bad: 'bad',
  Acceptable: 'acceptable',
  Good: 'good',
  'It could have been made shorter': 'make_shorter',
  'It could have been made longer': 'make_longer',
  'Not Truthful': 'not_truthful',
  'Partially Truthful': 'partially_truthful',
  Truthful: 'truthful',
  'Highly Unsatisfying': 'not_satisfying',
  'Slightly Unsatisfying': 'slightly_unsatisfying',
  'Slightly Satisfying': 'satisfying',
  'Highly Satisfying': 'highly_satisfying',
};

const COMPARE_MAP = { Same: 'A=B', 'Left Much Better': 'A>>>B', 'Left Better': 'A>>B', 'Left Slightly Better': 'A>B', 'Right Slightly Better': 'B>A', 'Right Better': 'B>>A', 'Right Much Better': 'B>>>A' };

async function clickRadioInPanel(frm1, panelId, value) {
  const handle = await frm1.evaluateHandle(
    (pid, val) => {
      const panel = document.getElementById(pid);
      const radio = panel?.querySelector(`input[type=radio][value="${val}"]`);
      if (!radio) return null;
      const btn = radio.closest('.radio-button');
      return btn && btn.offsetHeight > 0 ? btn : radio.closest('label') || radio;
    },
    panelId,
    value
  );
  const el = handle.asElement();
  if (!el) return false;
  await el.click();
  await sleep(200);
  return true;
}

async function fillResponse(frm1, key, rating, panelId) {
  console.log(`=== ${key} panel=${panelId} ===`);
  await frm1.evaluate((k) => {
    const tab = [...document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')].find((t) =>
      new RegExp(k.replace('Response ', 'response '), 'i').test(t.textContent)
    );
    tab?.click();
  }, key);
  await sleep(500);
  await scrollTaskEditorToResponses(frm1);

  const steps = [
    rating.instructionFollowing,
    rating.localization,
    rating.concision,
    rating.description,
    rating.truthfulness,
    rating.satisfaction,
  ].filter(Boolean);

  for (const label of steps) {
    const val = VALUE_MAP[label];
    if (!val) throw new Error(`unknown label ${label}`);
    if (label === rating.description) {
      await frm1.waitForFunction(
        (pid) => !!document.getElementById(pid)?.querySelector('input[value=make_shorter],input[value=make_longer]'),
        { timeout: 8000 },
        panelId
      ).catch(() => {});
    }
    const ok = await clickRadioInPanel(frm1, panelId, val);
    console.log(`  ${label} (${val}): ${ok ? 'OK' : 'FAIL'}`);
    await sleep(250);
  }
}

async function main() {
  const { ratings } = assertRatingsReady();
  const { browser, page, frm1 } = await getFrame();
  if (!frm1) throw new Error('no task-editor frame');
  await page.setViewport({ width: 1919, height: 1079 });

  const panelIds = await frm1.evaluate(() => {
    const out = {};
    for (const t of document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')) {
      const text = t.textContent.trim();
      const pid = t.getAttribute('aria-controls');
      if (/response a/i.test(text)) out['Response A'] = pid;
      if (/response b/i.test(text)) out['Response B'] = pid;
    }
    return out;
  });

  await fillResponse(frm1, 'Response A', ratings.responses['Response A'], panelIds['Response A']);
  await fillResponse(frm1, 'Response B', ratings.responses['Response B'], panelIds['Response B']);

  // Commit B → compare tab
  await frm1.evaluate(() => {
    document.querySelectorAll('[role=tablist]')[1]?.querySelector('[role=tab]')?.click();
  });
  await sleep(800);

  const compVal = COMPARE_MAP[ratings.comparisons['A and B']] || 'A=B';
  const compPanel = await frm1.evaluate(() => document.querySelectorAll('[role=tablist]')[1]?.querySelector('[role=tab]')?.getAttribute('aria-controls'));
  await clickRadioInPanel(frm1, compPanel, compVal);
  console.log('Compare', compVal);

  await frm1.evaluate((text) => {
    const ta = document.querySelector('textarea');
    const pk = Object.keys(ta || {}).find((k) => k.startsWith('__reactProps'));
    if (pk && ta[pk]?.onChange) {
      ta[pk].onChange({ target: { value: text }, currentTarget: { value: text }, preventDefault: () => {}, stopPropagation: () => {}, nativeEvent: new Event('input'), type: 'input', persist: () => {} });
    }
    if (ta) ta.value = text;
  }, ratings.rationale);
  console.log('Rationale len', ratings.rationale.length);

  await sleep(2000);
  const h3 = await frm1.evaluate(() => [...document.querySelectorAll('h3')].map((h) => h.textContent.trim()));
  console.log('Completions:', h3.filter((t) => /complete/i.test(t)));
  const verify = await verifyFormSubmittableOn(page, frm1);
  console.log('Verify:', JSON.stringify(verify));

  if (verify.ok) {
    const RUNS = path.join(__dirname, 'runs');
    fs.mkdirSync(RUNS, { recursive: true });
    const flag = { fingerprint: ratings.fingerprint, at: new Date().toISOString(), form: verify.form };
    fs.writeFileSync(path.join(RUNS, 'form_filled.flag'), JSON.stringify(flag, null, 2));
    fs.writeFileSync(path.join(RUNS, 'submittable.flag'), JSON.stringify(flag, null, 2));
    console.log('DONE — form submittable');
  } else {
    process.exit(1);
  }
  await browser.disconnect();
}

main().catch((e) => { console.error('FATAL', e.message); process.exit(1); });
