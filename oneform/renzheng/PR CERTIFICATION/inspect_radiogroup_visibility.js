const puppeteer = require('puppeteer-core');

const CDP_URL = 'http://127.0.0.1:9235';

async function main() {
  const browser = await puppeteer.connect({
    browserURL: CDP_URL,
    defaultViewport: null
  });

  const pages = await browser.pages();
  const page = pages[0];
  const frames = page.frames();
  const frm = frames.find(f => f.url().includes('task-editor'));

  if (!frm) {
    console.error('Task editor frame not found');
    await browser.disconnect();
    return;
  }

  const info = await frm.evaluate(() => {
    const rgs = Array.from(document.querySelectorAll('.radio-buttons, [role="radiogroup"]')).map((rg, idx) => {
      const style = window.getComputedStyle(rg);
      const rect = rg.getBoundingClientRect();
      const legend = rg.querySelector('.legend, legend')?.textContent.trim() || '';
      return {
        index: idx + 1,
        legend: legend,
        display: style.display,
        visibility: style.visibility,
        offsetHeight: rg.offsetHeight,
        offsetWidth: rg.offsetWidth,
        rect: {
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height
        }
      };
    });
    return rgs;
  });

  console.log('Visibility of all radiogroups:');
  console.log(JSON.stringify(info, null, 2));

  await browser.disconnect();
}

main().catch(console.error);
