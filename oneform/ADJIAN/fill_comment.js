const { chromium } = require('playwright');

const COMMENT = process.argv[2] || '';

if (!COMMENT) {
  console.error('Usage: node fill_comment.js "<comment>"');
  process.exit(1);
}

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const pages = browser.contexts()[0]?.pages() || [];
  const page = pages.find(p => p.url().includes('tryrating.com')) || pages[0];

  if (!page) {
    console.log('No TryRating page found');
    return;
  }

  console.log('Filling comment:', COMMENT);

  // Focus and fill textarea using native setter
  const filled = await page.evaluate((comment) => {
    const textarea = document.querySelector('textarea');
    if (!textarea) return 'NO_TEXTAREA';

    textarea.focus();
    const nativeSetter = Object.getOwnPropertyDescriptor(
      window.HTMLTextAreaElement.prototype, 'value'
    ).set;
    nativeSetter.call(textarea, comment);
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    textarea.dispatchEvent(new Event('change', { bubbles: true }));

    return textarea.value;
  }, COMMENT);

  console.log('Textarea value after fill:', filled);
  console.log('Match:', filled === COMMENT ? 'YES' : 'NO - LENGTH MISMATCH');
}

main().catch(console.error);
