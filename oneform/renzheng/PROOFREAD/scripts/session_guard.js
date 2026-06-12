/**
 * session_guard.js — Daily session time tracker and safety guard.
 *
 * Tracks cumulative active time across the day. Warns at thresholds.
 * Writes state to runs/session_state.json so it persists across script restarts.
 *
 * Usage:
 *   node scripts/session_guard.js start    — Record session start
 *   node scripts/session_guard.js stop     — Record session stop, show totals
 *   node scripts/session_guard.js status   — Show current day totals
 *   node scripts/session_guard.js reset    — Reset daily counters (new day)
 *
 * Limits (from Lighthouse policy):
 *   - Max total time: 8h (warn at 6.5h, hard stop at 7.5h)
 *   - Max tasks: 30/day (soft recommendation)
 */

const fs = require('fs');
const path = require('path');

const STATE_FILE = path.join(__dirname, '..', 'runs', 'session_state.json');
const MAX_TOTAL_HOURS = 8;
const WARN_HOURS = 6.5;
const HARD_STOP_HOURS = 7.5;

function loadState() {
  try {
    const data = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
    const today = new Date().toISOString().slice(0, 10);
    if (data.date !== today) {
      return { date: today, sessions: [], tasksCompleted: 0, totalActiveMs: 0, currentStart: null };
    }
    return data;
  } catch {
    const today = new Date().toISOString().slice(0, 10);
    return { date: today, sessions: [], tasksCompleted: 0, totalActiveMs: 0, currentStart: null };
  }
}

function saveState(state) {
  fs.mkdirSync(path.dirname(STATE_FILE), { recursive: true });
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

function formatMs(ms) {
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  return `${h}h ${m}m`;
}

function printStatus(state) {
  const totalMs = state.totalActiveMs + (state.currentStart ? Date.now() - state.currentStart : 0);
  const totalHours = totalMs / 3600000;
  const remainingMs = Math.max(0, HARD_STOP_HOURS * 3600000 - totalMs);

  console.log('═══════════════════════════════════════════');
  console.log(`  📅 Date: ${state.date}`);
  console.log(`  ⏱  Total time: ${formatMs(totalMs)} / ${MAX_TOTAL_HOURS}h`);
  console.log(`  📝 Tasks completed: ${state.tasksCompleted}`);
  console.log(`  ⏳ Remaining safe time: ${formatMs(remainingMs)}`);
  console.log(`  📊 Sessions today: ${state.sessions.length}`);
  if (state.currentStart) {
    const sessionMs = Date.now() - state.currentStart;
    console.log(`  🟢 Current session: ${formatMs(sessionMs)} (running)`);
  } else {
    console.log(`  ⚪ No active session`);
  }
  console.log('═══════════════════════════════════════════');

  if (totalHours >= HARD_STOP_HOURS) {
    console.log('\n  🚨 HARD STOP! Close the tool NOW! You are at the limit!');
  } else if (totalHours >= WARN_HOURS) {
    console.log(`\n  ⚠️  WARNING: Approaching limit. Finish current task and stop.`);
  }
}

const cmd = process.argv[2];
const state = loadState();

switch (cmd) {
  case 'start':
    if (state.currentStart) {
      console.log('Session already running. Use "stop" first.');
    } else {
      state.currentStart = Date.now();
      saveState(state);
      console.log(`Session started at ${new Date().toTimeString().slice(0, 8)}`);
    }
    printStatus(state);
    break;

  case 'stop':
    if (!state.currentStart) {
      console.log('No active session.');
    } else {
      const duration = Date.now() - state.currentStart;
      state.totalActiveMs += duration;
      state.sessions.push({ start: state.currentStart, end: Date.now(), durationMs: duration });
      state.currentStart = null;
      saveState(state);
      console.log(`Session stopped. Duration: ${formatMs(duration)}`);
    }
    printStatus(state);
    break;

  case 'status':
    printStatus(state);
    break;

  case 'task':
    state.tasksCompleted++;
    saveState(state);
    console.log(`Task count: ${state.tasksCompleted}`);
    printStatus(state);
    break;

  case 'reset':
    const fresh = { date: new Date().toISOString().slice(0, 10), sessions: [], tasksCompleted: 0, totalActiveMs: 0, currentStart: null };
    saveState(fresh);
    console.log('Session state reset for new day.');
    printStatus(fresh);
    break;

  default:
    console.log('Usage: node session_guard.js [start|stop|status|task|reset]');
    break;
}
