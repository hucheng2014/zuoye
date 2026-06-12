const { chromium } = require('playwright');

async function run() {
  console.log('Connecting to browser on http://127.0.0.1:9237...');
  let browser;
  try {
    browser = await chromium.connectOverCDP('http://127.0.0.1:9237');
  } catch (err) {
    console.error('Failed to connect:', err);
    process.exit(1);
  }

  const contexts = browser.contexts();
  const page = contexts[0].pages()[0];
  console.log(`Connected. Page URL: ${page.url()}`);
  console.log(`Page Title: ${await page.title()}`);

  // Dump some interesting element text content
  const editTab = await page.textContent('div:has-text("编辑")').catch(() => null);
  const compareTab = await page.textContent('div:has-text("对比")').catch(() => null);
  console.log(`Edit Tab present: ${!!editTab}`);
  console.log(`Compare Tab present: ${!!compareTab}`);

  // Let's click the Compare tab and take a screenshot of it to see what's in there!
  try {
    const compareTabEl = await page.locator('div:text("对比")').first();
    if (await compareTabEl.count() > 0) {
      console.log('Clicking "对比" tab...');
      await compareTabEl.click();
      await page.waitForTimeout(1000);
      const imgPath = '/Users/xaa/.gemini/antigravity-cli/brain/6ffe4535-d43d-47de-bd8b-27434df1d17f/scratch/compare_tab_clicked.png';
      await page.screenshot({ path: imgPath });
      console.log(`Saved screenshot to ${imgPath}`);

      // Dump all text on the right side panel
      const panelText = await page.locator('.ant-tabs-content-holder').first().innerText().catch(() => '');
      console.log('--- Panel text after clicking Compare ---');
      console.log(panelText);
      console.log('-----------------------------------------');

      // Switch back to "编辑"
      console.log('Switching back to "编辑" tab...');
      await page.locator('div:text("编辑")').first().click();
      await page.waitForTimeout(500);
    } else {
      console.log('Could not find "对比" tab by text.');
    }
  } catch (err) {
    console.error('Error in tab clicking:', err);
  }

  // Check language radios
  const radios = await page.$$eval('input[type="radio"]', els => {
    return els.map(el => ({
      value: el.value,
      checked: el.checked,
      labelText: el.closest('label')?.innerText || ''
    }));
  });
  console.log('Radio buttons:', radios);

  // Check textareas
  const textareas = await page.$$eval('textarea', els => {
    return els.map(el => ({
      placeholder: el.placeholder,
      value: el.value,
      id: el.id
    }));
  });
  console.log('Textareas:', textareas);

  await browser.close();
}

run().catch(console.error);
