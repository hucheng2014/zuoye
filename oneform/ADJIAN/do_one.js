const { chromium } = require('playwright');

const RATING = process.argv[2];
const COMMENT = process.argv[3];

if (!RATING || !COMMENT) {
  console.error('Usage: node do_one.js <Good|Acceptable|Bad> "<comment>"');
  process.exit(1);
}

if (!['Good', 'Acceptable', 'Bad'].includes(RATING)) {
  console.error('Rating must be exactly: Good, Acceptable, or Bad');
  process.exit(1);
}

(async () => {
  // Connect to browser via WebSocket
  // CDP_ENDPOINT must be a ws:// URL pointing to the browser container
  const wsUrl = process.env.CDP_ENDPOINT;
  if (!wsUrl) {
    console.error('ERROR: CDP_ENDPOINT environment variable not set.');
    console.error('Get it with: docker exec oneform-browser python3 -c "import urllib.request,json; r=urllib.request.urlopen(\'http://localhost:9222/json/version\'); d=json.loads(r.read()); print(d[\'webSocketDebuggerUrl\'])"');
    console.error('Then replace ws://localhost:9222 with ws://browser:9223');
    process.exit(1);
  }

  const browser = await chromium.connectOverCDP(wsUrl);

  try {
    const pages = browser.contexts()[0]?.pages() || [];
    const page = pages.find(p => p.url().includes('tryrating.com')) || pages[0];
    if (!page) {
      console.log('ERROR: No TryRating page found');
      process.exit(1);
    }

    // Dismiss any lingering error dialogs
    await page.evaluate(() => {
      const btns = document.querySelectorAll('button');
      for (const b of btns) {
        if (b.innerText.trim() === 'OK') { b.click(); break; }
      }
    });
    await page.waitForTimeout(300);

    // Read current task info
    const taskInfo = await page.evaluate(() => {
      const text = document.body.innerText;
      const tid = text.match(/Task ID\s*\n?\s*(\S+)/);
      const kw = text.match(/KEYWORD\s*\n+([\s\S]+?)\n\n/);
      const ex = text.match(/EXPANSION\s*\n+([\s\S]+?)\n\n/);
      return {
        taskId: tid ? tid[1] : 'unknown',
        keyword: kw ? kw[1].replace(/\s+/g, ' ').trim() : null,
        expansion: ex ? ex[1].replace(/\s+/g, ' ').trim() : null,
      };
    });
    console.log('Task:', taskInfo.taskId);
    console.log('KEYWORD:', taskInfo.keyword);
    console.log('EXPANSION:', taskInfo.expansion);

    // Step 1: Fill comment using Playwright locator
    const ta = page.locator('textarea').first();
    await ta.click();
    await ta.fill('');
    await ta.fill(COMMENT);
    await page.waitForTimeout(300);

    const actualComment = await ta.inputValue();
    if (actualComment !== COMMENT) {
      console.log('WARNING: Comment mismatch. Got:', actualComment.substring(0, 50));
    } else {
      console.log('Comment filled OK');
    }

    // Step 2: Select rating by clicking the radio input directly via Playwright
    // IMPORTANT: Must use Playwright .click({force:true}), not JS evaluate click,
    // because React state won't update with a plain JS click on these elements.
    const radios = await page.locator('input[type="radio"]').all();
    let ratingSelected = false;
    for (const r of radios) {
      const value = await r.evaluate(el => el.value);
      if (value === RATING) {
        await r.click({ force: true });
        ratingSelected = true;
        break;
      }
    }
    if (!ratingSelected) {
      console.error('ERROR: Could not find radio for rating:', RATING);
      process.exit(1);
    }
    await page.waitForTimeout(300);

    // Verify radio is checked
    const isChecked = await page.evaluate((rating) => {
      const radios = document.querySelectorAll('input[type="radio"]');
      for (const r of radios) {
        if (r.value === rating) return r.checked;
      }
      return false;
    }, RATING);
    if (!isChecked) {
      console.error('ERROR: Radio not checked after click!');
      process.exit(1);
    }
    console.log('Rating selected:', RATING);

    // Step 3: Submit
    await page.evaluate(() => {
      const btns = document.querySelectorAll('button');
      for (const b of btns) {
        if (b.innerText.includes('Submit')) { b.click(); break; }
      }
    });
    console.log('Submitted, waiting...');

    // Wait for response
    await page.waitForTimeout(4000);

    // Check for validation error
    const hasError = await page.evaluate(() => {
      return document.body.innerText.includes('Validation failed');
    });
    if (hasError) {
      console.error('ERROR: Validation failed! Dismissing...');
      await page.evaluate(() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) { if (b.innerText.trim() === 'OK') { b.click(); break; } }
      });
      process.exit(1);
    }

    // Wait 22-55 seconds (random) before reading next question
    const waitSec = Math.floor(Math.random() * (55 - 22 + 1)) + 22;
    console.log(`\nWaiting ${waitSec}s before next question...`);
    await page.waitForTimeout(waitSec * 1000);

    // Read next question
    const nextInfo = await page.evaluate(() => {
      const text = document.body.innerText;
      const tid = text.match(/Task ID\s*\n?\s*(\S+)/);
      const kw = text.match(/KEYWORD\s*\n+([\s\S]+?)\n\n/);
      const ex = text.match(/EXPANSION\s*\n+([\s\S]+?)\n\n/);
      return {
        taskId: tid ? tid[1] : null,
        keyword: kw ? kw[1].replace(/\s+/g, ' ').trim() : null,
        expansion: ex ? ex[1].replace(/\s+/g, ' ').trim() : null,
      };
    });
    console.log('=== NEXT ===');
    console.log(JSON.stringify(nextInfo, null, 2));

  } finally {
    await browser.close().catch(() => {});
    process.exit(0);
  }
})().catch(e => {
  console.error('FATAL:', e.message);
  process.exit(1);
});
