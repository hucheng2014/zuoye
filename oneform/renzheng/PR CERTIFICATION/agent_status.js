#!/usr/bin/env node
/**
 * Foreground agent checkpoint — run after each extract or when user asks "why not submitted".
 * Prints actionable next steps; does NOT replace agent judgment.
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const {
  RUNS,
  loadTaskFile,
  ratingsReadyStrict,
  ROOT,
} = require('./task_utils');

const FORM_FILLED = path.join(RUNS, 'form_filled.flag');
const GRADE_NOW = path.join(RUNS, 'GRADE_NOW.json');
const OVERDUE = path.join(RUNS, 'OVERDUE_ALERT.json');

function readJson(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return null; }
}

function main() {
  const task = loadTaskFile();
  const ratingsOk = ratingsReadyStrict();
  const formFlag = readJson(FORM_FILLED);
  const formOk = ratingsOk && formFlag?.fingerprint === task?.fingerprint &&
    fs.existsSync(path.join(RUNS, 'submittable.flag'));

  let tpt = -1;
  let postOk = null;
  try {
    const v = JSON.parse(execSync(`node "${path.join(ROOT, 'verify_task.js')}" --form-only`, {
      cwd: ROOT, encoding: 'utf8', timeout: 20000,
    }));
    tpt = v.tpt;
    if (!formOk && v.form?.responsesComplete) {
      // page may be filled but flag missing
    }
  } catch {}

  try {
    postOk = JSON.parse(execSync(`node "${path.join(ROOT, 'verify_task.js')}" --after`, {
      cwd: ROOT, encoding: 'utf8', timeout: 20000,
    }));
  } catch {}

  const actions = [];
  if (postOk?.onSuccess && postOk?.hasNext) {
    actions.push('CLICK Next Task → extract → grade → fill → restart bridge');
  } else if (!task?.fingerprint) {
    actions.push('No task — open TryRating / click Start');
  } else if (!ratingsOk) {
    actions.push(`GRADE NOW: write current_ratings.json fingerprint=${task.fingerprint}`);
    actions.push('Run: node validate_ratings.js');
  } else if (!formOk && tpt < 720) {
    actions.push('FILL NOW: node fill_from_ratings.js');
  } else if (formOk && tpt >= 720) {
    actions.push('SUBMIT NOW: node submit_from_ratings.js --submit-only');
  } else if (formOk && tpt < 720) {
    actions.push(`Wait until TPT≥720 (now ${tpt}s) — form pre-filled OK`);
  } else if (tpt >= 720) {
    actions.push('OVERDUE — grade + fill + submit immediately');
  }

  const status = {
    at: new Date().toISOString(),
    fingerprint: task?.fingerprint || null,
    tpt,
    ratingsOk,
    formOk,
    onSuccess: postOk?.onSuccess || false,
    hasNext: postOk?.hasNext || false,
    gradeNow: fs.existsSync(GRADE_NOW),
    overdue: fs.existsSync(OVERDUE),
    bridgeRunning: (() => {
      try {
        execSync('pgrep -f "node ' + path.join(ROOT, 'task_bridge.js') + '"', { stdio: 'ignore' });
        return true;
      } catch { return false; }
    })(),
    agentActions: actions,
  };

  console.log(JSON.stringify(status, null, 2));
  if (actions.length) {
    console.error('\n>>> AGENT MUST DO:\n' + actions.map((a) => `  • ${a}`).join('\n'));
  }
  process.exit(actions.some((a) => /NOW|OVERDUE|CLICK/.test(a)) ? 2 : 0);
}

if (require.main === module) main();
