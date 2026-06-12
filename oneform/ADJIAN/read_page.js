const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP(process.env.CDP_ENDPOINT);
  const pages = browser.contexts()[0]?.pages() || [];
  const page = pages.find(p => p.url().includes('tryrating.com')) || pages[0];
  if (!page) { console.log('No page'); process.exit(1); }

  // Dismiss any error dialog first
  await page.evaluate(() => {
    const btns = document.querySelectorAll('button');
    for (const b of btns) { if (b.innerText.trim() === 'OK') { b.click(); break; } }
  });
  await page.waitForTimeout(300);

  const info = await page.evaluate(() => {
    const text = document.body.innerText;
    const tid = text.match(/Task ID\s*\n?\s*(\S+)/);
    const kw = text.match(/KEYWORD\s*\n+([\s\S]+?)\n\n/);
    const ex = text.match(/EXPANSION\s*\n+([\s\S]+?)\n\n/);
    const ta = document.querySelector('textarea');
    const radios = document.querySelectorAll('input[type="radio"]');
    const radioStates = [];
    radios.forEach(r => radioStates.push({ value: r.value, checked: r.checked }));
    return {
      taskId: tid ? tid[1] : null,
      keyword: kw ? kw[1].replace(/\s+/g, ' ').trim() : null,
      expansion: ex ? ex[1].replace(/\s+/g, ' ').trim() : null,
      comment: ta ? ta.value : null,
      radios: radioStates,
      hasValidationError: text.includes('Validation failed'),
    };
  });
  console.log(JSON.stringify(info, null, 2));
  await browser.close().catch(() => {});
  process.exit(0);
})().catch(e => { console.error(e.message); process.exit(1); });
