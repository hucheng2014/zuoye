#!/usr/bin/env node
/**
 * Fill + verify + submit current task. Uses panel-scoped React onChange + .radio-button click.
 */
const fs = require('fs');
const path = require('path');
const { getFrame, sleep, scrollTaskEditorToResponses } = require('./pr_automation_helper');
const { assertRatingsReady } = require('./task_utils');
const { verifyFormSubmittableOn, verifyBeforeSubmitOn } = require('./verify_task');
const { SUBMIT_AT_SEC } = require('./config');

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

async function reactRadio(frm1, panelId, val, propsKey) {
  return frm1.evaluate(
    (pid, v, pk) => {
      const radio = document.getElementById(pid)?.querySelector(`input[type=radio][value="${v}"]`);
      if (!radio) return 'not found';
      const props = radio[pk];
      if (props?.onChange) {
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
      }
      const btn = radio.closest('.radio-button') || radio.closest('.radio-button__wrapper');
      if (btn) btn.click();
      return radio.checked ? 'ok' : 'unchecked';
    },
    panelId,
    val,
    propsKey
  );
}

async function mouseClickTab(frm1, matchRe) {
  const page = frm1.page();
  const fbox = await (await frm1.frameElement()).boundingBox();
  const pos = await frm1.evaluate((reSrc) => {
    const re = new RegExp(reSrc, 'i');
    const lists = document.querySelectorAll('[role=tablist]');
    for (const list of lists) {
      for (const tab of list.querySelectorAll('[role=tab]')) {
        if (re.test(tab.textContent)) {
          const r = tab.getBoundingClientRect();
          return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
        }
      }
    }
    return null;
  }, matchRe);
  if (!pos || !fbox) return false;
  await page.mouse.click(fbox.x + pos.x, fbox.y + pos.y);
  await sleep(500);
  return true;
}

async function fillPanel(frm1, panelId, rating, propsKey) {
  const order = [
    ['instructionFollowing', rating.instructionFollowing],
    ['localization', rating.localization],
    ['concision', rating.concision],
    ['description', rating.description],
    ['truthfulness', rating.truthfulness],
    ['satisfaction', rating.satisfaction],
  ];
  for (const [field, label] of order) {
    if (!label) continue;
    const val = VALUE_MAP[label];
    if (!val) throw new Error(`unknown ${label}`);
    if (field === 'description') {
      await frm1
        .waitForFunction(
          (pid) => !!document.getElementById(pid)?.querySelector('input[value=make_shorter],input[value=make_longer]'),
          { timeout: 8000 },
          panelId
        )
        .catch(() => {});
    }
    const res = await reactRadio(frm1, panelId, val, propsKey);
    console.log(`  ${field}=${label} -> ${res}`);
    await sleep(350);
  }
}

async function readTpt(page) {
  return page.evaluate(() => {
    const m = (document.body.innerText || '').match(/Time worked:\s*(\d+)/i);
    return m ? parseInt(m[1], 10) : -1;
  });
}

async function main() {
  const { ratings } = assertRatingsReady();
  const { browser, page, frm1 } = await getFrame();
  if (!frm1) throw new Error('no task-editor frame');
  await page.setViewport({ width: 1919, height: 1079 });

  const propsKey = await getPropsKey(frm1);
  if (!propsKey) throw new Error('no __reactProps');

  const panelIds = await frm1.evaluate(() => {
    const out = {};
    for (const t of document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')) {
      const pid = t.getAttribute('aria-controls');
      if (/response a/i.test(t.textContent)) out['Response A'] = pid;
      if (/response b/i.test(t.textContent)) out['Response B'] = pid;
    }
    return out;
  });
  console.log('panels', panelIds);

  // Fill Response A
  console.log('Fill Response A');
  await mouseClickTab(frm1, 'response a');
  await scrollTaskEditorToResponses(frm1);
  await fillPanel(frm1, panelIds['Response A'], ratings.responses['Response A'], propsKey);

  // Commit A -> B
  console.log('Commit A -> B');
  await mouseClickTab(frm1, 'response b');
  await scrollTaskEditorToResponses(frm1);
  await fillPanel(frm1, panelIds['Response B'], ratings.responses['Response B'], propsKey);

  // Commit B -> Compare
  console.log('Commit B -> Compare');
  await mouseClickTab(frm1, 'a and b');
  await sleep(500);

  const compPanel = await frm1.evaluate(() =>
    document.querySelectorAll('[role=tablist]')[1]?.querySelector('[role=tab]')?.getAttribute('aria-controls')
  );
  const compVal = COMPARE_MAP[ratings.comparisons['A and B']] || 'A=B';
  console.log('Compare', compVal, await reactRadio(frm1, compPanel, compVal, propsKey));

  await frm1.evaluate((text) => {
    const ta = document.querySelector('textarea');
    const pk = Object.keys(ta || {}).find((k) => k.startsWith('__reactProps'));
    if (pk && ta[pk]?.onChange) {
      ta[pk].onChange({
        target: { value: text },
        currentTarget: { value: text },
        preventDefault: () => {},
        stopPropagation: () => {},
        nativeEvent: new Event('input'),
        type: 'input',
        persist: () => {},
      });
    }
    if (ta) ta.value = text;
  }, ratings.rationale);

  await sleep(2000);
  let verify = await verifyFormSubmittableOn(page, frm1);
  console.log('Verify1', JSON.stringify(verify));

  if (!verify.ok) {
    // Retry: click compare tab again to force commit
    await mouseClickTab(frm1, 'response a');
    await mouseClickTab(frm1, 'response b');
    await mouseClickTab(frm1, 'a and b');
    await sleep(2000);
    verify = await verifyFormSubmittableOn(page, frm1);
    console.log('Verify2', JSON.stringify(verify));
  }

  if (!verify.ok) {
    console.error('FATAL: form incomplete', verify.issues);
    process.exit(1);
  }

  const RUNS = path.join(__dirname, 'runs');
  fs.mkdirSync(RUNS, { recursive: true });
  const flag = { fingerprint: ratings.fingerprint, at: new Date().toISOString(), form: verify.form };
  fs.writeFileSync(path.join(RUNS, 'form_filled.flag'), JSON.stringify(flag, null, 2));
  fs.writeFileSync(path.join(RUNS, 'submittable.flag'), JSON.stringify(flag, null, 2));

  // Wait for TPT >= 720
  let tpt = await readTpt(page);
  console.log(`TPT=${tpt}s, waiting for ${SUBMIT_AT_SEC}s...`);
  while (tpt >= 0 && tpt < SUBMIT_AT_SEC) {
    const remain = SUBMIT_AT_SEC - tpt;
    const wait = Math.min(remain + 5, 120);
    console.log(`  sleep ${wait}s (TPT=${tpt})`);
    await sleep(wait * 1000);
    tpt = await readTpt(page);
  }

  const pre = await verifyBeforeSubmitOn(page, frm1, { skipRatings: false });
  if (!pre.ok) {
    console.error('FATAL pre-submit', pre.issues);
    process.exit(1);
  }

  console.log('Clicking Submit...');
  const clicked = await frm1.evaluate(() => {
    const btn =
      document.querySelector('.submit-button') ||
      [...document.querySelectorAll('button')].find((b) => b.textContent.trim() === 'Submit');
    if (!btn || btn.disabled) return { ok: false, label: btn?.textContent };
    btn.click();
    return { ok: true, label: btn.textContent.trim() };
  });
  if (!clicked.ok) throw new Error(`Submit failed: ${clicked.label}`);

  await sleep(2000);
  // Confirm modal
  await page.evaluate(() => {
    for (const btn of document.querySelectorAll('button')) {
      if (btn.textContent.trim() === 'Submit' && btn.offsetParent) {
        btn.click();
        return;
      }
    }
  });
  await frm1.evaluate(() => {
    for (const btn of document.querySelectorAll('button')) {
      if (btn.textContent.trim() === 'Submit' && btn.offsetParent) {
        btn.click();
        return;
      }
    }
  }).catch(() => {});

  await sleep(5000);
  const after = await page.evaluate(() => /successfully submitted/i.test(document.body.innerText));
  console.log('Submitted:', after);
  await browser.disconnect();
  process.exit(after ? 0 : 1);
}

main().catch((e) => {
  console.error('FATAL', e.message);
  process.exit(1);
});
