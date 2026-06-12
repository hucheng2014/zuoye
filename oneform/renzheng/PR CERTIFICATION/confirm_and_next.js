const puppeteer = require('puppeteer-core');
const { CDP_URL } = require('./config');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function clickConfirm(ctx, name) {
  return ctx.evaluate(() => {
    const all = Array.from(document.querySelectorAll('button, [role="button"]'));
    for (const b of all) {
      const t = b.textContent.trim();
      const vis = b.offsetParent !== null;
      if (!vis) continue;
      if (t === 'Submit' || t === 'Yes' || t === 'Confirm' || t === 'OK') {
        const parent = b.closest('div,section,dialog')?.textContent || '';
        if (parent.includes('submit') || parent.includes('Submit') || parent.includes('sure')) {
          b.click();
          return { ok: true, label: t, parent: parent.substring(0, 80) };
        }
      }
    }
    const modal = all.find((b) => b.textContent.trim() === 'Submit' && b.offsetParent);
    if (modal) {
      modal.click();
      return { ok: true, label: 'Submit-fallback' };
    }
    return { ok: false };
  }).then((r) => ({ ...r, where: name }));
}

(async () => {
  const browser = await puppeteer.connect({ browserURL: CDP_URL, defaultViewport: null });
  const page = (await browser.pages()).find((p) => p.url().includes('starshot'));
  const frm = page.frames().find((f) => f.url().includes('task-editor'));

  // Click main Submit if present
  const pre = await frm.evaluate(() => {
    const btn = [...document.querySelectorAll('button')].find((b) => b.textContent.trim() === 'Submit' && b.offsetParent);
    if (btn) { btn.click(); return true; }
    return false;
  });
  console.log('Clicked frame Submit:', pre);
  await sleep(2000);

  for (let i = 0; i < 8; i++) {
    const r1 = await clickConfirm(page, 'page');
    const r2 = await clickConfirm(frm, 'frame');
    console.log(`poll ${i}:`, r1, r2);
    if (r1.ok || r2.ok) break;
    await sleep(1000);
  }
  await sleep(3000);

  const next = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button,a,[role=button]')].find((x) => /next task/i.test(x.textContent) && x.offsetParent);
    if (b) { b.click(); return b.textContent.trim(); }
    return null;
  });
  console.log('Next task:', next);
  await sleep(3000);
  const timer = await page.evaluate(() => document.body.innerText.match(/\d+s/)?.[0]);
  console.log('Timer after:', timer);
  await browser.disconnect();
})();
