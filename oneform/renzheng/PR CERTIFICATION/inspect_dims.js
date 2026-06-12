const puppeteer = require('puppeteer-core');
const { CDP_URL } = require('./config');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const b = await puppeteer.connect({ browserURL: CDP_URL, defaultViewport: null });
  const frm = (await b.pages()).find((p) => p.url().includes('starshot')).frames().find((f) => f.url().includes('task-editor'));
  for (const tab of ['Response A', 'Response B', 'Response C']) {
    await frm.evaluate((t) => {
      [...document.querySelectorAll('[role=tab],button')].find((x) => x.textContent.includes(t))?.click();
    }, tab);
    await sleep(500);
    const groups = await frm.evaluate(() =>
      [...document.querySelectorAll('.radio-buttons,[role=radiogroup]')]
        .filter((g) => g.offsetHeight > 0)
        .map((g) => ({
          legend: (g.querySelector('.legend') || g).textContent.trim().substring(0, 100),
          labels: [...g.querySelectorAll('label')].map((l) => l.textContent.trim()),
        }))
    );
    console.log('===', tab, '===');
    console.log(JSON.stringify(groups, null, 2));
  }
  await b.disconnect();
})();
