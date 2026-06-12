require('./_timeout');
const { chromium } = require('playwright');

async function isNextTaskVisible(page) {
  const nextBtn = page.locator('button').filter({ hasText: /^Next Task$/ }).filter({ visible: true }).first();
  return await nextBtn.count().then(c => c > 0).catch(() => false);
}

async function getVisibleDialogs(page) {
  return page.evaluate(() => {
    const dialogs = document.querySelectorAll('[role="dialog"]');
    return [...dialogs]
      .filter(d => d.offsetWidth > 0)
      .map(d => (d.innerText || '').trim().slice(0, 500));
  });
}

async function clickRetryIfPresent(page) {
  const retryBtn = page.locator('button').filter({ hasText: /^Retry$/ }).filter({ visible: true }).first();
  if (await retryBtn.count().then(c => c > 0).catch(() => false)) {
    console.log('Clicking Retry in failure dialog...');
    await retryBtn.click({ force: true });
    return true;
  }
  return false;
}

async function submitWithRetry(page, taskFrame, maxAttempts = 3) {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    console.log(`Submission attempt ${attempt}/${maxAttempts}...`);

    const submitBtn = taskFrame.getByRole('button', { name: 'Submit' });
    console.log('Clicking Submit in frame...');
    await submitBtn.click({ force: true });
    await page.waitForTimeout(2000);

    const confirmSubmit = page.locator('#starshot_submit_task_button');
    if (await confirmSubmit.count() > 0 && await confirmSubmit.isVisible()) {
      console.log('Clicking Submit in confirmation dialog...');
      await confirmSubmit.click({ force: true });
      await page.waitForTimeout(5000);
    } else {
      const submitBtns = page.locator('button').filter({ hasText: 'Submit' }).filter({ visible: true });
      if (await submitBtns.count() > 0) {
        console.log('Clicking Submit button by text...');
        await submitBtns.last().click({ force: true });
        await page.waitForTimeout(5000);
      }
    }

    for (let i = 0; i < 6; i++) {
      if (await isNextTaskVisible(page)) return { success: true, attempt };
      await page.waitForTimeout(1000);
    }

    const dialogs = await getVisibleDialogs(page);
    console.log('Dialogs after submit attempt:', JSON.stringify(dialogs));

    const hasUploadFailure = dialogs.some(d =>
      d.includes('Submission failed!') &&
      d.includes('Upload failed')
    );
    if (!hasUploadFailure) {
      return { success: false, attempt, dialogs };
    }

    const retried = await clickRetryIfPresent(page);
    if (!retried) {
      return { success: false, attempt, dialogs };
    }
    await page.waitForTimeout(5000);

    if (await isNextTaskVisible(page)) return { success: true, attempt };
  }

  return { success: false, attempt: maxAttempts, dialogs: await getVisibleDialogs(page) };
}

(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  
  const frames = page.frames();
  const taskFrame = frames.find(f => f.url().includes('task-editor'));
  if (!taskFrame) { console.log('No task-editor frame'); await browser.close(); return; }
  
  console.log('--- STARTING PRE-SUBMISSION VALIDATION ---');
  
  // Find all Response tabs dynamically
  const tabNames = await taskFrame.locator('button[role="tab"]').evaluateAll(els => 
    els.map(el => el.innerText.trim()).filter(t => t.startsWith('Response '))
  );
  
  if (tabNames.length === 0) {
    console.error('CRITICAL ERROR: No Response tabs detected!');
    await browser.close();
    process.exit(1);
  }
  
  console.log(`Detected Response tabs: ${JSON.stringify(tabNames)}`);
  
  let validationPassed = true;
  const validationErrors = [];
  
  for (const tabName of tabNames) {
    console.log(`Checking ${tabName}...`);
    const tab = taskFrame.locator('button[role="tab"]').filter({ hasText: tabName });
    await tab.first().click({ timeout: 3000 });
    await page.waitForTimeout(600);
    
    // Get visible checked and unchecked radios
    const visible = await taskFrame.locator('input[type="radio"]').evaluateAll(els =>
      els.filter(el => el.offsetParent !== null).map(el => ({
        name: el.name, value: el.value, checked: el.checked,
        label: (el.closest('label')?.innerText || '').trim().slice(0, 80),
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
      validationPassed = false;
      const msg = `${tabName} has unchecked required radio groups: ${uncheckedGroups.map(([name]) => name).join(', ')}`;
      validationErrors.push(msg);
      console.log(`  [FAIL] ${msg}`);
    } else {
      console.log(`  [PASS] All radio groups have selections.`);
    }
    
    // Check for visible error messages
    const errors = await taskFrame.locator('[class*="error"], [class*="required"]').evaluateAll(els =>
      els.filter(el => el.offsetParent !== null).map(el => (el.innerText || '').trim().slice(0, 100)).filter(t => t)
    );
    if (errors.length > 0) {
      validationPassed = false;
      const msg = `${tabName} has active validation errors: ${JSON.stringify(errors)}`;
      validationErrors.push(msg);
      console.log(`  [FAIL] ${msg}`);
    }
  }
  
  // Verify overall completion text
  const formText = await taskFrame.locator('body').innerText({ timeout: 2000 }).catch(() => '');
  const completeMatch = formText.match(/(\d+\/\d+) Complete/);
  console.log('Completion status label found:', completeMatch ? completeMatch[0] : 'None');
  
  const expectedCompleteText = `${tabNames.length}/${tabNames.length} Complete`;
  if (!completeMatch || completeMatch[0] !== expectedCompleteText) {
    validationPassed = false;
    validationErrors.push(`Form status is not fully complete (Expected: ${expectedCompleteText}, Found: ${completeMatch ? completeMatch[0] : 'None'})`);
  }
  
  if (!validationPassed) {
    console.error('\n*****************************************************************');
    console.error('* CRITICAL ERROR: SUBMISSION ABORTED!                           *');
    console.error('* The form has incomplete or invalid fields.                     *');
    console.error('* Skipping questions or incomplete submissions is strictly      *');
    console.error('* PROHIBITED by the SOP. Please correct the errors below.       *');
    console.error('*****************************************************************');
    for (const err of validationErrors) {
      console.error(`- ${err}`);
    }
    console.error('*****************************************************************\n');
    await browser.close();
    process.exit(1);
  }
  
  console.log('--- VALIDATION PASSED SUCCESSFULLY! PROCEEDING TO SUBMISSION ---');
  const result = await submitWithRetry(page, taskFrame, 5);
  const state = await getVisibleDialogs(page);
  console.log('Final dialogs:', JSON.stringify(state));
  console.log('SuccessByNextTask:', result.success);
  console.log('SubmissionResult:', JSON.stringify(result));

  if (!result.success) {
    process.exitCode = 1;
  }
  
  await browser.close();
})().catch(e => {
  console.error('Submission failed with error:', e);
  process.exit(1);
});
