#!/usr/bin/env node
/**
 * monitor.js — Continuous task-availability monitor.
 *
 * Polls the oneform browser for new tasks. When tasks appear:
 *   1. Desktop notification (notify-send)
 *   2. Writes event to pipeline/runs/events.jsonl
 *   3. Optionally auto-starts a lane via lane.js
 *
 * Usage:
 *   node monitor.js [--interval 300] [--auto-start] [--browser oneform]
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');

const SCRIPTS = __dirname;
const BROWSERS = JSON.parse(fs.readFileSync(path.join(SCRIPTS, 'browsers.json'), 'utf8')).browsers;
const EVENTS_FILE = path.join(SCRIPTS, '..', 'runs', 'events.jsonl');

const args = process.argv.slice(2);
function arg(name, def) {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] ? args[i + 1] : def;
}
const flag = name => args.includes(`--${name}`);

const intervalSec = parseInt(arg('interval', '300'), 10);
const autoStart = flag('auto-start');
const browserId = arg('browser', 'oneform');

const browser = BROWSERS.find(b => b.id === browserId);
if (!browser) { console.error(`Unknown browser: ${browserId}`); process.exit(1); }

function log(msg) {
  const ts = new Date().toISOString().replace('T', ' ').slice(0, 19);
  console.log(`[${ts}] [monitor] ${msg}`);
}

function emitEvent(type, data) {
  const evt = { ts: new Date().toISOString(), type, ...data };
  fs.appendFileSync(EVENTS_FILE, JSON.stringify(evt) + '\n');
  return evt;
}

function httpGet(url, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, { timeout, headers: { Host: 'localhost:9222' } }, res => {
      let d = ''; res.on('data', c => d += c);
      res.on('end', () => { try { resolve(JSON.parse(d)); } catch { resolve(d); } });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  });
}

function wsEval(wsUrl, js, timeout = 8000) {
  const WebSocket = require('ws');
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    const timer = setTimeout(() => { ws.close(); reject(new Error('ws timeout')); }, timeout);
    ws.on('open', () => {
      ws.send(JSON.stringify({
        id: 1, method: 'Runtime.evaluate',
        params: { expression: js, returnByValue: true, awaitPromise: true }
      }));
    });
    ws.on('message', raw => {
      const msg = JSON.parse(raw);
      if (msg.id === 1) { clearTimeout(timer); ws.close(); resolve(msg?.result?.result?.value ?? null); }
    });
    ws.on('error', e => { clearTimeout(timer); reject(e); });
  });
}

function notify(title, body) {
  try {
    execSync(`notify-send -u critical "${title}" "${body}"`, {
      env: {
        ...process.env,
        DISPLAY: ':0',
        DBUS_SESSION_BUS_ADDRESS: `unix:path=/run/user/${process.getuid?.() ?? 1000}/bus`,
      },
    });
  } catch { /* silent */ }
}

async function checkForTasks() {
  let pages;
  try {
    pages = await httpGet(`${browser.cdp}/json/list`);
  } catch (e) {
    log(`Browser unreachable: ${e.message}`);
    emitEvent('browser_down', { browser_id: browser.id, error: e.message });
    return null;
  }

  if (!Array.isArray(pages)) return null;

  const taskPages = pages.filter(p =>
    p.type === 'page' && (p.url?.includes('tryrating') || p.url?.includes('survey'))
  );

  for (const pg of taskPages) {
    const wsUrl = pg.webSocketDebuggerUrl;
    if (!wsUrl) continue;

    try {
      // Click "Check Now" if present
      await wsEval(wsUrl, `(() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
          if (b.textContent.trim().toLowerCase().includes('check now')) { b.click(); return 'clicked'; }
        }
        return 'no_button';
      })()`);

      await new Promise(r => setTimeout(r, 5000));

      // Check page content
      const status = await wsEval(wsUrl, `(() => {
        const t = document.body?.innerText || '';
        if (t.includes('No more surveys')) return 'no_tasks';
        if (t.includes('QUERY') && t.includes('RESULT AD')) return 'AD_TASKS';
        if (t.includes('keyword') && t.includes('expansion')) return 'ADJIAN_TASKS';
        if (t.toLowerCase().includes('proofreading') || t.toLowerCase().includes('proofread')) return 'PROOFREAD_TASKS';
        if (t.toLowerCase().includes('intelligent polls') || t.toLowerCase().includes('poll')) return 'TA_POLLS_TASKS';
        if (t.toLowerCase().includes('mail smart reply') || t.toLowerCase().includes('msr')) return 'MAIL_TASKS';
        if (t.toLowerCase().includes('message reply') || t.toLowerCase().includes('psr')) return 'TAMESSAGE_TASKS';
        if (t.toLowerCase().includes('rate') && !t.includes('No more')) return 'POSSIBLE_TASKS';
        return 'no_tasks';
      })()`);

      if (status && status.includes('TASKS') && !status.includes('no_tasks')) {
        return { browser_id: browser.id, status, page_url: pg.url };
      }
    } catch (e) {
      log(`Error checking page: ${e.message}`);
    }
  }

  return null;
}

let activeLane = null;

async function loop() {
  log(`Monitor started. Interval=${intervalSec}s, auto-start=${autoStart}, browser=${browserId}`);
  fs.mkdirSync(path.dirname(EVENTS_FILE), { recursive: true });

  while (true) {
    const result = await checkForTasks();

    if (result) {
      log(`🎯 TASKS FOUND: ${result.status}`);
      emitEvent('tasks_found', result);
      notify('🎯 TryRating 有新题!', result.status);

      if (autoStart && !activeLane) {
        // Determine which worker browser to use based on task type
        const taskType = result.status.replace('_TASKS', '');
        const workerBrowser = taskType === 'PROOFREAD' ? 'work-b' : 'work-a';
        log(`Auto-starting lane on ${workerBrowser} for ${taskType}...`);
        emitEvent('lane_started', { browser: workerBrowser, task_type: taskType });

        activeLane = spawn('node', [path.join(SCRIPTS, 'lane.js'), '--browser', workerBrowser, '--max-tasks', '5'], {
          stdio: 'inherit',
          cwd: SCRIPTS,
        });
        activeLane.on('exit', code => {
          log(`Lane exited with code ${code}`);
          emitEvent('lane_finished', { browser: workerBrowser, exit_code: code });
          activeLane = null;
        });
      }
    } else {
      log('No tasks found.');
    }

    await new Promise(r => setTimeout(r, intervalSec * 1000));
  }
}

loop().catch(e => { log(`FATAL: ${e.message}`); process.exit(1); });
