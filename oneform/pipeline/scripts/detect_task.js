#!/usr/bin/env node
/**
 * detect_task.js — Detect what task type is currently loaded in a browser.
 *
 * Usage: node detect_task.js [--browser work-a|work-b|all] [--json]
 *
 * Connects via CDP, scans page URLs and content, matches against task_types.json.
 * Returns: { browser_id, task_type, page_url, confidence }
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const WebSocket = require('ws');

const BROWSERS = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'browsers.json'), 'utf8')
).browsers;
const TASK_TYPES = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'task_types.json'), 'utf8')
).task_types;

function httpGet(url, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, { timeout, headers: { Host: 'localhost:9222' } }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => { try { resolve(JSON.parse(d)); } catch { resolve(d); } });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  });
}

function wsEval(wsUrl, js, timeout = 8000) {
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
      if (msg.id === 1) {
        clearTimeout(timer);
        ws.close();
        resolve(msg?.result?.result?.value ?? null);
      }
    });
    ws.on('error', e => { clearTimeout(timer); reject(e); });
  });
}

async function detectOnBrowser(browser) {
  const results = [];
  let pages;
  try {
    pages = await httpGet(`${browser.cdp}/json/list`);
  } catch {
    return [{ browser_id: browser.id, task_type: null, error: 'cdp_unreachable' }];
  }
  if (!Array.isArray(pages)) return [{ browser_id: browser.id, task_type: null, error: 'bad_response' }];

  const taskPages = pages.filter(p =>
    p.type === 'page' && (p.url.includes('tryrating') || p.url.includes('starshot') || p.url.includes('survey'))
  );

  if (taskPages.length === 0) {
    return [{ browser_id: browser.id, task_type: null, status: 'no_task_page' }];
  }

  for (const pg of taskPages) {
    const wsUrl = pg.webSocketDebuggerUrl;
    if (!wsUrl) continue;

    let bodySnippet = '';
    try {
      bodySnippet = await wsEval(wsUrl, `(() => {
        const b = document.body?.innerText || '';
        return b.substring(0, 2000);
      })()`);
    } catch { continue; }

    let matched = null;
    let confidence = 0;
    for (const [typeId, def] of Object.entries(TASK_TYPES)) {
      for (const marker of (def.page_markers || [])) {
        const lm = marker.toLowerCase();
        const lb = (bodySnippet || '').toLowerCase();
        const lu = (pg.url || '').toLowerCase();
        if (lb.includes(lm) || lu.includes(lm) || (pg.title || '').toLowerCase().includes(lm)) {
          const score = lb.includes(lm) ? 0.9 : 0.6;
          if (score > confidence) {
            matched = typeId;
            confidence = score;
          }
        }
      }
    }

    // Fallback: check for generic survey page with tasks
    if (!matched && bodySnippet && !bodySnippet.includes('No more surveys')) {
      matched = 'UNKNOWN';
      confidence = 0.3;
    }

    results.push({
      browser_id: browser.id,
      task_type: matched,
      confidence,
      page_url: pg.url?.slice(0, 120),
      page_title: pg.title?.slice(0, 80),
    });
  }

  return results.length ? results : [{ browser_id: browser.id, task_type: null, status: 'no_match' }];
}

async function main() {
  const args = process.argv.slice(2);
  const jsonMode = args.includes('--json');
  const browserFilter = args.find((a, i) => args[i - 1] === '--browser') || 'all';

  const targets = browserFilter === 'all'
    ? BROWSERS.filter(b => b.role === 'worker')
    : BROWSERS.filter(b => b.id === browserFilter);

  if (targets.length === 0) {
    console.error(`No browser found for filter: ${browserFilter}`);
    process.exit(1);
  }

  const allResults = [];
  for (const b of targets) {
    const r = await detectOnBrowser(b);
    allResults.push(...r);
  }

  if (jsonMode) {
    console.log(JSON.stringify(allResults, null, 2));
  } else {
    for (const r of allResults) {
      const icon = r.task_type && r.task_type !== 'UNKNOWN' ? '🎯' : (r.task_type === 'UNKNOWN' ? '❓' : '—');
      console.log(`${icon} [${r.browser_id}] ${r.task_type || r.status || r.error} (${(r.confidence * 100 | 0)}%) ${r.page_url || ''}`);
    }
  }
}

main().catch(e => { console.error(e); process.exit(1); });
