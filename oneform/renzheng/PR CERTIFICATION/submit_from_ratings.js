/**
 * Submit @ TPT>=720s
 *
 * Default (--submit-only): form already filled by fill_from_ratings.js → verify → click Submit (<15s)
 * Legacy (no flag): TPT → fill → verify → submit (fallback)
 */
const fs = require('fs');
const path = require('path');
const {
  assertReadyToSubmit,
  fillAndVerifySubmittable,
  finalizeSubmit,
  getFrame,
} = require('./pr_automation_helper');
const {
  verifyAfterSubmitWithRetry,
  verifyBeforeSubmitOn,
  verifyFormSubmittableOn,
  assertTPTReady,
  waitForTPT,
  SUBMIT_AT_SEC,
} = require('./verify_task');
const {
  assertRatingsReady,
  extractTaskFromPuppeteerFrame,
  validateRatingsForTask,
} = require('./task_utils');

const RUNS = path.join(__dirname, 'runs');
const SUBMIT_ONLY = process.argv.includes('--submit-only') || process.argv.includes('--fast');
const FORM_FILLED = path.join(RUNS, 'form_filled.flag');

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  fs.mkdirSync(RUNS, { recursive: true });
  fs.appendFileSync(path.join(RUNS, 'submit.log'), line + '\n', { flag: 'a' });
}

async function ensureTPT() {
  const readyFlag = path.join(RUNS, 'ready.flag');
  if (fs.existsSync(readyFlag)) {
    const gate = await assertTPTReady(SUBMIT_AT_SEC);
    if (gate.ok) return gate;
    log(`ready.flag but TPT=${gate.tpt}s — brief wait`);
  }
  return waitForTPT(SUBMIT_AT_SEC, 120000);
}

async function main() {
  const t0 = Date.now();
  let fileGuard;
  try {
    fileGuard = assertRatingsReady();
  } catch (e) {
    log(`FATAL STALE GUARD (files): ${e.message}`);
    process.exit(1);
  }

  const gate = await ensureTPT();
  if (!gate.ok) {
    log(`FATAL: ${gate.error}`);
    process.exit(1);
  }
  if (gate.tpt > SUBMIT_AT_SEC + 120) {
    log(`WARN: TPT=${gate.tpt}s 已超出目标较多，仍立即提交`);
  }
  log(`TPT=${gate.tpt}s — fast submit start (+${Date.now() - t0}ms)`);

  const ratings = fileGuard.ratings;
  const { browser, page, frm1 } = await getFrame();
  if (!frm1) {
    await browser.disconnect();
    throw new Error('task-editor frame not found');
  }

  const liveTask = await extractTaskFromPuppeteerFrame(frm1, 400);
  const liveCheck = validateRatingsForTask(liveTask, ratings);
  if (!liveCheck.ok) {
    await browser.disconnect();
    log(`FATAL STALE GUARD (live page): ${liveCheck.issues.join('; ')}`);
    process.exit(1);
  }
  log(`STALE GUARD OK fingerprint=${liveTask.fingerprint}`);

  let ready;
  const useSubmitOnly = SUBMIT_ONLY || fs.existsSync(path.join(RUNS, 'submittable.flag'));
  if (useSubmitOnly) {
    log('submit-only: form pre-filled, verify then click Submit');
    let formCheck = await verifyFormSubmittableOn(page, frm1);
    if (!formCheck.ok) {
      log(`form incomplete (${formCheck.issues.join('; ')}) — emergency refill`);
      const refill = await fillAndVerifySubmittable(page, frm1, ratings, { log });
      if (!refill.ok) {
        await browser.disconnect();
        log(`FATAL refill: ${refill.issues.join('; ')}`);
        process.exit(1);
      }
      formCheck = await verifyFormSubmittableOn(page, frm1);
    }
    ready = await verifyBeforeSubmitOn(page, frm1);
    if (!ready.ok) {
      await browser.disconnect();
      log(`FATAL pre-submit: ${ready.issues.join('; ')}`);
      if (ready.form) log(`Form state: ${JSON.stringify(ready.form)}`);
      process.exit(1);
    }
    log(`Pre-submit OK (submit-only) TPT=${ready.tpt}s form=${JSON.stringify(ready.form)}`);
  } else {
    ready = await assertReadyToSubmit(page, frm1, ratings, { log });
    if (!ready.ok) {
      await browser.disconnect();
      log(`FATAL ${ready.stage || 'pre-submit'}: ${ready.issues.join('; ')}`);
      if (ready.form) log(`Form state: ${JSON.stringify(ready.form)}`);
      process.exit(1);
    }
    log(`Pre-submit OK (fill attempts=${ready.attempts}) TPT=${ready.tpt}s form=${JSON.stringify(ready.form)}`);
  }

  const result = await finalizeSubmit(browser, page, frm1);
  await browser.disconnect();
  log(`Submit done (+${Date.now() - t0}ms): ${JSON.stringify(result)}`);

  let post = await verifyAfterSubmitWithRetry(15000);
  if (!post.ok) {
    log(`Post-verify retry confirm/next: ${post.issues.join('; ')}`);
    const { browser: b2, page: p2 } = await getFrame();
    for (let i = 0; i < 8; i++) {
      const step = await p2.evaluate(() => {
        for (const b of document.querySelectorAll('button,[role=button]')) {
          if (!b.offsetParent) continue;
          const t = b.textContent.trim();
          const ctx = (b.closest('div,section,dialog')?.textContent || '').toLowerCase();
          if (t === 'Submit' && ctx.includes('do you want')) { b.click(); return 'confirm'; }
          if (/next task/i.test(t)) { b.click(); return 'next'; }
        }
        return null;
      });
      if (step === 'next') break;
      await new Promise((r) => setTimeout(r, 500));
    }
    await b2.disconnect();
    post = await verifyAfterSubmitWithRetry(8000);
  }

  if (!post.ok) {
    log(`FATAL post-verify: ${post.issues.join('; ')}`);
    process.exit(1);
  }
  if (post.onSuccess) log('Post-verify: success screen detected');
  if (post.tpt >= 0 && gate.tpt > 100 && post.tpt < 90) {
    log(`Post-verify: TPT reset ${gate.tpt}→${post.tpt}s = success`);
  }

  fs.writeFileSync(path.join(RUNS, 'submitted.flag'), new Date().toISOString());
  try { fs.unlinkSync(path.join(RUNS, 'ready.flag')); } catch {}
  try { fs.unlinkSync(path.join(RUNS, 'submittable.flag')); } catch {}
  try { fs.unlinkSync(FORM_FILLED); } catch {}
  log(`SUCCESS total ${Date.now() - t0}ms`);
}

main().catch((e) => {
  log(`FATAL: ${e.message}`);
  process.exit(1);
});
