const puppeteer = require('puppeteer-core');

const { CDP_URL, CDP_FALLBACK } = require('./config');

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log('Connecting to browser via CDP...');
  let browser;
  for (const url of [CDP_URL, CDP_FALLBACK]) {
    try {
      browser = await puppeteer.connect({ browserURL: url, defaultViewport: null });
      break;
    } catch (e) {
      if (url === CDP_FALLBACK) throw e;
    }
  }

  const pages = await browser.pages();
  const page = pages[0];

  const frames = page.frames();
  const frm1 = frames.find(f => f.url().includes('task-editor'));

  if (!frm1) {
    console.error('Task editor frame not found');
    await browser.disconnect();
    return;
  }

  // Click Response A
  console.log('Clicking Response A tab...');
  await frm1.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll('[role="tab"], button'));
    const tab = tabs.find(t => t.textContent.includes('Response A'));
    if (tab) tab.click();
  });
  await sleep(1000);

  // Get radio buttons details in Response A
  const radios = await frm1.evaluate(() => {
    const radioInputs = Array.from(document.querySelectorAll('input[type="radio"]'));
    return radioInputs.map(r => {
      const container = r.closest('.radio-buttons, [role="radiogroup"]');
      const legend = container ? (container.querySelector('.legend') || container) : null;
      const label = r.closest('label');
      return {
        name: r.name,
        value: r.value,
        labelText: label ? label.textContent.trim() : '',
        legendText: legend ? legend.textContent.trim() : '',
        visible: r.offsetParent !== null
      };
    });
  });

  console.log('All radio buttons in current view (Response A):');
  console.log(JSON.stringify(radios.filter(r => r.visible), null, 2));

  await browser.disconnect();
}

main().catch(console.error);
