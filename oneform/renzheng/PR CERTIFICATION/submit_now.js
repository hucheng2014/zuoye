/** Emergency submit current task — fill, verify, submit, confirm, next */
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');
const { CDP_URL } = require('./config');
const { fillRatings, finalizeSubmit, sleep } = require('./pr_automation_helper');

const { assertRatingsReady, extractTaskFromPuppeteerFrame, validateRatingsForTask } = require('./task_utils');
const { ratings } = assertRatingsReady();
const RATINGS = ratings;

async function getFrame() {
  const browser = await puppeteer.connect({ browserURL: CDP_URL, defaultViewport: null });
  const page = (await browser.pages()).find((p) => p.url().includes('starshot'));
  const frm1 = page.frames().find((f) => f.url().includes('task-editor'));
  return { browser, page, frm1 };
}

(async () => {
  const { browser, page, frm1 } = await getFrame();
  if (!frm1) throw new Error('no frame');

  const liveTask = await extractTaskFromPuppeteerFrame(frm1, 400);
  const liveCheck = validateRatingsForTask(liveTask, RATINGS);
  if (!liveCheck.ok) throw new Error(`STALE GUARD: ${liveCheck.issues.join('; ')}`);

  await fillRatings(frm1, RATINGS);

  const check = await frm1.evaluate(() => {
    const ta = [...document.querySelectorAll('textarea')].find((t) => {
      const b = t.closest('div')?.parentElement?.textContent || '';
      return b.includes('reasons for your gradings');
    });
    const btn = [...document.querySelectorAll('button')].find((b) => /submit|invalid/i.test(b.textContent));
    return { rationaleLen: ta?.value?.length || 0, submit: btn?.textContent?.trim() };
  });
  console.log('Pre-submit check:', check);
  if (check.rationaleLen < 50) throw new Error('rationale still empty');

  const result = await finalizeSubmit(browser, page, frm1);
  console.log('Result:', result);
  await browser.disconnect();
})().catch((e) => {
  console.error('FAILED:', e.message);
  process.exit(1);
});
