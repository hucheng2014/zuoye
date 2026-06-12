/**
 * full_submit.js — Validate form completeness and submit the Intelligent Polls task.
 *
 * Steps:
 *   1. Verify all radio groups have a selection (abort if not).
 *   2. Click Submit in the task-editor iframe.
 *   3. Click the confirmation dialog (#starshot_submit_task_button).
 *   4. Verify submission succeeded (Next Task button appears).
 *
 * Usage:
 *   node scripts/full_submit.js
 */

require('./_timeout');
const { chromium } = require('playwright');

const CDP_ENDPOINTS = [
  process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233',
  'http://127.0.0.1:9232',
];

async function connect() {
  for (const ep of CDP_ENDPOINTS) {
    try { return await chromium.connectOverCDP(ep); } catch {}
  }
  throw new Error('No CDP endpoint available');
}

async function isNextTaskVisible(page) {
  const nextBtn = page.locator('button').filter({ hasText: /^Next Task$/ }).filter({ visible: true }).first();
  return await nextBtn.count().then(c => c > 0).catch(() => false);
}

async function submitWithRetry(page, taskFrame, maxAttempts = 3) {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    console.log(`Submission attempt ${attempt}/${maxAttempts}...`);

    // Click Submit in the iframe
    const submitBtn = taskFrame.getByRole('button', { name: 'Submit' });
    console.log('Clicking Submit in frame...');
    await submitBtn.click({ force: true });
    await page.waitForTimeout(2000);

    // Click confirmation dialog
    const confirmSubmit = page.locator('#starshot_submit_task_button');
    if (await confirmSubmit.count() > 0 && await confirmSubmit.isVisible()) {
      console.log('Clicking Submit in confirmation dialog...');
      await confirmSubmit.click({ force: true });
      await page.waitForTimeout(5000);
    } else {
      // Fallback: look for any visible Submit button on the page
      const submitBtns = page.locator('button').filter({ hasText: 'Submit' }).filter({ visible: true });
      if (await submitBtns.count() > 0) {
        console.log('Clicking Submit button by text...');
        await submitBtns.last().click({ force: true });
        await page.waitForTimeout(5000);
      }
    }

    // Check if Next Task appeared
    for (let i = 0; i < 6; i++) {
      if (await isNextTaskVisible(page)) return { success: true, attempt };
      await page.waitForTimeout(1000);
    }

    // Check for failure dialog
    const retryBtn = page.locator('button').filter({ hasText: /^Retry$/ }).filter({ visible: true }).first();
    if (await retryBtn.count().then(c => c > 0).catch(() => false)) {
      console.log('Clicking Retry in failure dialog...');
      await retryBtn.click({ force: true });
      await page.waitForTimeout(5000);
      if (await isNextTaskVisible(page)) return { success: true, attempt };
    }
  }

  return { success: false, attempt: maxAttempts };
}

(async () => {
  const browser = await connect();
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];

  const taskFrame = page.frames().find(f => f.url().includes('task-editor'));
  if (!taskFrame) { console.log('No task-editor frame'); await browser.close(); return; }

  console.log('--- STARTING PRE-SUBMISSION VALIDATION ---');

  // Get all visible radios and check each group has a selection
  const visible = await taskFrame.locator('input[type="radio"]').evaluateAll(els =>
    els.filter(el => el.offsetParent !== null).map(el => ({
      name: el.name, value: el.value, checked: el.checked,
    }))
  );

  const groups = {};
  for (const v of visible) {
    if (!groups[v.name]) groups[v.name] = { checked: false, values: [] };
    groups[v.name].values.push(v.value);
    if (v.checked) groups[v.name].checked = true;
  }

  const uncheckedGroups = Object.entries(groups).filter(([_, g]) => !g.checked);
  if (uncheckedGroups.length > 0) {
    console.error('\n*****************************************************************');
    console.error('* CRITICAL ERROR: SUBMISSION ABORTED!                           *');
    console.error('* The form has unchecked radio groups.                          *');
    console.error('* Skipping questions or incomplete submissions is strictly      *');
    console.error('* PROHIBITED by the SOP. Please correct the errors below.       *');
    console.error('*****************************************************************');
    for (const [name, g] of uncheckedGroups) {
      console.error(`  ❌ Group "${name}": options=${JSON.stringify(g.values)}`);
    }
    console.error('*****************************************************************\n');
    await browser.close();
    process.exit(1);
  }

  console.log('✅ All radio groups have selections.');

  // Check for validation errors
  const errors = await taskFrame.locator('[class*="error"], [class*="validation-error"]').evaluateAll(els =>
    els.filter(el => el.offsetParent !== null).map(el => (el.innerText || '').trim().slice(0, 100)).filter(t => t)
  );
  if (errors.length > 0) {
    console.error('❌ VALIDATION ERRORS:', errors);
    console.error('ABORTING SUBMISSION.');
    await browser.close();
    process.exit(1);
  }

  console.log('--- VALIDATION PASSED! PROCEEDING TO SUBMISSION ---');
  const result = await submitWithRetry(page, taskFrame, 5);
  console.log('SubmissionResult:', JSON.stringify(result));

  if (result.success) {
    // Click Next Task immediately to stop the current task's timer
    console.log('[submit] Clicking Next Task to stop timer...');
    const nextBtn = page.locator('button').filter({ hasText: /^Next Task$/ }).filter({ visible: true }).first();
    try {
      await nextBtn.waitFor({ state: 'visible', timeout: 5000 });
      await nextBtn.click({ timeout: 3000 });
      console.log('[submit] Next Task clicked. Timer stopped.');
    } catch (e) {
      console.log('[submit] Next Task button not found:', e.message.split('\n')[0]);
    }
  }

  if (!result.success) {
    process.exitCode = 1;
  }

  await browser.close();
})().catch(e => {
  console.error('Submission failed with error:', e.message);
  process.exit(1);
});
