const { chromium } = require('playwright');

const RATING = process.argv[2] || 'Bad';
const COMMENT = process.argv[3] || '';

if (!COMMENT) {
  console.error('Usage: node submit_rating.js <Good|Acceptable|Bad> "<comment>"');
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

  console.log('Submitting rating:', RATING);
  console.log('Comment:', COMMENT);

  // Select rating
  await page.evaluate((rating) => {
    const labels = document.querySelectorAll('label');
    for (const label of labels) {
      if (label.innerText.trim() === rating) {
        label.click();
        break;
      }
    }
  }, RATING);

  // Fill comment using native setter to sync React/Vue state
  await page.evaluate((comment) => {
    const textarea = document.querySelector('textarea');
    if (!textarea) {
      console.error('Textarea not found');
      return;
    }
    // Use native setter to trigger framework's onChange
    const nativeSetter = Object.getOwnPropertyDescriptor(
      window.HTMLTextAreaElement.prototype, 'value'
    ).set;
    nativeSetter.call(textarea, comment);
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    textarea.dispatchEvent(new Event('change', { bubbles: true }));
    // Also try React's synthetic event
    textarea.dispatchEvent(new Event('compositionend', { bubbles: true }));
  }, COMMENT);

  // Small delay before submit
  await page.waitForTimeout(500);

  // Click submit
  await page.evaluate(() => {
    const buttons = document.querySelectorAll('button');
    for (const btn of buttons) {
      if (btn.innerText.includes('Submit')) {
        btn.click();
        break;
      }
    }
  });

  // Wait for next question to load
  await page.waitForTimeout(3000);

  // Read new question
  const bodyText = await page.evaluate(() => {
    const el = document.querySelector('.task-item, .question, [class*="question"], [class*="task"]');
    return el ? el.innerText : document.body.innerText;
  });

  console.log('\n=== New Page Content ===');
  console.log(bodyText.substring(0, 3000));

  // NEVER close browser
}

main().catch(console.error);
