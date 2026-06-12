#!/usr/bin/env node
/**
 * cdp_probe.js — Probe all registered browsers and report status.
 *
 * Usage: node cdp_probe.js [--json]
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const BROWSERS = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'browsers.json'), 'utf8')
).browsers;

function fetch(url, timeout = 3000) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, { timeout, headers: { Host: 'localhost:9222' } }, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); } catch { resolve(data); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  });
}

async function probeBrowser(b) {
  const result = { id: b.id, role: b.role, container: b.container, cdp: b.cdp };
  try {
    const ver = await fetch(`${b.cdp}/json/version`);
    result.status = 'up';
    result.browser_version = typeof ver === 'object' ? ver.Browser || ver['User-Agent'] : String(ver).slice(0, 80);
  } catch (e) {
    result.status = 'down';
    result.error = e.message;
  }

  if (result.status === 'up') {
    try {
      const pages = await fetch(`${b.cdp}/json/list`);
      result.pages = Array.isArray(pages) ? pages.filter(p => p.type === 'page').map(p => ({
        title: (p.title || '').slice(0, 60),
        url: (p.url || '').slice(0, 120),
      })) : [];
    } catch {
      result.pages = [];
    }
  }
  return result;
}

async function main() {
  const jsonMode = process.argv.includes('--json');
  const results = await Promise.all(BROWSERS.map(probeBrowser));
  if (jsonMode) {
    console.log(JSON.stringify(results, null, 2));
  } else {
    for (const r of results) {
      const icon = r.status === 'up' ? '✓' : '✗';
      const pages = r.pages ? ` (${r.pages.length} pages)` : '';
      console.log(`[${icon}] ${r.id.padEnd(10)} ${r.role.padEnd(10)} ${r.status}${pages} — ${r.cdp}`);
      if (r.pages) {
        for (const p of r.pages) {
          console.log(`    ${p.title || '(untitled)'} — ${p.url}`);
        }
      }
      if (r.error) console.log(`    Error: ${r.error}`);
    }
  }
}

main().catch(e => { console.error(e); process.exit(1); });
