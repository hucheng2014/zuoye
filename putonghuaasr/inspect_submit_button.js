const { chromium } = require('playwright');

async function run() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9237');
  const page = browser.contexts()[0].pages()[0];

  const buttonInfo = await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    return btns.map((btn, i) => ({
      index: i,
      text: btn.innerText.trim(),
      className: btn.className,
      id: btn.id,
      disabled: btn.disabled,
      visible: btn.offsetWidth > 0 && btn.offsetHeight > 0
    }));
  });

  console.log('Buttons on page:', buttonInfo);
  await browser.close();
}

run().catch(console.error);
