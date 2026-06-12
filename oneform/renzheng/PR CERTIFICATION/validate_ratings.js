#!/usr/bin/env node
/**
 * CLI stale-ratings guard — exit 0 only when current_ratings.json matches current_task.json.
 */
const { assertRatingsReady, validateRatingsForTask, loadTaskFile, loadRatingsFile } = require('./task_utils');

function main() {
  try {
    const { task, ratings } = assertRatingsReady();
    console.log(JSON.stringify({
      ok: true,
      fingerprint: task.fingerprint,
      gradedAt: ratings.gradedAt,
      ratingMethod: ratings.ratingMethod,
    }, null, 2));
    process.exit(0);
  } catch (e) {
    const task = loadTaskFile();
    const ratings = loadRatingsFile();
    const detail = task && ratings ? validateRatingsForTask(task, ratings) : { issues: [e.message] };
    console.error(JSON.stringify({ ok: false, error: e.message, issues: detail.issues }, null, 2));
    process.exit(1);
  }
}

if (require.main === module) main();
