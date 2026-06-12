const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const CDP_ENDPOINTS = [
  process.env.MAIL_CDP_ENDPOINT || 'http://127.0.0.1:9233',
  'http://127.0.0.1:9232',
];

const FIELD_ORDER = [
  'harmfulness',
  'subjectQuality',
  'groundedness',
  'instructionFit',
  'tone',
  'naturalness',
  'localization',
  'personalization',
];

const LOCALIZATION_ISSUE_VALUES = new Set([
  'translation_issue',
  'mixed_languages',
  'wrong_format',
  'wrong_punctuation',
  'scrambled_symbols',
  'culture_misfit',
  'other',
]);

function parseArgs() {
  const args = process.argv.slice(2);
  const out = { dryRun: false, submit: false };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--answers') out.answersPath = args[++i];
    else if (args[i] === '--dry-run') out.dryRun = true;
    else if (args[i] === '--submit') out.submit = true;
    else throw new Error(`Unknown argument: ${args[i]}`);
  }
  if (!out.answersPath) throw new Error('Usage: node MAIL/scripts/fill_task.js --answers FILE [--dry-run|--submit]');
  return out;
}

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

function controlKey(control) {
  return [control.name, control.value].join('=');
}

async function getTaskFrame(page) {
  for (const frame of page.frames()) {
    const text = await frame.locator('body').innerText({ timeout: 1000 }).catch(() => '');
    if (text.includes('Response A') && text.includes('Response B') && text.includes('Pairwise Comparison')) return frame;
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

function buildPlan(inputs, answers) {
  const responseGroups = [];
  const radioGroups = [];
  const checkboxGroups = [];
  const textareas = [];

  for (const input of inputs) {
    if (input.tag === 'TEXTAREA') textareas.push(input);
    if (input.type === 'radio') {
      let group = radioGroups.find((item) => item.name === input.name);
      if (!group) {
        group = { name: input.name, inputs: [] };
        radioGroups.push(group);
      }
      group.inputs.push(input);
    }
    if (input.type === 'checkbox') {
      let group = checkboxGroups.find((item) => item.name === input.name);
      if (!group) {
        group = { name: input.name, inputs: [] };
        checkboxGroups.push(group);
      }
      group.inputs.push(input);
    }
  }

  const usefulRadioGroups = radioGroups.filter((group) => group.inputs.length >= 2);
  const usefulCheckboxGroups = checkboxGroups.filter((group) => group.inputs.length >= 2);

  if (usefulRadioGroups.length < 13) {
    throw new Error(`Expected at least 13 radio groups, found ${usefulRadioGroups.length}`);
  }

  let radioOffset = 0;
  for (const responseName of ['responseA', 'responseB']) {
    const responsePlan = { responseName, radio: [], checkbox: null };
    for (const field of FIELD_ORDER) {
    if (field === 'subjectQuality') {
        responsePlan.checkbox = {
          field,
          group: usefulCheckboxGroups[responseGroups.length],
          values: answers[responseName][field] || [],
        };
      } else {
        const group = usefulRadioGroups[radioOffset++];
        responsePlan.radio.push({
          field,
          group,
          value: answers[responseName][field],
        });
      }
    }
    const issueValues = answers[responseName].localizationIssues || [];
    const issueGroup = usefulCheckboxGroups.find((group) =>
      group.inputs.some((input) => LOCALIZATION_ISSUE_VALUES.has(input.value))
    );
    if (issueValues.length) {
      responsePlan.localizationIssues = {
        field: 'localizationIssues',
        group: issueGroup || null,
        values: issueValues,
      };
    }
    responseGroups.push(responsePlan);
  }

  const pairwise = {
    field: 'pairwise',
    group: usefulRadioGroups[radioOffset],
    value: answers.pairwise,
  };

  return {
    responseGroups,
    pairwise,
    observation: answers.observation || '',
    textarea: textareas[0],
  };
}

async function clickInput(frame, input) {
  await frame.locator(`input[name="${input.name}"][value="${input.value}"]`).first().evaluate(el => el.click());
}

async function clickTab(frame, name) {
  const tab = frame.getByRole('tab', { name, exact: true });
  if (await tab.count()) {
    await tab.first().evaluate(el => el.click());
    await frame.page().waitForTimeout(200);
  }
}

async function applyPlan(frame, plan) {
  for (const response of plan.responseGroups) {
    await clickTab(frame, response.responseName === 'responseA' ? 'Response A' : 'Response B');
    for (const item of response.radio) {
      const target = item.group.inputs.find((input) => input.value === item.value);
      if (!target) throw new Error(`No radio value ${item.value} for ${response.responseName}.${item.field}`);
      await clickInput(frame, target);
    }
    if (response.checkbox && response.checkbox.group) {
      for (const input of response.checkbox.group.inputs) {
        const shouldCheck = response.checkbox.values.includes(input.value);
        const locator = frame.locator(`input[name="${input.name}"][value="${input.value}"]`);
        if (shouldCheck) await locator.check({ force: true });
        else await locator.uncheck({ force: true }).catch(() => {});
      }
    }
    if (response.localizationIssues && response.localizationIssues.group) {
      for (const input of response.localizationIssues.group.inputs) {
        const shouldCheck = response.localizationIssues.values.includes(input.value);
        const locator = frame.locator(`input[name="${input.name}"][value="${input.value}"]`);
        if (shouldCheck) await locator.check({ force: true });
        else await locator.uncheck({ force: true }).catch(() => {});
      }
    } else if (response.localizationIssues) {
      for (const value of response.localizationIssues.values) {
        await frame.locator(`input[type="checkbox"][value="${value}"]`).first().check({ force: true, timeout: 2000 });
      }
    }
  }

  await clickTab(frame, 'A and B');
  const pairwiseTarget = plan.pairwise.group.inputs.find((input) => input.value === plan.pairwise.value);
  if (!pairwiseTarget) throw new Error(`No pairwise value ${plan.pairwise.value}`);
  await clickInput(frame, pairwiseTarget);

  if (plan.textarea && plan.observation) {
    await frame.locator('textarea').first().fill(plan.observation);
  }
}

function summarizePlan(plan) {
  return {
    responses: plan.responseGroups.map((response) => ({
      responseName: response.responseName,
      radio: response.radio.map((item) => ({
        field: item.field,
        group: item.group.name,
        value: item.value,
        available: item.group.inputs.map((input) => input.value),
      })),
      checkbox: response.checkbox
        ? {
            field: response.checkbox.field,
            group: response.checkbox.group && response.checkbox.group.name,
            values: response.checkbox.values,
            available: response.checkbox.group ? response.checkbox.group.inputs.map((input) => input.value) : [],
          }
        : null,
      localizationIssues: response.localizationIssues
        ? {
            field: response.localizationIssues.field,
            group: response.localizationIssues.group && response.localizationIssues.group.name,
            values: response.localizationIssues.values,
            available: response.localizationIssues.group
              ? response.localizationIssues.group.inputs.map((input) => input.value)
              : [],
          }
        : null,
    })),
    pairwise: {
      group: plan.pairwise.group.name,
      value: plan.pairwise.value,
      available: plan.pairwise.group.inputs.map((input) => input.value),
    },
    observation: plan.observation,
    hasTextarea: Boolean(plan.textarea),
  };
}

async function main() {
  const args = parseArgs();
  const answers = JSON.parse(fs.readFileSync(path.resolve(args.answersPath), 'utf8'));
  const { browser, endpoint } = await connect();
  try {
    const context = browser.contexts()[0];
    if (!context) throw new Error('No browser context found');
    const page = context.pages().find((p) => p.url().includes('starshot.scilliance.com')) || context.pages()[0];
    if (!page) throw new Error('No page found');
    const frame = await getTaskFrame(page);
    const inputs = await readInputs(frame);
    const plan = buildPlan(inputs, answers);
    console.log(JSON.stringify({ cdpEndpoint: endpoint, dryRun: args.dryRun, plan: summarizePlan(plan) }, null, 2));

    if (!args.dryRun) {
      await applyPlan(frame, plan);
      if (args.submit) {
        await frame.getByText('Submit', { exact: true }).first().evaluate(el => el.click());
        await page.waitForTimeout(1000);
        const doneBtn = page.getByLabel('Submit Task');
        if (await doneBtn.count()) {
          await doneBtn.first().evaluate(el => el.click()).catch(() => {});
        }
        // Handle confirmation dialog: "Do you want to submit your task?" → click Submit
        await page.waitForTimeout(2000);
        const confirmDialog = page.locator('div[role="dialog"]');
        if (await confirmDialog.count() > 0) {
          const submitBtn = confirmDialog.locator('button', { hasText: 'Submit' }).first();
          if (await submitBtn.isVisible().catch(() => false)) {
            await submitBtn.click({ timeout: 5000 }).catch(() => {});
            // Wait for submission result (success or failure)
            await page.waitForTimeout(5000);
          }
        }
        // Check for Submission failed → auto retry up to 3 times
        for (let retry = 0; retry < 3; retry++) {
          const body = await page.locator('body').innerText({ timeout: 3000 }).catch(() => '');
          if (/Submission failed/i.test(body)) {
            const retryBtn = page.locator('button', { hasText: 'Retry' }).first();
            if (await retryBtn.isVisible().catch(() => false)) {
              await retryBtn.click({ timeout: 5000 }).catch(() => {});
              await page.waitForTimeout(8000);
            }
          } else if (/Task successfully submitted/i.test(body)) {
            break; // Success, no retry needed
          } else {
            await page.waitForTimeout(3000);
          }
        }
      }
    }
  } finally {
    await browser.close();
  }
}

// Wrap main execution in a 45s absolute timeout to prevent indefinite hangs
Promise.race([
  main(),
  new Promise((_, reject) => setTimeout(() => reject(new Error('FILL_TASK_TIMEOUT_LIMIT_REACHED')), 90000))
]).catch((error) => {
  console.error(`[FATAL_TIMEOUT] Fill task script timed out or failed: ${error.stack || error.message}`);
  process.exit(1);
});
