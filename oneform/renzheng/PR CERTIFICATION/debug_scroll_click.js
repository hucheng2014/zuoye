#!/usr/bin/env node
const puppeteer = require('puppeteer-core');
const { CDP_URL, CDP_FALLBACK } = require('./config');

async function connect() {
  for (const url of [CDP_URL, CDP_FALLBACK]) {
    try { return await puppeteer.connect({ browserURL: url, defaultViewport: null }); } catch {}
  }
  throw new Error('no cdp');
}

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

async function scan(frm1) {
  return frm1.evaluate(() => {
    const text = document.body.innerText;
    const respM = text.match(/RESPONSES\s*(\d+)\/(\d+)\s*Complete/i);
    const tabs = [...document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')].map((t) => t.textContent.trim());
    return { respM: respM ? `${respM[1]}/${respM[2]}` : null, tabs };
  });
}

async function clickTab(frm1, idx) {
  await frm1.evaluate((i) => {
    const tab = document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')[i];
    tab.scrollIntoView({ block: 'center' });
    tab.click();
    tab.dispatchEvent(new Event('click', { bubbles: true }));
  }, idx);
  await sleep(500);
}

async function clickRadio(frm1, value) {
  return frm1.evaluate((val) => {
    const tab = document.querySelectorAll('[role=tablist]')[0].querySelector('[role=tab][aria-selected=true]');
    const panel = document.getElementById(tab.getAttribute('aria-controls'));
    const radio = panel.querySelector(`input[type=radio][value="${val}"]`);
    if (!radio) return false;
    const label = radio.closest('label') || radio;
    label.scrollIntoView({ block: 'center' });
    label.click();
    radio.checked = true;
    radio.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    radio.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
    radio.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    radio.dispatchEvent(new Event('input', { bubbles: true }));
    radio.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  }, value);
}

async function main() {
  const browser = await connect();
  const page = (await browser.pages()).find((p) => p.url().includes('starshot'));
  const frm1 = page.frames().find((f) => f.url().includes('task-editor'));
  console.log('start', await scan(frm1));

  const vals = ['following_instructions', 'no_issues', 'acceptable', 'make_shorter', 'truthful', 'highly_satisfying'];
  for (const idx of [0, 1]) {
    await clickTab(frm1, idx);
    console.log(`tab ${idx}`, await scan(frm1));
    for (const v of vals) {
      const ok = await clickRadio(frm1, v);
      if (!ok) console.log('miss', v);
      await sleep(200);
    }
    console.log(`after fill tab ${idx}`, await scan(frm1));
  }
  await browser.disconnect();
}

main().catch((e) => { console.error(e); process.exit(1); });
