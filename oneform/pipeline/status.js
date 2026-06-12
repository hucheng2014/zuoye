#!/usr/bin/env node
/**
 * status.js — Pipeline status dashboard.
 *
 * Shows: browsers, detected tasks, today's run stats, active lanes, events.
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const SCRIPTS = path.join(__dirname, 'scripts');
const RUNS = path.join(__dirname, 'runs');

function section(title) { console.log(`\n${'═'.repeat(60)}\n  ${title}\n${'═'.repeat(60)}`); }

async function main() {
  const today = new Date().toISOString().slice(0, 10);

  // 1. Browser status
  section('🖥️  Browser Status');
  try {
    const out = execSync(`node ${path.join(SCRIPTS, 'cdp_probe.js')}`, { encoding: 'utf8', timeout: 10000 });
    console.log(out.trim());
  } catch (e) {
    console.log('  (probe failed)');
  }

  // 2. Task detection
  section('🎯  Task Detection');
  try {
    const out = execSync(`node ${path.join(SCRIPTS, 'detect_task.js')}`, { encoding: 'utf8', timeout: 20000 });
    console.log(out.trim());
  } catch (e) {
    console.log('  (detect failed)');
  }

  // 3. Today's runs
  section(`📊  Today's Runs (${today})`);
  const runDirs = fs.readdirSync(RUNS).filter(d => d.includes(today)).sort();
  if (runDirs.length === 0) {
    console.log('  No runs today.');
  } else {
    for (const d of runDirs) {
      const dir = path.join(RUNS, d);
      const logFile = path.join(dir, 'lane.log');
      if (fs.existsSync(logFile)) {
        const lines = fs.readFileSync(logFile, 'utf8').trim().split('\n');
        const tasks = lines.filter(l => l.includes('completed')).length;
        const errors = lines.filter(l => l.includes('FAILED')).length;
        console.log(`  ${d}: ${tasks} completed, ${errors} failed, ${lines.length} log lines`);
      } else {
        console.log(`  ${d}: (no log)`);
      }
    }
  }

  // 4. Recent events
  section('📋  Recent Events');
  const eventsFile = path.join(RUNS, 'events.jsonl');
  if (fs.existsSync(eventsFile)) {
    const lines = fs.readFileSync(eventsFile, 'utf8').trim().split('\n').slice(-10);
    for (const line of lines) {
      try {
        const evt = JSON.parse(line);
        console.log(`  [${evt.ts?.slice(11, 19)}] ${evt.type} ${evt.status || evt.task_type || evt.error || ''}`);
      } catch { console.log(`  ${line.slice(0, 80)}`); }
    }
  } else {
    console.log('  No events yet.');
  }

  // 5. Claw version
  section('🦀  Claw Code');
  try {
    const ver = execSync(`${process.env.HOME}/.cargo/bin/claw --version`, { encoding: 'utf8', timeout: 5000 });
    console.log('  ' + ver.trim().replace(/\n/g, '\n  '));
  } catch {
    console.log('  claw not found — install from /tmp/claw-code');
  }

  console.log('');
}

main().catch(e => { console.error(e); process.exit(1); });
