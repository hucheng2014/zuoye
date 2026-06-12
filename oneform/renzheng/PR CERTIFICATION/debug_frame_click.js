#!/usr/bin/env node
const puppeteer = require('puppeteer-core');
const { CDP_URL, CDP_FALLBACK } = require('./config');

async function connect() {
  for (const url of [CDP_URL, CDP_FALLBACK]) {
    try { return await puppeteer.connect({ browserURL: url, defaultViewport: null }); } catch {}
  }
  throw new Error('no cdp');
}

async function scan(frm1) {
  return frm1.evaluate(() => {
    const text = document.body.innerText;
    const respM = text.match(/RESPONSES\s*(\d+)\/(\d+)\s*Complete/i);
    const tabs = [...document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')].map((t) => ({
      text: t.textContent.trim(),
      selected: t.getAttribute('aria-selected') === 'true',
    }));
    return { respM: respM ? `${respM[1]}/${respM[2]}` : null, tabs };
  });
}

async function scrollTop(frm1) {
  await frm1.evaluate(() => {
    window.scrollTo(0, 0);
    for (const el of document.querySelectorAll('*')) { if (el.scrollTop > 0) el.scrollTop = 0; }
    document.querySelectorAll('[role=tablist]')[0]?.querySelector('[role=tab]')?.scrollIntoView({ block: 'center' });
  });
  await new Promise((r) => setTimeout(r, 300));
}

async function clickTab(frm1, page, index) {
  await scrollTop(frm1);
  const box = await frm1.evaluate((idx) => {
    const tab = document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')[idx];
    const r = tab.getBoundingClientRect();
    const frameEl = window.frameElement;
    const fr = frameEl ? frameEl.getBoundingClientRect() : { left: 0, top: 0 };
    return { x: fr.left + r.left + r.width / 2, y: fr.top + r.top + r.height / 2 };
  }, index);
  await page.mouse.click(box.x, box.y);
}

async function clickRadioValue(frm1, page, value) {
  await scrollTop(frm1);
  const box = await frm1.evaluate((val) => {
    const tab = document.querySelectorAll('[role=tablist]')[0].querySelector('[role=tab][aria-selected=true]');
    const panel = document.getElementById(tab.getAttribute('aria-controls'));
    const radio = panel.querySelector(`input[type=radio][value="${val}"]`);
    const el = radio?.closest('label') || radio;
    el?.scrollIntoView({ block: 'center' });
    const r = el.getBoundingClientRect();
    const frameEl = window.frameElement;
    const fr = frameEl ? frameEl.getBoundingClientRect() : { left: 0, top: 0 };
    return { x: fr.left + r.left + r.width / 2, y: fr.top + r.top + r.height / 2, found: !!radio };
  }, value);
  if (!box.found) return false;
  await page.mouse.click(box.x, box.y);
  return true;
}

async function main() {
  const browser = await connect();
  const page = (await browser.pages()).find((p) => p.url().includes('starshot'));
  const frm1 = page.frames().find((f) => f.url().includes('task-editor'));
  console.log('start', await scan(frm1));

  await clickTab(frm1, page, 0);
  await new Promise((r) => setTimeout(r, 600));
  console.log('tab0', await scan(frm1));

  const vals = ['following_instructions', 'no_issues', 'acceptable', 'make_shorter', 'truthful', 'highly_satisfying'];
  for (const v of vals) {
    await clickRadioValue(frm1, page, v);
    await new Promise((r) => setTimeout(r, 200));
  }
  console.log('after A', await scan(frm1));

  await clickTab(frm1, page, 1);
  await new Promise((r) => setTimeout(r, 600));
  for (const v of vals) {
    await clickRadioValue(frm1, page, v);
    await new Promise((r) => setTimeout(r, 200));
  }
  console.log('after B', await scan(frm1));

  await browser.disconnect();
}

main().catch((e) => { console.error(e); process.exit(1); });
