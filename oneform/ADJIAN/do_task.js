const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const pages = browser.contexts()[0]?.pages() || [];
  
  const page = pages.find(p => p.url().includes('tryrating.com')) || pages[0];
  if (!page) {
    console.log('No TryRating page found');
    return;
  }

  const url = page.url();
  console.log('URL:', url);

  const bodyText = await page.evaluate(() => {
    const el = document.querySelector('.task-item, .question, [class*="question"], [class*="task"]');
    return el ? el.innerText : document.body.innerText;
  });

  console.log('\n=== Page Content ===');
  console.log(bodyText.substring(0, 5000));

  // NEVER close browser or navigate away from task page
  // browser.disconnect() is not available on connectOverCDP - just exit
}

main().catch(console.error);
