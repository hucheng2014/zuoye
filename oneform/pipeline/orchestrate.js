#!/usr/bin/env node
/**
 * orchestrate.js — Multi-lane orchestrator.
 *
 * Runs monitor + multiple worker lanes in parallel.
 * Respects daily hour limits and task caps per lane.
 *
 * Usage:
 *   node orchestrate.js [--lanes work-a,work-b] [--monitor] [--max-hours 7]
 *
 * The orchestrator:
 *   1. Starts a monitor on the oneform browser (task availability poller)
 *   2. Starts one lane per worker browser
 *   3. Tracks cumulative hours per lane via session_guard
 *   4. Shuts down lanes when daily limits are reached
 *   5. Writes structured events to runs/events.jsonl
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const SCRIPTS = path.join(__dirname, 'scripts');
const RUNS = path.join(__dirname, 'runs');
const EVENTS_FILE = path.join(RUNS, 'events.jsonl');

fs.mkdirSync(RUNS, { recursive: true });

const args = process.argv.slice(2);
function arg(name, def) {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] ? args[i + 1] : def;
}
const flag = name => args.includes(`--${name}`);

const laneIds = arg('lanes', 'work-a,work-b').split(',');
const runMonitor = flag('monitor') || true; // always monitor
const maxHours = parseFloat(arg('max-hours', '7'));
const maxTasks = parseInt(arg('max-tasks', '30'), 10);
const dryRun = flag('dry-run');

function log(msg) {
  const ts = new Date().toISOString().replace('T', ' ').slice(0, 19);
  const line = `[${ts}] [orchestrator] ${msg}`;
  console.log(line);
  fs.appendFileSync(path.join(RUNS, 'orchestrator.log'), line + '\n');
}

function emitEvent(type, data) {
  const evt = { ts: new Date().toISOString(), type, ...data };
  fs.appendFileSync(EVENTS_FILE, JSON.stringify(evt) + '\n');
}

const children = [];

function startProcess(name, cmd, cmdArgs, opts = {}) {
  log(`Starting ${name}: ${cmd} ${cmdArgs.join(' ')}`);
  const child = spawn(cmd, cmdArgs, {
    stdio: ['ignore', 'pipe', 'pipe'],
    cwd: opts.cwd || SCRIPTS,
    env: { ...process.env, ...opts.env },
  });

  const prefix = `[${name}]`;
  child.stdout.on('data', d => {
    for (const line of d.toString().split('\n').filter(Boolean)) {
      console.log(`${prefix} ${line}`);
    }
  });
  child.stderr.on('data', d => {
    for (const line of d.toString().split('\n').filter(Boolean)) {
      console.error(`${prefix} ${line}`);
    }
  });
  child.on('exit', code => {
    log(`${name} exited with code ${code}`);
    emitEvent('process_exit', { name, exit_code: code });
  });

  children.push({ name, child });
  return child;
}

function shutdown(signal) {
  log(`Received ${signal}. Shutting down ${children.length} children...`);
  emitEvent('orchestrator_shutdown', { signal, children: children.length });
  for (const { name, child } of children) {
    log(`Killing ${name} (pid=${child.pid})`);
    child.kill('SIGTERM');
  }
  setTimeout(() => {
    for (const { child } of children) {
      if (!child.killed) child.kill('SIGKILL');
    }
    process.exit(0);
  }, 5000);
}

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));

function main() {
  log(`═══════════════════════════════════════════`);
  log(`  Oneform Agent Pipeline — Orchestrator`);
  log(`  Lanes: ${laneIds.join(', ')}`);
  log(`  Max hours: ${maxHours}h, Max tasks: ${maxTasks}`);
  log(`  Dry run: ${dryRun}`);
  log(`═══════════════════════════════════════════`);
  emitEvent('orchestrator_start', { lanes: laneIds, max_hours: maxHours, max_tasks: maxTasks, dry_run: dryRun });

  // Start monitor
  if (runMonitor) {
    startProcess('monitor', 'node', [
      path.join(SCRIPTS, 'monitor.js'),
      '--interval', '300',
      '--browser', 'oneform',
    ]);
  }

  // Start lanes
  for (const laneId of laneIds) {
    const laneArgs = [
      path.join(SCRIPTS, 'lane.js'),
      '--browser', laneId,
      '--max-tasks', String(maxTasks),
    ];
    if (dryRun) laneArgs.push('--dry-run');
    startProcess(`lane:${laneId}`, 'node', laneArgs);
  }

  log('All processes started. Ctrl+C to shut down.');
}

main();
