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
  const frm1 = frames.find(f => f.name() === 'frm1');

  if (!frm1) {
    console.error('frm1 not found');
    await browser.disconnect();
    return;
  }

  const elements = await frm1.evaluate(() => {
    // Helper to get element details
    const radios = Array.from(document.querySelectorAll('input[type="radio"]')).map(r => ({
      name: r.name,
      value: r.value,
      labelText: r.closest('label')?.textContent.trim() || '',
      checked: r.checked,
      legendText: r.closest('.radio-buttons, [role="radiogroup"]')?.querySelector('.legend')?.textContent.trim() || ''
    }));

    const textareas = Array.from(document.querySelectorAll('textarea')).map(t => ({
      id: t.id,
      name: t.name,
      placeholder: t.placeholder,
      value: t.value,
      labelText: t.closest('.form-item, .field-wrapper')?.querySelector('.label, label')?.textContent.trim() || ''
    }));

    const buttons = Array.from(document.querySelectorAll('button')).map(b => ({
      id: b.id,
      class: b.className,
      text: b.textContent.trim(),
      visible: b.offsetParent !== null
    }));

    return { radios, textareas, buttons };
  });

  console.log('=== ELEMENTS INSIDE FRM1 ===');
  console.log('\nTextareas:');
  console.log(JSON.stringify(elements.textareas, null, 2));
  console.log('\nVisible Buttons:');
  console.log(JSON.stringify(elements.buttons.filter(b => b.visible), null, 2));

  await browser.disconnect();
}

main().catch(console.error);
