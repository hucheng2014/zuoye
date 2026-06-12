#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { getFrame, clickRadioByLabel } = require('./pr_automation_helper');
const { verifyFormSubmittableOn } = require('./verify_task');

const ratings = JSON.parse(fs.readFileSync(path.join(__dirname, 'current_ratings.json'), 'utf8'));

async function scanResponses(frm1) {
  return frm1.evaluate(() => {
    const respList = document.querySelectorAll('[role=tablist]')[0];
    const tabs = [...(respList?.querySelectorAll('[role=tab]') || [])].map((t) => ({
      text: t.textContent.trim(),
      selected: t.getAttribute('aria-selected') === 'true',
      controls: t.getAttribute('aria-controls'),
    }));
    const text = document.body.innerText;
    const respM = text.match(/RESPONSES\s*(\d+)\/(\d+)\s*Complete/i);
    const active = tabs.find((t) => t.selected);
    const panel = active?.controls ? document.getElementById(active.controls) : null;
    const groups = panel
      ? [...panel.querySelectorAll('.radio-buttons, [role="radiogroup"]')].map((g) => {
          const legend = g.querySelector('.legend, legend')?.textContent?.trim() || '';
          const checked = [...g.querySelectorAll('input[type=radio]')].find((r) => r.checked);
          return { legend, checked: checked?.value || null };
        })
      : [];
    return { respM: respM ? `${respM[1]}/${respM[2]}` : null, tabs, groups };
  });
}

async function main() {
  const { browser, page, frm1 } = await getFrame();
  if (!frm1) throw new Error('no frame');
  console.log('BEFORE', await scanResponses(frm1));

  const rData = ratings.responses['Response A'];
  await frm1.evaluate(() => {
    const respList = document.querySelectorAll('[role=tablist]')[0];
    const tab = [...(respList?.querySelectorAll('[role=tab]') || [])].find((t) => t.textContent.trim() === 'Response A');
    tab?.click();
  });
  await new Promise((r) => setTimeout(r, 800));
  console.log('AFTER tab A click', await scanResponses(frm1));
  for (const [cat, label] of [
    ['IF', rData.instructionFollowing],
    ['Localization', rData.localization],
    ['Concision', rData.concision],
    ['Description', rData.description],
    ['Truthfulness', rData.truthfulness],
    ['Satisfaction', rData.satisfaction],
  ]) {
    const res = await clickRadioByLabel(frm1, cat, label, { scope: 'active-tabpanel' });
    console.log(cat, label, res);
  }
  console.log('AFTER A fill', await scanResponses(frm1));

  await clickResponseTab(frm1, 'Response B');
  console.log('AFTER switch to B', await scanResponses(frm1));

  const v = await verifyFormSubmittableOn(page, frm1);
  console.log('verify', v);
  await browser.disconnect();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
