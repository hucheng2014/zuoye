#!/usr/bin/env node
/**
 * Pre-720 phase: fill form + form-only verify. Does NOT require TPT>=720.
 * Writes runs/form_filled.flag + runs/submittable.flag when OK.
 */
const fs = require('fs');
const path = require('path');
const {
  assertRatingsReady,
  extractTaskFromPuppeteerFrame,
  validateRatingsForTask,
  loadTaskFile,
} = require('./task_utils');
const { getFrame, fillAndVerifySubmittable } = require('./pr_automation_helper');
const { verifyFormSubmittableOn } = require('./verify_task');

const RUNS = path.join(__dirname, 'runs');
const FORM_FILLED = path.join(RUNS, 'form_filled.flag');

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  fs.mkdirSync(RUNS, { recursive: true });
  fs.appendFileSync(path.join(RUNS, 'fill.log'), line + '\n', { flag: 'a' });
}

function writeFilledFlag(fingerprint, form) {
  fs.writeFileSync(FORM_FILLED, JSON.stringify({
    fingerprint,
    at: new Date().toISOString(),
    form,
  }, null, 2));
}

async function main() {
  let guard;
  try {
    guard = assertRatingsReady();
  } catch (e) {
    log(`FATAL: ${e.message}`);
    process.exit(1);
  }

  const ratings = guard.ratings;
  const task = loadTaskFile();
  const { browser, page, frm1 } = await getFrame();
  if (!frm1) {
    await browser.disconnect();
    log('FATAL: task-editor frame not found');
    process.exit(1);
  }

  const liveTask = await extractTaskFromPuppeteerFrame(frm1, 400);
  const liveCheck = validateRatingsForTask(liveTask, ratings);
  if (!liveCheck.ok) {
    await browser.disconnect();
    log(`FATAL STALE GUARD: ${liveCheck.issues.join('; ')}`);
    process.exit(1);
  }
  log(`fill start fingerprint=${liveTask.fingerprint}`);

  const existing = await verifyFormSubmittableOn(page, frm1);
  if (existing.ok) {
    log(`form already complete ${JSON.stringify(existing.form)}`);
    writeFilledFlag(liveTask.fingerprint, existing.form);
    fs.writeFileSync(path.join(RUNS, 'submittable.flag'), new Date().toISOString());
    await browser.disconnect();
    process.exit(0);
  }

  const result = await fillAndVerifySubmittable(page, frm1, ratings, { log });
  await browser.disconnect();

  if (!result.ok) {
    log(`FATAL fill-verify: ${result.issues.join('; ')}`);
    try { fs.unlinkSync(FORM_FILLED); } catch {}
    try { fs.unlinkSync(path.join(RUNS, 'submittable.flag')); } catch {}
    process.exit(1);
  }

  writeFilledFlag(task.fingerprint || liveTask.fingerprint, result.form);
  log(`fill OK TPT=${existing.tpt}s form=${JSON.stringify(result.form)}`);
  process.exit(0);
}

main().catch((e) => {
  log(`FATAL: ${e.message}`);
  process.exit(1);
});
