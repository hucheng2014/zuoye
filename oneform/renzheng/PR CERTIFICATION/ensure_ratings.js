#!/usr/bin/env node
/**
 * Closed-loop ratings: try LLM grade_task.js when ratings missing or stale.
 * Bridge calls this on extract and when submit is blocked — never spin TPT forever.
 */
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const {
  RUNS,
  NEEDS_GRADING,
  loadTaskFile,
  loadRatingsFile,
  validateRatingsForTask,
  ROOT,
} = require('./task_utils');

const LOG = path.join(RUNS, 'ensure_ratings.log');

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.mkdirSync(RUNS, { recursive: true });
  fs.appendFileSync(LOG, line);
  console.log(msg);
}

function main() {
  const task = loadTaskFile();
  if (!task?.fingerprint) {
    log('no current_task.json');
    process.exit(1);
  }

  const ratings = loadRatingsFile();
  if (ratings) {
    const v = validateRatingsForTask(task, ratings);
    if (v.ok) {
      try { fs.unlinkSync(NEEDS_GRADING); } catch {}
      log(`ratings OK fingerprint=${task.fingerprint}`);
      process.exit(0);
    }
    log(`ratings invalid: ${v.issues.join('; ')}`);
  } else {
    log(`no ratings for fingerprint=${task.fingerprint}`);
  }

  const gradeNow = {
    at: new Date().toISOString(),
    fingerprint: task.fingerprint,
    action: 'Agent must write current_ratings.json and run validate_ratings.js (LLM auto-grade unavailable)',
  };
  fs.writeFileSync(path.join(RUNS, 'GRADE_NOW.json'), JSON.stringify(gradeNow, null, 2));
  log(`GRADE_NOW written fingerprint=${task.fingerprint} — agent manual grade required`);
  process.exit(1);

  const after = loadRatingsFile();
  const v2 = validateRatingsForTask(task, after);
  if (!v2.ok) {
    log(`post-grade still invalid: ${v2.issues.join('; ')}`);
    process.exit(1);
  }
  try { fs.unlinkSync(NEEDS_GRADING); } catch {}
  log(`graded OK fingerprint=${task.fingerprint}`);
  process.exit(0);
}

if (require.main === module) main();
