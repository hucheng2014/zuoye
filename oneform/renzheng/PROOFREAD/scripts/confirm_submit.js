require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  
  // The confirmation dialog is on main page with Cancel/Submit buttons
  // Find the "Submit" button (not Cancel) that's visible
  const allBtns = await page.evaluate(() => {
    return [...document.querySelectorAll('button')].filter(b => b.offsetWidth > 0).map(b => ({
      text: b.innerText?.trim(),
      ariaLabel: b.getAttribute('aria-label'),
      id: b.id
    }));
  });
  console.log('All visible buttons:', JSON.stringify(allBtns));
  
  // Click the "Submit" button in the confirmation dialog
  // The dialog has "Cancel" and "Submit" - we want "Submit"
  const submitInDialog = await page.locator('button', { hasText: 'Submit' }).filter({ visible: true }).last();
  if (submitInDialog) {
    console.log('Clicking Submit in confirmation dialog...');
    await submitInDialog.click({ force: true });
    await page.waitForTimeout(3000);
  }
  
  // Check the state after
  const newState = await page.evaluate(() => {
    const dialogs = document.querySelectorAll('[role="dialog"]');
    const dlgInfo = [...dialogs].map(d => ({text: d.innerText?.slice(0, 200), visible: d.offsetWidth > 0}));
    const visibleBtns = [...document.querySelectorAll('button')].filter(b => b.offsetWidth > 0).map(b => b.innerText?.trim());
    return { dialogs: dlgInfo, buttons: visibleBtns };
  });
  console.log('State after submit:', JSON.stringify(newState, null, 2));
  
  await browser.close();
})().catch(e => console.error(e));
