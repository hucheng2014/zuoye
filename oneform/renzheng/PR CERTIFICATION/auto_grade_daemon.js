/**
 * Ratings watchdog — no CDP, no LLM.
 * Monitors current_task.json vs current_ratings.json; logs when agent grading is pending.
 * LLM grade_task.js is NOT used — agent writes current_ratings.json manually.
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const {
  RUNS,
  NEEDS_GRADING,
  loadTaskFile,
  loadRatingsFile,
  validateRatingsForTask,
} = require('./task_utils');

const LOG_FILE = path.join(RUNS, 'grade_daemon.log');
const PID_FILE = path.join(RUNS, 'grade_daemon.pid');
const POLL_MS = parseInt(process.env.PR_GRADE_POLL_MS || '45000', 10);

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  process.stdout.write(line);
  fs.mkdirSync(RUNS, { recursive: true });
  fs.appendFileSync(LOG_FILE, line, { flag: 'a' });
}

function checkRatings() {
  const task = loadTaskFile();
  if (!task?.fingerprint) return { pending: false, reason: 'no task fingerprint' };

  const ratings = loadRatingsFile();
  if (!ratings) return { pending: true, task, reason: 'no ratings file — agent must grade' };

  const v = validateRatingsForTask(task, ratings);
  if (!v.ok) return { pending: true, task, reason: v.issues.join('; ') };

  try { fs.unlinkSync(NEEDS_GRADING); } catch {}
  return { pending: false, task, ratings };
}

async function main() {
  fs.mkdirSync(RUNS, { recursive: true });
  if (fs.existsSync(PID_FILE)) {
    const old = parseInt(fs.readFileSync(PID_FILE, 'utf8'), 10);
    try { process.kill(old, 0); log(`ratings_watchdog already pid=${old}`); process.exit(0); } catch {}
  }
  fs.writeFileSync(PID_FILE, String(process.pid));
  log(`ratings_watchdog pid=${process.pid} poll=${POLL_MS}ms (LLM grade disabled)`);

  let lastPending = null;
  let pendingSince = null;
  while (true) {
    try {
      const check = checkRatings();
      const key = check.pending ? `${check.task?.fingerprint}:${check.reason}` : 'ok';
      if (check.pending) {
        if (!pendingSince) pendingSince = Date.now();
        const waitSec = Math.floor((Date.now() - pendingSince) / 1000);
        if (waitSec >= 90 && waitSec % 90 < POLL_MS / 1000) {
          log(`PENDING ${waitSec}s — running ensure_ratings.js`);
          try {
            execSync(`node "${path.join(__dirname, 'ensure_ratings.js')}"`, {
              cwd: __dirname,
              stdio: ['ignore', 'pipe', 'pipe'],
              timeout: 320000,
            });
          } catch (e) {
            log(`ensure_ratings failed: ${(e.stderr || e.message || '').toString().slice(0, 200)}`);
          }
        }
      } else {
        pendingSince = null;
      }
      if (key !== lastPending) {
        if (check.pending) {
          log(`PENDING grade fingerprint=${check.task.fingerprint}: ${check.reason}`);
        } else if (check.ratings) {
          log(`Ratings OK fingerprint=${check.task.fingerprint}`);
        }
        lastPending = key;
      }
    } catch (e) {
      log(`ERROR: ${e.message}`);
    }
    await new Promise((r) => setTimeout(r, POLL_MS));
  }
}

process.on('SIGTERM', () => { try { fs.unlinkSync(PID_FILE); } catch {}; process.exit(0); });
main().catch((e) => { log(`FATAL: ${e.message}`); process.exit(1); });
