const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const pages = browser.contexts()[0]?.pages() || [];
  const page = pages.find(p => p.url().includes('tryrating.com')) || pages[0];
  if (!page) { console.log('No page'); return; }

  // Dismiss error - click body, try to close any error messages
  await page.evaluate(() => {
    document.body.click();
    // Try clicking any error close buttons
    const all = document.querySelectorAll('[class*="close"], [class*="dismiss"], [class*="error"], .modal button');
    all.forEach(el => el.click());
  });
  await page.waitForTimeout(300);
  
  // Check page state
  const state = await page.evaluate(() => {
    const text = document.body.innerText;
    return {
      hasError: text.includes('Validation failed') || text.includes('required'),
      hasTaskId: text.includes('Task ID'),
      snippet: text.substring(0, 300)
    };
  });
  console.log(JSON.stringify(state, null, 2));
})();
