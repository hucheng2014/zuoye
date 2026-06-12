const { chromium } = require('playwright');

(async () => {
  const context = await chromium.launchPersistentContext(
    '/Users/xaa/zuoye/oneform/ADJIAN/.browser_profile',
    {
      headless: false,
      args: ['--no-first-run', '--remote-debugging-port=9222'],
    }
  );

  const page = context.pages()[0] || await context.newPage();
  await page.goto('https://tryrating.com');

  console.log('Browser opened. Press Ctrl+C to close.');
})();
