#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const http = require('http');
const WebSocket = require('ws');

const outDir = __dirname;
const today = new Date().toISOString().slice(0, 10);
const cdpEndpoints = ['http://127.0.0.1:9233', 'http://127.0.0.1:9232'];

function getJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, res => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(body)); } catch (error) { reject(error); }
      });
    }).on('error', reject);
  });
}

async function listTabs() {
  for (const endpoint of cdpEndpoints) {
    try {
      const tabs = await getJson(endpoint + '/json/list');
      return { endpoint, tabs };
    } catch (_) {}
  }
  throw new Error('Cannot connect to controlled-browser CDP on 9233 or 9232. If login/captcha is needed, open http://127.0.0.1:6082/vnc.html');
}

function connect(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let id = 0;
  const pending = new Map();
  ws.on('message', data => {
    const msg = JSON.parse(data);
    if (msg.id && pending.has(msg.id)) {
      const item = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) item.reject(new Error(JSON.stringify(msg.error)));
      else item.resolve(msg.result);
    }
  });
  return new Promise((resolve, reject) => {
    ws.on('open', () => {
      resolve((method, params = {}) => new Promise((res, rej) => {
        const msg = { id: ++id, method, params };
        pending.set(msg.id, { resolve: res, reject: rej });
        ws.send(JSON.stringify(msg));
      }));
    });
    ws.on('error', reject);
  }).then(send => ({ ws, send }));
}

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
function clean(s) { return (s || '').replace(/[ \t]+/g, ' ').replace(/\n{3,}/g, '\n\n').trim(); }
function mask(s) { return clean(s).replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '[email masked]'); }
function lineMatch(t, re) { const m = t.match(re); return m ? m[1].trim() : ''; }
function between(t, a, b) { let i = t.indexOf(a); if (i < 0) return ''; i += a.length; let j = b ? t.indexOf(b, i) : -1; if (j < 0) j = t.length; return t.slice(i, j).trim(); }
function meta(t) {
  const cats = ['Tag Tool Issues', 'Other topics', 'TA/TC', 'VCG', 'CYU', 'LE'];
  const re = new RegExp('ID Project Category View Status Date Submitted Last Update\\n(\\d+)\\s+(.+?)\\s+(' + cats.map(c => c.replace('/', '\\/')).join('|') + ')\\s+(private|public)\\s+(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2})\\s+(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2})', 's');
  const m = t.match(re);
  return m ? { id: m[1], project: m[2].trim(), category: m[3], view: m[4], submitted: m[5], updated: m[6] } : {};
}
function status(t) { return lineMatch(t, /Reporter[^\n]*\nStatus\s+([^\n]+?)\s*(?:\n|$)/) || lineMatch(t, /\nStatus\s+([^\n]+?)\s*(?:\n|$)/); }
function summary(t) { return lineMatch(t, /Summary\s+\d+:\s*(.+)/); }
function reporter(t) { return lineMatch(t, /Reporter\s+([^\n]+)/); }
function descOf(t) { return mask(between(t, 'Description ', '\n\n Activities') || between(t, 'Description ', '\n Activities')); }
function activities(t) { return between(t, 'Activities', 'Issue History'); }
function history(t) { return between(t, 'Issue History', 'Powered by MantisBT'); }
function histBullets(h) { return h.split('\n').map(l => l.trim()).filter(l => /^\d{4}-\d{2}-\d{2}/.test(l)).map(l => '- ' + mask(l)).join('\n'); }
function noteBullets(act) {
  const lines = act.split('\n').map(l => l.trim()).filter(Boolean).filter(l => !/^Add Note$|^Note$|^Upload Files$|^Maximum size:|^Attach files/.test(l));
  const chunks = []; let cur = [];
  for (const l of lines) {
    if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(l) && cur.length) { chunks.push(cur); cur = [l]; }
    else cur.push(l);
  }
  if (cur.length) chunks.push(cur);
  return chunks.map(c => '- ' + mask(c.join(' | '))).join('\n');
}
function insight(t, d, act) {
  const s = summary(t), cat = meta(t).category || '', st = status(t);
  const lower = (s + ' ' + d + ' ' + act).toLowerCase();
  const parts = [];
  if (lower.includes('cherry opal')) parts.push('Cherry Opal task availability / task-notification issue.');
  if (lower.includes('no tasks')) parts.push('The reporter says the tool shows no tasks and worries about work hours or payment.');
  if (lower.includes('certification') || lower.includes('webinar')) parts.push('Certification, webinar link, or eligibility synchronization issue.');
  if (lower.includes('tpt')) parts.push('The post discusses TPT limits, actual completion time, or certification TPT.');
  if (cat === 'VCG') parts.push('VCG-related issue, mainly about Edit Model / ADM / Direct Manipulation / grading workflow.');
  if (lower.includes('pii transcription')) parts.push('PII Transcription workflow/task-routing issue.');
  if (st === 'closed') parts.push('The issue is currently closed.');
  if (st === 'pending') parts.push('The issue is still pending.');
  return parts.join(' ') || 'General issue visible in the daily timeline.';
}

function writeSummary(details) {
  let md = '# Global Query Detailed Daily Summary (' + today + ')\n\n';
  md += 'Source: controlled-browser Docker browser via CDP.\n\n';
  md += '## Overview\n\n- Visible issues: ' + details.length + '\n- Emails are masked as `[email masked]`.\n\n';
  md += '## Issue Index\n\n| Issue | Title | Category | Status | Submitted | Last Updated |\n|---|---|---|---|---|---|\n';
  for (const x of details) {
    const t = x.text, m = meta(t);
    md += '| ' + x.issue + ' | ' + mask(summary(t)) + ' | ' + (m.category || '') + ' | ' + (status(t) || '') + ' | ' + (m.submitted || '') + ' | ' + (m.updated || '') + ' |\n';
  }
  md += '\n## Per-Issue Details\n\n';
  for (const x of details) {
    const t = x.text, m = meta(t), d = descOf(t), act = activities(t), hist = history(t);
    const attach = [...new Set((x.attachments || []).map(a => mask(a.text || a.title || a.href)).filter(Boolean))].map(a => '- ' + a).join('\n');
    md += '### ' + x.issue + ': ' + mask(summary(t)) + '\n\n';
    md += '**Metadata**\n\n- Project: ' + (m.project || 'Not extracted') + '\n- Category: ' + (m.category || 'Not extracted') + '\n- Visibility: ' + (m.view || 'Not extracted') + '\n- Status: ' + (status(t) || 'Not extracted') + '\n- Submitted: ' + (m.submitted || 'Not extracted') + '\n- Last updated: ' + (m.updated || 'Not extracted') + '\n- Reporter: ' + mask(reporter(t)) + '\n\n';
    md += '**English summary**\n\n' + insight(t, d, act) + '\n\n';
    md += '**Post content / detail fields**\n\n' + (d || 'No description captured.') + '\n\n';
    md += '**Attachments / screenshots**\n\n' + (attach || 'No attachment detected.') + '\n\n';
    md += '**Replies / comments / activity**\n\n' + (noteBullets(act) || 'No visible replies or comments.') + '\n\n';
    md += '**Handling history**\n\n' + (histBullets(hist) || 'No visible handling history.') + '\n\n';
  }
  fs.writeFileSync(path.join(outDir, 'Global_Query_Detailed_Summary_' + today + '.md'), md);
}

(async () => {
  const { tabs } = await listTabs();
  const tab = tabs.find(t => /globalquery\.oneforma\.com\/my_view_page\.php/.test(t.url)) || tabs.find(t => /globalquery\.oneforma\.com/.test(t.url));
  if (!tab) throw new Error('Global Query tab not found. Open it in the controlled-browser container first.');
  const { ws, send } = await connect(tab.webSocketDebuggerUrl);
  try {
    await send('Runtime.enable');
    await send('Page.enable');
    await send('Page.bringToFront');
    await send('Page.navigate', { url: 'https://globalquery.oneforma.com/my_view_page.php?refresh=true' });
    await sleep(2000);
    const idsResult = await send('Runtime.evaluate', { expression: `(() => [...new Set((document.body.innerText.match(/004\\d{4}/g) || []))])()`, returnByValue: true });
    const ids = idsResult.result.value;
    const details = [];
    for (const issue of ids) {
      const numericId = String(Number(issue));
      await send('Page.navigate', { url: 'https://globalquery.oneforma.com/view.php?id=' + numericId });
      await sleep(1500);
      const expr = `(() => { const clean = s => (s || '').replace(/[ \\t]+/g, ' ').replace(/\\n{3,}/g, '\\n\\n').trim(); const links = Array.from(document.querySelectorAll('a')).map(a => ({ text: clean(a.innerText), href: a.href, title: a.title || '' })).filter(a => a.text || a.title); const attachments = links.filter(a => /attachment|download|Screenshot|png|jpg|jpeg|pdf|\\.txt|\\.doc/i.test(a.text + ' ' + a.href + ' ' + a.title)); return JSON.stringify({ issue: '${issue}', url: location.href, title: document.title, text: clean(document.body.innerText), attachments }); })()`;
      const result = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
      details.push(JSON.parse(result.result.value));
      console.log('fetched', issue);
    }
    fs.writeFileSync(path.join(outDir, '.global_query_issue_details_' + today + '.json'), JSON.stringify(details, null, 2));
    writeSummary(details);
    console.log('saved', details.length, 'issues for', today);
  } finally {
    ws.close();
  }
})().catch(error => {
  console.error(error.message || error);
  process.exit(1);
});
