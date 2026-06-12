const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { submitAndNext } = require('./submit_task');

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
  const out = { dryRun: false, submit: false };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--answers') out.answersPath = args[++i];
    else if (args[i] === '--dry-run') out.dryRun = true;
    else if (args[i] === '--submit') out.submit = true;
    else throw new Error(`Unknown argument: ${args[i]}`);
  }
  if (!out.answersPath) throw new Error('Usage: node fill_task.js --answers FILE [--dry-run|--submit]');
  return out;
}

async function connect() {
  let lastError;
  for (const endpoint of CDP_ENDPOINTS) {
    try {
      const browser = await chromium.connectOverCDP(endpoint);
      return { browser, endpoint };
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError || new Error('No CDP endpoint available');
}

async function getTaskFrame(page) {
  const byUrl = page.frames().find((f) => f.url().includes('/task-editor/'));
  if (byUrl) return byUrl;
  for (const frame of page.frames()) {
    const text = await frame.locator('body').innerText({ timeout: 1000 }).catch(() => '');
    if (text.includes('Response A1') && text.includes('Pairwise Comparison')) return frame;
  }
  throw new Error('Task frame not found');
}

async function readInputs(frame) {
  return frame.locator('input, textarea, button').evaluateAll((elements) =>
    elements.map((el, index) => ({
      index,
      tag: el.tagName,
      type: el.getAttribute('type'),
      name: el.getAttribute('name'),
      value: el.value || '',
      checked: Boolean(el.checked),
      ariaLabel: el.getAttribute('aria-label'),
      text: (el.innerText || el.textContent || '').trim(),
    }))
  );
}

async function listTabLabels(frame) {
  return frame.getByRole('tab').evaluateAll((els) =>
    els.map((el) => (el.textContent || '').trim()).filter(Boolean)
  );
}

async function detectResponseTabs(frame) {
  const labels = await listTabLabels(frame);
  const tabs = [];
  for (let i = 0; i < RESPONSE_TABS.length; i++) {
    if (labels.includes(RESPONSE_TABS[i])) {
      tabs.push({ tab: RESPONSE_TABS[i], key: RESPONSE_KEYS[i] });
    }
  }
  if (!tabs.length) throw new Error(`No response tabs found (labels: ${labels.join(', ')})`);
  return tabs;
}

function buildPlan(inputs, answers, activeTabs) {
  const radioGroups = [];
  for (const input of inputs) {
    if (input.type === 'radio') {
      let group = radioGroups.find((item) => item.name === input.name);
      if (!group) {
        group = { name: input.name, inputs: [] };
        radioGroups.push(group);
      }
      group.inputs.push(input);
    }
  }

  const usefulRadioGroups = radioGroups.filter((group) => group.inputs.length >= 2);
  const lastTopicGroup = usefulRadioGroups.find((group) =>
    group.inputs.some((input) => LAST_TOPIC_VALUES.has(input.value))
  );
  if (!lastTopicGroup) throw new Error('Last topic radio group not found');

  const ratingGroups = usefulRadioGroups.filter((group) => group !== lastTopicGroup);
  const pairwiseGroup = ratingGroups.find((group) =>
    group.inputs.some((input) => ['A>>>B', 'A>B', 'A=B', 'B>A', 'B>>>A'].includes(input.value))
  );
  if (!pairwiseGroup) throw new Error('Pairwise radio group not found');

  const perResponseGroups = ratingGroups.filter((group) => group !== pairwiseGroup);
  const expected = activeTabs.length * FIELD_ORDER.length;
  if (perResponseGroups.length < expected) {
    throw new Error(`Expected ${expected} rating groups (${activeTabs.length} tabs), found ${perResponseGroups.length}`);
  }

  const responsePlans = [];
  let offset = 0;
  for (const { tab, key } of activeTabs) {
    const responseAnswers = answers[key];
    if (!responseAnswers) throw new Error(`Missing answers for ${key}`);
    const radio = [];
    for (const field of FIELD_ORDER) {
      radio.push({
        field,
        group: perResponseGroups[offset++],
        value: responseAnswers[field],
      });
    }
    responsePlans.push({ key, tab, radio });
  }

  return {
    lastTopic: { group: lastTopicGroup, value: answers.lastTopic },
    responsePlans,
    pairwise: { group: pairwiseGroup, value: answers.pairwise },
    observation: answers.observation || '',
    textarea: inputs.find((input) => input.tag === 'TEXTAREA'),
  };
}

async function clickInput(frame, input) {
  await frame.locator(`input[name="${input.name}"][value="${input.value}"]`).first().evaluate((el) => el.click());
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
  await frame.page().waitForTimeout(200);
}

async function applyPlan(frame, plan) {
  const lastTopicTarget = plan.lastTopic.group.inputs.find((input) => input.value === plan.lastTopic.value);
  if (!lastTopicTarget) throw new Error(`No last topic value ${plan.lastTopic.value}`);
  await clickInput(frame, lastTopicTarget);

  for (const response of plan.responsePlans) {
    await clickTab(frame, response.tab);
    for (const item of response.radio) {
      const target = item.group.inputs.find((input) => input.value === item.value);
      if (!target) throw new Error(`No radio value ${item.value} for ${response.key}.${item.field}`);
      await clickInput(frame, target);
    }
  }

  await clickTab(frame, 'A and B');
  const pairwiseTarget = plan.pairwise.group.inputs.find((input) => input.value === plan.pairwise.value);
  if (!pairwiseTarget) throw new Error(`No pairwise value ${plan.pairwise.value}`);
  await clickInput(frame, pairwiseTarget);

  if (plan.observation) {
    await fillObservation(frame, plan.observation);
  }
}

async function fillObservation(frame, text) {
  await clickTab(frame, 'A and B');
  await frame.page().waitForTimeout(300);

  const textareas = frame.locator('textarea');
  const count = await textareas.count();
  let filled = false;

  for (let i = 0; i < count; i++) {
    const box = textareas.nth(i);
    const meta = await box.evaluate((el) => ({
      h: el.offsetHeight,
      ph: el.placeholder || '',
      vis: el.offsetParent !== null,
    })).catch(() => ({ h: 0, ph: '', vis: false }));

    // 跳过 AI 助手隐藏框；选可见且足够高的评语框
    if (!meta.vis || meta.h < 40 || /refine the current design/i.test(meta.ph)) continue;

    await box.scrollIntoViewIfNeeded().catch(() => {});
    await box.click({ timeout: 2000 }).catch(() => {});
    await box.fill(text, { timeout: 5000 });
    const val = await box.inputValue().catch(() => '');
    if (val.length > 10) {
      filled = true;
      break;
    }
  }

  if (!filled) {
    // fallback: 找 "observations" 附近的 textarea
    const near = frame.locator('textarea:near(:text("observations"), 200)').first();
    if (await near.count()) {
      await near.fill(text, { timeout: 5000 });
      filled = true;
    }
  }

  if (!filled) throw new Error('Observation textarea not found or fill failed');
}

function summarizePlan(plan) {
  return {
    lastTopic: plan.lastTopic.value,
    responses: plan.responsePlans.map((response) => ({
      key: response.key,
      tab: response.tab,
      radio: response.radio.map((item) => ({
        field: item.field,
        value: item.value,
        available: item.group.inputs.map((input) => input.value),
      })),
    })),
    pairwise: {
      value: plan.pairwise.value,
      available: plan.pairwise.group.inputs.map((input) => input.value),
    },
    observation: plan.observation,
  };
}

async function submitTask(frame, page) {
  await submitAndNext(page, frame, { clickNext: true });
}

async function main() {
  const args = parseArgs();
  const answers = JSON.parse(fs.readFileSync(path.resolve(args.answersPath), 'utf8'));
  if (answers.fingerprint) {
    const { extractTask } = require('./task_utils');
    const task = await extractTask();
    if (task.fingerprint !== answers.fingerprint) {
      throw new Error(
        `TASK CHANGED: answers fingerprint=${answers.fingerprint} but page=${task.fingerprint}. Refusing to fill stale answers.`
      );
    }
  }
  const { browser, endpoint } = await connect();
  try {
    const context = browser.contexts()[0];
    if (!context) throw new Error('No browser context found');
    const page = context.pages().find((p) => p.url().includes('starshot.scilliance.com')) || context.pages()[0];
    if (!page) throw new Error('No page found');
    const frame = await getTaskFrame(page);
    const activeTabs = await detectResponseTabs(frame);
    const inputs = await readInputs(frame);
    const plan = buildPlan(inputs, answers, activeTabs);
    console.log(JSON.stringify({ cdpEndpoint: endpoint, dryRun: args.dryRun, plan: summarizePlan(plan) }, null, 2));

    if (!args.dryRun) {
      await applyPlan(frame, plan);
    }
  } finally {
    await browser.close();
  }

  if (!args.dryRun && args.submit) {
    const { spawnSync } = require('child_process');
    const root = path.resolve(__dirname, '..', '..');
    const check = spawnSync(
      'node',
      [path.join(__dirname, 'check_form.js'), '--answers', path.resolve(args.answersPath)],
      { cwd: root, encoding: 'utf8' }
    );
    if (check.stdout) process.stdout.write(check.stdout);
    if (check.status !== 0) {
      if (check.stderr) process.stderr.write(check.stderr);
      throw new Error('Verify failed — aborting submit');
    }
    const submit = spawnSync('node', [path.join(__dirname, 'submit_task.js')], { cwd: root, encoding: 'utf8' });
    if (submit.stdout) process.stdout.write(submit.stdout);
    if (submit.stderr) process.stderr.write(submit.stderr);
    if (submit.status !== 0) throw new Error('submit_task.js failed');
  }
}

Promise.race([
  main(),
  new Promise((_, reject) => setTimeout(() => reject(new Error('FILL_TASK_TIMEOUT')), 90000)),
]).catch((error) => {
  console.error(`[FATAL] ${error.stack || error.message}`);
  process.exit(1);
});
