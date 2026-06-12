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
    const tabs = [...document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')].map((t) => t.textContent.trim());
    return { respM: respM ? `${respM[1]}/${respM[2]}` : null, tabs };
  });
}

async function main() {
  const browser = await connect();
  const page = (await browser.pages()).find((p) => p.url().includes('starshot')) || (await browser.pages())[0];
  const frm1 = page.frames().find((f) => f.url().includes('task-editor'));
  console.log('start', await scan(frm1));

  const forId = await frm1.evaluate(() => {
    const tab = document.querySelectorAll('[role=tablist]')[0].querySelector('[role=tab][aria-selected=true]');
    const panel = document.getElementById(tab.getAttribute('aria-controls'));
    const group = [...panel.querySelectorAll('.radio-buttons, [role="radiogroup"]')].find((g) => /instructions/i.test(g.textContent));
    const radio = group?.querySelector('input[value="following_instructions"]');
    return radio?.id || null;
  });
  console.log('forId', forId);
  if (!forId) { await browser.disconnect(); return; }

  await frm1.click(`label[for="${forId}"]`);
  await new Promise((r) => setTimeout(r, 500));
  console.log('after puppeteer click IF', await scan(frm1));

  // click all 6 dimensions on Response A via puppeteer
  const dims = ['following_instructions', 'no_issues', 'acceptable', 'make_shorter', 'truthful', 'highly_satisfying'];
  for (const val of dims) {
    const id = await frm1.evaluate((v) => {
      const tab = document.querySelectorAll('[role=tablist]')[0].querySelector('[role=tab][aria-selected=true]');
      const panel = document.getElementById(tab.getAttribute('aria-controls'));
      return panel?.querySelector(`input[value="${v}"]`)?.id || null;
    }, val);
    if (id) {
      await frm1.click(`label[for="${id}"]`);
      await new Promise((r) => setTimeout(r, 150));
    }
  }
  console.log('after all A dims', await scan(frm1));

  // switch to B
  await frm1.evaluate(() => {
    [...document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')][1].click();
  });
  await new Promise((r) => setTimeout(r, 600));
  for (const val of dims) {
    const id = await frm1.evaluate((v) => {
      const tab = document.querySelectorAll('[role=tablist]')[0].querySelector('[role=tab][aria-selected=true]');
      const panel = document.getElementById(tab.getAttribute('aria-controls'));
      return panel?.querySelector(`input[value="${v}"]`)?.id || null;
    }, val);
    if (id) {
      await frm1.click(`label[for="${id}"]`);
      await new Promise((r) => setTimeout(r, 150));
    }
  }
  console.log('after B dims', await scan(frm1));

  await browser.disconnect();
}

main().catch((e) => { console.error(e); process.exit(1); });
