#!/usr/bin/env node
/**
 * One-shot fill via React onChange — proven in conversation-2026-06-11-163815.md (2/2 + 1/1).
 * Run alone: stop task_bridge first to avoid CDP contention.
 */
const fs = require('fs');
const path = require('path');
const { getFrame } = require('./pr_automation_helper');
const { verifyFormSubmittableOn } = require('./verify_task');
const { assertRatingsReady } = require('./task_utils');

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

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

const COMPARE_MAP = {
  Same: 'A=B',
  'Left Much Better': 'A>>>B',
  'Left Better': 'A>>B',
  'Left Slightly Better': 'A>B',
  'Right Slightly Better': 'B>A',
  'Right Better': 'B>>A',
  'Right Much Better': 'B>>>A',
};

async function getPropsKey(frm1) {
  return frm1.evaluate(() =>
    Object.keys(document.querySelector('input[type=radio]') || {}).find((k) => k.startsWith('__reactProps'))
  );
}

async function fillPanelRadios(frm1, panelId, entries, propsKey) {
  for (const { val, cat } of entries) {
    let found = await frm1.evaluate(
      (p, v) => !!document.getElementById(p)?.querySelector(`input[type=radio][value="${v}"]`),
      panelId,
      val
    );
    if (!found) {
      await sleep(600);
      found = await frm1.evaluate(
        (p, v) => !!document.getElementById(p)?.querySelector(`input[type=radio][value="${v}"]`),
        panelId,
        val
      );
    }
    if (!found) {
      console.log('  SKIP', cat, val);
      continue;
    }
    const result = await frm1.evaluate(
      (p, v, pk) => {
        const radio = document.getElementById(p)?.querySelector(`input[type=radio][value="${v}"]`);
        if (!radio) return 'not found';
        const props = radio[pk];
        if (!props?.onChange) return 'no onChange';
        const evt = {
          target: { value: v, checked: true, type: 'radio', name: radio.name },
          currentTarget: { value: v, checked: true, type: 'radio', name: radio.name },
          preventDefault: () => {},
          stopPropagation: () => {},
          nativeEvent: new Event('change'),
          type: 'change',
          persist: () => {},
        };
        props.onChange(evt);
        return 'ok';
      },
      panelId,
      val,
      propsKey
    );
    console.log(' ', cat, val, result);
    await sleep(400);
  }
}

function buildResponseEntries(rating) {
  const entries = [
    { val: VALUE_MAP[rating.instructionFollowing], cat: 'IF' },
    { val: VALUE_MAP[rating.localization], cat: 'Localization' },
    { val: VALUE_MAP[rating.concision], cat: 'Concision' },
  ];
  if (rating.description) {
    entries.push({ val: VALUE_MAP[rating.description] || 'make_shorter', cat: 'Description' });
  }
  entries.push(
    { val: VALUE_MAP[rating.truthfulness], cat: 'Truthfulness' },
    { val: VALUE_MAP[rating.satisfaction], cat: 'Satisfaction' }
  );
  return entries.filter((e) => e.val);
}

async function clickResponseTab(frm1, key) {
  await frm1.evaluate((k) => {
    const tabs = [...document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')];
    const tab = tabs.find((t) => new RegExp(k.replace('Response ', 'response '), 'i').test(t.textContent));
    if (tab) tab.click();
  }, key);
  await sleep(500);
  await frm1.evaluate(() => {
    const c = document.querySelector('.Box-sc-18eybku-0.autPh');
    if (c) c.scrollTop = 0;
  });
  await sleep(300);
}

async function main() {
  const { ratings } = assertRatingsReady();
  const { browser, page, frm1 } = await getFrame();
  if (!frm1) {
    await browser.disconnect();
    console.error('FATAL: task-editor frame not found');
    process.exit(1);
  }
  await page.setViewport({ width: 1919, height: 1079 });

  const propsKey = await getPropsKey(frm1);
  if (!propsKey) {
    await browser.disconnect();
    console.error('FATAL: no __reactProps on radio');
    process.exit(1);
  }

  const panelIds = await frm1.evaluate(() => {
    const tabs = [...document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')];
    const out = {};
    for (const t of tabs) {
      const text = t.textContent.trim();
      const pid = t.getAttribute('aria-controls');
      if (/response a/i.test(text)) out['Response A'] = pid;
      if (/response b/i.test(text)) out['Response B'] = pid;
    }
    return out;
  });
  console.log('Panel IDs:', panelIds);

  for (const key of ['Response A', 'Response B']) {
    console.log(`Filling ${key}...`);
    await clickResponseTab(frm1, key);
    await fillPanelRadios(frm1, panelIds[key], buildResponseEntries(ratings.responses[key]), propsKey);
  }

  console.log('Filling Compare...');
  const compVal = COMPARE_MAP[ratings.comparisons['A and B']] || 'A=B';
  const compPanelId = await frm1.evaluate(() => {
    const tabList = document.querySelectorAll('[role=tablist]')[1];
    const tab = tabList?.querySelector('[role=tab]');
    return tab?.getAttribute('aria-controls') || null;
  });
  if (compPanelId) {
    const compResult = await frm1.evaluate(
      (p, v, pk) => {
        const radio = document.getElementById(p)?.querySelector(`input[type=radio][value="${v}"]`);
        if (!radio) return 'not found';
        const props = radio[pk];
        if (!props?.onChange) return 'no onChange';
        const evt = {
          target: { value: v, checked: true, type: 'radio', name: radio.name },
          currentTarget: { value: v, checked: true, type: 'radio', name: radio.name },
          preventDefault: () => {},
          stopPropagation: () => {},
          nativeEvent: new Event('change'),
          type: 'change',
          persist: () => {},
        };
        props.onChange(evt);
        return 'ok';
      },
      compPanelId,
      compVal,
      propsKey
    );
    console.log('Compare', compVal, compResult);
  }

  console.log('Filling Rationale...');
  const rationaleResult = await frm1.evaluate((text) => {
    const textarea = document.querySelector('textarea');
    if (!textarea) return 'no textarea';
    const pk = Object.keys(textarea).find((k) => k.startsWith('__reactProps'));
    if (pk && textarea[pk]?.onChange) {
      textarea[pk].onChange({
        target: { value: text },
        currentTarget: { value: text },
        preventDefault: () => {},
        stopPropagation: () => {},
        nativeEvent: new Event('input'),
        type: 'input',
        persist: () => {},
      });
    }
    textarea.value = text;
    return `ok len=${text.length}`;
  }, ratings.rationale);
  console.log('Rationale:', rationaleResult);

  await sleep(2000);
  const verify = await verifyFormSubmittableOn(page, frm1);
  const completions = await frm1.evaluate(() =>
    [...document.querySelectorAll('h3')].map((h) => h.textContent.trim()).filter((t) => /complete/i.test(t))
  );
  console.log('Completions:', completions);
  console.log('Form verify:', JSON.stringify(verify));

  const RUNS = path.join(__dirname, 'runs');
  fs.mkdirSync(RUNS, { recursive: true });
  if (verify.ok) {
    const flag = { fingerprint: ratings.fingerprint, at: new Date().toISOString(), form: verify.form };
    fs.writeFileSync(path.join(RUNS, 'form_filled.flag'), JSON.stringify(flag, null, 2));
    fs.writeFileSync(path.join(RUNS, 'submittable.flag'), JSON.stringify(flag, null, 2));
    console.log('FLAGS written — form ready');
  } else {
    console.error('FATAL: form not submittable');
    process.exit(1);
  }

  await browser.disconnect();
}

main().catch((e) => {
  console.error('FATAL:', e.message);
  process.exit(1);
});
