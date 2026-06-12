const { chromium } = require('playwright');

async function run() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9237');
  const page = browser.contexts()[0].pages()[0];
  
  const info = await page.evaluate(() => {
    const tas = Array.from(document.querySelectorAll('textarea'));
    return tas.map((ta, i) => ({
      index: i,
      className: ta.className,
      id: ta.id,
      value: ta.value,
      placeholder: ta.placeholder,
      visible: ta.offsetWidth > 0 && ta.offsetHeight > 0
    }));
  });
  console.log('Textareas on page:', info);
  await browser.close();
}

run().catch(console.error);
