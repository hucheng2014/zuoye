#!/usr/bin/env node
const { getFrame, clickRadioByLabel, scrollTaskEditorToResponses, sleep } = require('./pr_automation_helper');
const ratings = require('./current_ratings.json');

async function scan(frm1) {
  return frm1.evaluate(() => {
    const text = document.body.innerText;
    const respM = text.match(/RESPONSES\s*(\d+)\/(\d+)\s*Complete/i);
    const tabs = [...document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')].map((t) => t.textContent.trim());
    return { respM: respM ? `${respM[1]}/${respM[2]}` : null, tabs };
  });
}

async function clickTab(frm1, idx) {
  await scrollTaskEditorToResponses(frm1);
  await frm1.evaluate((i) => {
    const tab = document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')[i];
    tab.click();
  }, idx);
  await sleep(600);
}

async function toggleThenSet(frm1, cat, label, altLabel) {
  await clickRadioByLabel(frm1, cat, altLabel, { scope: 'active-tabpanel' });
  await sleep(150);
  return clickRadioByLabel(frm1, cat, label, { scope: 'active-tabpanel' });
}

async function fillResponse(frm1, key, rData) {
  const idx = key.includes('A') ? 0 : 1;
  await clickTab(frm1, idx);
  const steps = [
    ['IF', rData.instructionFollowing, 'Partially following'],
    ['Localization', rData.localization, 'Yes (issues present)'],
    ['Concision', rData.concision, 'Bad'],
    rData.description ? ['Description', rData.description, 'It could have been made longer'] : null,
    ['Truthfulness', rData.truthfulness, 'Partially Truthful'],
    ['Satisfaction', rData.satisfaction, 'Slightly Satisfying'],
  ].filter(Boolean);
  for (const [cat, label, alt] of steps) {
    const res = await toggleThenSet(frm1, cat, label, alt);
    if (!res.success) throw new Error(`${key} ${cat}: ${res.error}`);
    await sleep(120);
  }
}

async function main() {
  const { browser, frm1 } = await getFrame();
  console.log('start', await scan(frm1));
  for (const key of ['Response A', 'Response B']) {
    await fillResponse(frm1, key, ratings.responses[key]);
    console.log(`after ${key}`, await scan(frm1));
  }
  await browser.disconnect();
}

main().catch((e) => { console.error(e); process.exit(1); });
