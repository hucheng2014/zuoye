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

  console.log('Found frame:', frm.url());

  const info = await frm.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll('[role="tab"], button')).map(t => ({
      text: t.textContent.trim(),
      role: t.getAttribute('role'),
      selected: t.getAttribute('aria-selected') === 'true' || t.classList.contains('active')
    })).filter(t => t.text.length > 0);

    const radiogroups = Array.from(document.querySelectorAll('.radio-buttons, [role="radiogroup"]')).map(rg => {
      const legendText = rg.querySelector('.legend, legend')?.textContent.trim() || 'No legend';
      const labels = Array.from(rg.querySelectorAll('label')).map(l => {
        const radio = l.querySelector('input[type="radio"]') || document.getElementById(l.getAttribute('for'));
        return {
          labelText: l.textContent.trim(),
          checked: radio ? radio.checked : false
        };
      });
      return { legendText, labels };
    });

    const textareas = Array.from(document.querySelectorAll('textarea')).map(ta => ({
      placeholder: ta.placeholder,
      value: ta.value,
      visible: ta.offsetParent !== null
    }));

    return { tabs, radiogroups, textareas };
  });

  console.log('\n=== TABS ===');
  console.log(info.tabs);

  console.log('\n=== RADIOGROUPS & VALS ===');
  info.radiogroups.forEach((rg, idx) => {
    console.log(`\nRadioGroup ${idx + 1}: ${rg.legendText}`);
    rg.labels.forEach(l => {
      console.log(`  [${l.checked ? 'X' : ' '}] ${l.labelText}`);
    });
  });

  console.log('\n=== TEXTAREAS ===');
  console.log(info.textareas);

  await browser.disconnect();
}

main().catch(console.error);
