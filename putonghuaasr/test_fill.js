const { chromium } = require('playwright');

async function run() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9237');
  const page = browser.contexts()[0].pages()[0];

  const testText = "测试填充文本\n1. 人声: 无\n2. 环境与音效: 无\n3. 背景音乐: 无\n4. 特殊合成音效: 无";

  console.log('Attempting to fill using page.locator("textarea").first().fill(...)');
  try {
    await page.locator('textarea').first().fill(testText);
    await page.waitForTimeout(1000);
    const val = await page.locator('textarea').first().inputValue();
    console.log('Value after fill:', val);
  } catch (err) {
    console.error('Fill failed:', err);
  }

  await browser.close();
}

run().catch(console.error);
