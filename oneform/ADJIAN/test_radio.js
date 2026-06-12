const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.connectOverCDP(process.env.CDP_ENDPOINT);
  const pages = browser.contexts()[0]?.pages() || [];
  const page = pages.find(p => p.url().includes('tryrating.com')) || pages[0];
  if (!page) { console.log('No page'); process.exit(1); }

  // Try clicking the Bad radio using Playwright locator
  const radios = await page.locator('input[type="radio"]').all();
  console.log('Found', radios.length, 'radios');
  for (const r of radios) {
    const info = await r.evaluate(el => ({
      ariaLabel: el.getAttribute('aria-label'),
      value: el.value,
      name: el.name,
      parentText: el.parentElement?.textContent?.trim(),
      grandparentText: el.parentElement?.parentElement?.textContent?.trim(),
    }));
    console.log('Radio info:', JSON.stringify(info));
    if (info.ariaLabel === 'Bad' || info.value === 'Bad' || info.grandparentText === 'Bad') {
      await r.click({ force: true });
      console.log('Clicked Bad radio via Playwright .click()');
      break;
    }
  }
  await page.waitForTimeout(500);

  // Verify radio state
  const checked = await page.evaluate(() => {
    const radios = document.querySelectorAll('input[type="radio"]');
    const states = [];
    radios.forEach(r => states.push({ checked: r.checked, label: r.parentElement.textContent.trim() }));
    return states;
  });
  console.log('After click:', JSON.stringify(checked, null, 2));

  await browser.close().catch(() => {});
  process.exit(0);
})().catch(e => { console.error(e.message); process.exit(1); });
