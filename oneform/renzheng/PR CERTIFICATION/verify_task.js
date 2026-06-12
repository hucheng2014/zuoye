/**
 * Pre/post submit verification — ensure form is complete and submission succeeded.
 */
const puppeteer = require('puppeteer-core');
const { CDP_URL, CDP_FALLBACK, SUBMIT_AT_SEC } = require('./config');
const { assertRatingsReady, ratingsReadyStrict } = require('./task_utils');

async function connect() {
  for (const url of [CDP_URL, CDP_FALLBACK]) {
    try {
      return await puppeteer.connect({ browserURL: url, defaultViewport: null });
    } catch (e) {
      if (url === CDP_FALLBACK) throw e;
    }
  }
}

async function getContexts() {
  const browser = await connect();
  const pages = await browser.pages();
  const page = pages.find((p) => p.url().includes('starshot')) || pages[0];
  const frm = page.frames().find((f) => f.url().includes('task-editor'));
  return { browser, page, frm };
}

/** Read page TPT timer in seconds from starshot top bar */
async function readTPT(page) {
  return page.evaluate(() => {
    const parse = (text) => {
      const m = String(text).match(/(\d+)\s*(?:seconds?|s)\b/i);
      return m ? parseInt(m[1], 10) : -1;
    };
    const allText = document.body?.innerText || '';
    let tpt = parse(allText);
    if (tpt >= 0) return tpt;
    const nodes = [...document.querySelectorAll('button,[aria-label],[role="timer"]')];
    for (const el of nodes) {
      const t = `${el.textContent || ''} ${el.getAttribute('aria-label') || ''}`;
      if (/time worked/i.test(t)) return parse(t);
    }
    const m = allText.match(/Time worked:\s*(\d+)/i);
    return m ? parseInt(m[1], 10) : -1;
  });
}

/** Scan iframe form state */
async function scanForm(frm) {
  if (!frm) return { ok: false, error: 'no task-editor frame' };
  return frm.evaluate(() => {
    const text = document.body.innerText;
    const respM = text.match(/RESPONSES\s*(\d+)\/(\d+)\s*Complete/i);
    const cmpM = text.match(/Compare\s*(\d+)\/(\d+)\s*Complete/i);
    const rationale = document.querySelector('textarea:not([placeholder*="Describe your task"])');
    const submitBtn = document.querySelector('.submit-button') ||
      [...document.querySelectorAll('button')].find((b) => /submit|invalid/i.test(b.textContent));
    const required = [...document.querySelectorAll('[class*="error"],[role="alert"],.legend')]
      .map((e) => e.textContent.trim())
      .filter((t) => /answer is required|invalid/i.test(t));
    const submitLabel = submitBtn?.textContent?.trim() || 'missing';
    return {
      responsesComplete: respM ? `${respM[1]}/${respM[2]}` : '?/?',
      responsesExpected: respM ? parseInt(respM[2], 10) : null,
      compareComplete: cmpM ? `${cmpM[1]}/${cmpM[2]}` : '?/?',
      compareExpected: cmpM ? parseInt(cmpM[2], 10) : null,
      rationaleLen: rationale?.value?.length || 0,
      submitLabel,
      submitDisabled: !!submitBtn?.disabled,
      submitInvalid: /invalid/i.test(submitLabel),
      submitReady: !!submitBtn && !submitBtn.disabled && submitLabel === 'Submit',
      requiredErrors: required.slice(0, 5),
    };
  });
}

/** Form-only gate: responses/compare/rationale/submit button (no TPT, no file ratings). */
function buildFormIssues(form) {
  const issues = [];
  if (!form || form.error) {
    issues.push(form?.error || 'no form scan');
    return issues;
  }
  const respTarget = form.responsesExpected != null
    ? `${form.responsesExpected}/${form.responsesExpected}`
    : null;
  const cmpTarget = form.compareExpected != null
    ? `${form.compareExpected}/${form.compareExpected}`
    : null;
  if (respTarget && form.responsesComplete !== respTarget) {
    issues.push(`Responses ${form.responsesComplete} (need ${respTarget})`);
  }
  if (cmpTarget && form.compareComplete !== cmpTarget) {
    issues.push(`Compare ${form.compareComplete} (need ${cmpTarget})`);
  }
  if (form.rationaleLen < 50) issues.push(`Rationale too short (${form.rationaleLen} chars)`);
  if (form.submitInvalid) issues.push(`Submit button: ${form.submitLabel}`);
  if (!form.submitReady) issues.push(`Submit not ready: ${form.submitLabel}`);
  if (form.requiredErrors.length) issues.push(`Required: ${form.requiredErrors.join('; ')}`);
  return issues;
}

function buildPreIssues(tpt, form, opts = {}) {
  const issues = [];
  if (!opts.skipRatings) {
    if (!ratingsReadyStrict()) {
      try {
        assertRatingsReady();
      } catch (e) {
        issues.push(`Stale ratings: ${e.message}`);
      }
    }
  }
  if (!opts.skipTpt && tpt >= 0 && tpt < SUBMIT_AT_SEC) {
    issues.push(`TPT=${tpt}s < ${SUBMIT_AT_SEC}s`);
  }
  issues.push(...buildFormIssues(form));
  return issues;
}

/** Pre-submit using existing connection (no extra CDP) */
async function verifyBeforeSubmitOn(page, frm, opts = {}) {
  const tpt = await readTPT(page);
  const form = await scanForm(frm);
  const issues = buildPreIssues(tpt, form, opts);
  return { ok: issues.length === 0, tpt, form, issues };
}

/** Form completeness only — use after fillRatings, before clicking Submit. */
async function verifyFormSubmittableOn(page, frm) {
  const tpt = await readTPT(page);
  const form = await scanForm(frm);
  const issues = buildFormIssues(form);
  return { ok: issues.length === 0, tpt, form, issues };
}

/** Pre-submit: all sections complete, valid Submit button, rationale filled */
async function verifyBeforeSubmit() {
  const { browser, page, frm } = await getContexts();
  const result = await verifyBeforeSubmitOn(page, frm);
  await browser.disconnect();
  return result;
}

async function detectSuccessScreen(page) {
  return page.evaluate(() => /successfully submitted/i.test(document.body?.innerText || ''));
}

async function detectSubmittingDialog(page) {
  return page.evaluate(() => /submitting task|uploading.*please wait/i.test(document.body?.innerText || ''));
}

/** Post-submit: task left editor or timer reset / next available */
async function verifyAfterSubmit() {
  const { browser, page, frm } = await getContexts();
  const tpt = await readTPT(page);
  const onSuccess = await detectSuccessScreen(page);
  const hasNext = await page.evaluate(() =>
    [...document.querySelectorAll('button,a,[role=button]')].some(
      (b) => /next task/i.test(b.textContent) && b.offsetParent
    )
  );
  const form = frm ? await scanForm(frm) : null;
  await browser.disconnect();

  const submitted =
    onSuccess ||
    hasNext ||
    (form && form.submitLabel === 'missing') ||
    (form && !form.submitInvalid && form.submitLabel !== 'Submit' && tpt < 60);

  const issues = [];
  if (!submitted) {
    if (form?.submitLabel === 'Submit') issues.push('Still on task — Submit button visible');
    if (form?.submitInvalid) issues.push(`Invalid answers: ${form.submitLabel}`);
    if (!hasNext && !onSuccess) issues.push('NEXT TASK not found');
  }

  return { ok: submitted, tpt, hasNext, onSuccess, form, issues };
}

/** Poll post-submit until success screen / next task / TPT reset (handles UI lag). */
async function verifyAfterSubmitWithRetry(maxWaitMs = 90000) {
  const start = Date.now();
  let last = null;
  while (Date.now() - start < maxWaitMs) {
    const { browser, page } = await getContexts();
    const uploading = await detectSubmittingDialog(page);
    await browser.disconnect();
    if (uploading) {
      await new Promise((r) => setTimeout(r, 3000));
      continue;
    }
    last = await verifyAfterSubmit();
    if (last.ok) return last;
    await new Promise((r) => setTimeout(r, 2000));
  }
  return last || { ok: false, issues: ['post-verify timeout'] };
}

/** One-shot TPT read — use when ready.flag already set */
async function assertTPTReady(minSec = SUBMIT_AT_SEC) {
  const { browser, page } = await getContexts();
  const tpt = await readTPT(page);
  await browser.disconnect();
  if (tpt < minSec) return { ok: false, tpt, error: `TPT=${tpt}s < ${minSec}s` };
  return { ok: true, tpt };
}

async function waitForTPT(minSec = SUBMIT_AT_SEC, timeoutMs = 900000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const { browser, page } = await getContexts();
    const tpt = await readTPT(page);
    await browser.disconnect();
    if (tpt >= minSec) return { ok: true, tpt };
    const remaining = minSec - tpt;
    const poll = remaining <= 30 ? 2000 : remaining <= 120 ? 5000 : 10000;
    await new Promise((r) => setTimeout(r, poll));
  }
  return { ok: false, error: `TPT did not reach ${minSec}s within timeout` };
}

module.exports = {
  readTPT,
  scanForm,
  buildFormIssues,
  buildPreIssues,
  verifyBeforeSubmit,
  verifyBeforeSubmitOn,
  verifyFormSubmittableOn,
  verifyAfterSubmit,
  verifyAfterSubmitWithRetry,
  detectSuccessScreen,
  waitForTPT,
  assertTPTReady,
  SUBMIT_AT_SEC,
};

// CLI: node verify_task.js [--after|--form-only]
if (require.main === module) {
  const after = process.argv.includes('--after');
  const formOnly = process.argv.includes('--form-only');
  const run = after
    ? verifyAfterSubmit()
    : formOnly
      ? getContexts().then(async ({ browser, page, frm }) => {
          const r = await verifyFormSubmittableOn(page, frm);
          await browser.disconnect();
          return r;
        })
      : verifyBeforeSubmit();
  run.then((r) => {
    console.log(JSON.stringify(r, null, 2));
    process.exit(r.ok ? 0 : 1);
  });
}
