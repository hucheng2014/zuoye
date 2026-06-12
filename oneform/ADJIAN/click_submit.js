const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const pages = browser.contexts()[0]?.pages() || [];
  const page = pages.find(p => p.url().includes('tryrating.com')) || pages[0];

  if (!page) {
    console.log('No TryRating page found');
    return;
  }

  // Select rating
  const rating = process.argv[2] || 'Bad';
  console.log('Selecting rating:', rating);
  await page.evaluate((r) => {
    const labels = document.querySelectorAll('label');
    for (const label of labels) {
      if (label.innerText.trim() === r) {
        label.click();
        console.log('Clicked label:', r);
        break;
      }
    }
    // Also try clicking radio inputs
    const inputs = document.querySelectorAll('input[type="radio"]');
    for (const input of inputs) {
      const parentLabel = input.closest('label');
      if (parentLabel && parentLabel.innerText.trim() === r) {
        input.click();
        break;
      }
    }
  }, rating);

  // Wait before clicking submit
  await page.waitForTimeout(800);

  // Verify comment is filled
  const commentValue = await page.evaluate(() => {
    const textarea = document.querySelector('textarea');
    return textarea ? textarea.value : 'NO_TEXTAREA';
  });
  console.log('Comment in textarea:', commentValue);

  if (commentValue === 'NO_TEXTAREA' || commentValue.length < 2) {
    console.log('WARNING: Comment not filled! Fill comment first.');
    return;
  }

  // Click submit
  console.log('Clicking Submit...');
  await page.evaluate(() => {
    const buttons = document.querySelectorAll('button, input[type="submit"]');
    for (const btn of buttons) {
      if (btn.innerText?.includes('Submit') || btn.value?.includes('Submit')) {
        btn.click();
        break;
      }
    }
  });

  // Wait for next question
  await page.waitForTimeout(4000);

  // Read new page
  const bodyText = await page.evaluate(() => document.body.innerText);
  console.log('\n=== After Submit ===');
  console.log(bodyText.substring(0, 2000));
}

main().catch(console.error);
