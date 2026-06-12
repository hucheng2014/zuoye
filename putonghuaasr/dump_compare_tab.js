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

  // Click Compare Tab
  console.log('Clicking "对比" tab...');
  await page.locator('div:text("对比")').first().click();
  await page.waitForTimeout(1000);

  // Let's dump all text from elements that look like column headers or blocks
  const headers = await page.$$eval('div', els => {
    // Find divs that contain version names (like 原始版本, 修改版本, or others)
    return els
      .map(el => el.innerText?.trim())
      .filter(text => text && (text.includes('版本') || text.includes('模型') || text.includes('原始') || text.includes('修改')))
      .map(text => text.substring(0, 100)); // limit length
  });
  console.log('Headers / Text containing "版本" or "模型":');
  console.log([...new Set(headers)]); // Unique values

  // Let's specifically find all column header divs or spans under the tab content
  // Looking at the screenshot, we have "原始版本" and "修改版本" headers. Let's find their siblings or parents
  const columnsInfo = await page.evaluate(() => {
    // Find all text elements under the active tab pane
    const pane = document.querySelector('.ant-tabs-tabpane-active') || document.querySelector('.ant-tabs-content');
    if (!pane) return 'No active tab pane found';
    
    // Let's print the structural text
    const cols = [];
    // Traverse elements
    const walker = document.createTreeWalker(pane, NodeFilter.SHOW_ELEMENT);
    let node = walker.nextNode();
    while (node) {
      if (node.children.length === 0 && node.textContent.trim()) {
        cols.push({
          tag: node.tagName,
          class: node.className,
          text: node.textContent.trim()
        });
      }
      node = walker.nextNode();
    }
    return cols;
  });

  console.log('\n--- Active Tab Pane text elements ---');
  console.log(JSON.stringify(columnsInfo, null, 2));
  console.log('-------------------------------------');

  await browser.close();
}

run().catch(console.error);
