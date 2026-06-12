/**
 * check_form.js — 填表后复核：对照 current-answers.json 校验页面选项与评语
 *
 * Usage:
 *   node TAMESSAGE/scripts/check_form.js [--answers TAMESSAGE/runs/current-answers.json]
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const CDP_ENDPOINTS = [
  process.env.TAMESSAGE_CDP_ENDPOINT || 'http://127.0.0.1:9233',
  'http://127.0.0.1:9232',
];

const LAST_TOPIC_VALUES = new Set([
  'conversation_ended', 'seeking_facts', 'auto_generated',
  'incomprehensible', 'personal_information', 'harmful', 'other',
]);

const FIELD_ORDER = [
  'harmfulness', 'groundedness', 'contextualFit', 'conciseness',
  'tone', 'naturalness', 'localization', 'personalization',
];

const RESPONSE_TABS = ['Response A1', 'Response A2', 'Response B1', 'Response B2'];
const RESPONSE_KEYS = ['responseA1', 'responseA2', 'responseB1', 'responseB2'];

function parseArgs() {
  const args = process.argv.slice(2);
  const out = { answersPath: path.join(__dirname, '..', 'runs', 'current-answers.json') };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--answers') out.answersPath = args[++i];
  }
  return out;
}

async function connect() {
  let lastError;
  for (const endpoint of CDP_ENDPOINTS) {
    try {
      return { browser: await chromium.connectOverCDP(endpoint), endpoint };
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError || new Error('No CDP endpoint available');
}

function getTaskFrame(page) {
  return page.frames().find((f) => f.url().includes('/task-editor/')) || null;
}

async function listTabLabels(frame) {
  return frame.getByRole('tab').evaluateAll((els) =>
    els.map((el) => (el.textContent || '').trim()).filter(Boolean)
  );
}

async function clickTab(frame, name) {
  const clicked = await frame.getByRole('tab').evaluateAll((els, label) => {
    const el = els.find((item) => (item.textContent || '').trim() === label);
    if (el) {
      el.click();
      return true;
    }
    return false;
  }, name);
  if (!clicked) throw new Error(`Tab not found: ${name}`);
  await frame.page().waitForTimeout(250);
}

async function readCheckedRadios(frame) {
  return frame.locator('input[type="radio"]:checked').evaluateAll((els) =>
    els.map((el) => ({ name: el.name, value: el.value, visible: el.offsetParent !== null }))
  );
}

async function readObservation(frame) {
  const textareas = frame.locator('textarea');
  const count = await textareas.count();
  for (let i = 0; i < count; i++) {
    const box = textareas.nth(i);
    const meta = await box.evaluate((el) => ({
      h: el.offsetHeight,
      ph: el.placeholder || '',
      vis: el.offsetParent !== null,
      val: el.value || '',
    })).catch(() => null);
    if (!meta || !meta.vis || meta.h < 40 || /refine the current design/i.test(meta.ph)) continue;
    return meta.val;
  }
  return '';
}

async function main() {
  const args = parseArgs();
  const answers = JSON.parse(fs.readFileSync(path.resolve(args.answersPath), 'utf8'));
  const { browser, endpoint } = await connect();

  try {
    const page = browser.contexts()[0].pages().find((p) => p.url().includes('starshot')) || browser.contexts()[0].pages()[0];
    const frame = getTaskFrame(page);
    if (!frame) throw new Error('Task frame not found');

    const labels = await listTabLabels(frame);
    const activeTabs = RESPONSE_TABS.filter((tab, i) => labels.includes(tab)).map((tab, i) => ({
      tab,
      key: RESPONSE_KEYS[RESPONSE_TABS.indexOf(tab)],
    }));

    const issues = [];
    const checked = await readCheckedRadios(frame);

    const lastTopic = checked.find((c) => LAST_TOPIC_VALUES.has(c.value));
    if (!lastTopic) issues.push('lastTopic: no selection');
    else if (lastTopic.value !== answers.lastTopic) {
      issues.push(`lastTopic: expected ${answers.lastTopic}, got ${lastTopic.value}`);
    } else {
      console.log(`✅ lastTopic: ${lastTopic.value}`);
    }

    for (const { tab, key } of activeTabs) {
      await clickTab(frame, tab);
      const tabChecked = await readCheckedRadios(frame);
      const responseAnswers = answers[key];
      if (!responseAnswers) {
        issues.push(`${key}: missing in answers file`);
        continue;
      }
      for (const field of FIELD_ORDER) {
        const expected = responseAnswers[field];
        const found = tabChecked.find((c) => c.value === expected);
        if (!found) {
          const actual = tabChecked.map((c) => c.value).join(', ');
          issues.push(`${key}.${field}: expected ${expected}, radios on tab: [${actual}]`);
        }
      }
      if (!issues.some((x) => x.startsWith(key))) {
        console.log(`✅ ${tab}: all ${FIELD_ORDER.length} dimensions match`);
      }
    }

    await clickTab(frame, 'A and B');
    const pairwiseChecked = await readCheckedRadios(frame);
    const pairwise = pairwiseChecked.find((c) => ['A>>>B', 'A>B', 'A=B', 'B>A', 'B>>>A'].includes(c.value));
    if (!pairwise) issues.push('pairwise: no selection');
    else if (pairwise.value !== answers.pairwise) {
      issues.push(`pairwise: expected ${answers.pairwise}, got ${pairwise.value}`);
    } else {
      console.log(`✅ pairwise: ${pairwise.value}`);
    }

    const obs = await readObservation(frame);
    const expectedObs = (answers.observation || '').trim();
    if (!expectedObs) {
      console.log('⚠️ observation: not required in answers');
    } else if (obs.length < 20) {
      issues.push(`observation: empty or too short (${obs.length} chars)`);
    } else if (!obs.includes(expectedObs.slice(0, 40))) {
      issues.push(`observation: content mismatch (page ${obs.length} chars)`);
    } else {
      console.log(`✅ observation: ${obs.length} chars`);
    }

    const totalRadios = await frame.locator('input[type="radio"]').count();
    const checkedCount = await frame.locator('input[type="radio"]:checked').count();
    console.log(`\nRadios: ${checkedCount} checked (page has ${totalRadios} total)`);
    console.log(`CDP: ${endpoint}`);

    if (issues.length) {
      console.log('\n❌ VERIFY FAILED:');
      for (const issue of issues) console.log(`  - ${issue}`);
      process.exit(1);
    }

    console.log('\n✅ ALL CHECKS PASSED — SAFE TO SUBMIT');
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(`[FATAL] ${error.stack || error.message}`);
  process.exit(1);
});
