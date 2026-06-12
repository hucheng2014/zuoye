const puppeteer = require('puppeteer-core');

const CDP_URL = 'http://127.0.0.1:9235';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  const browser = await puppeteer.connect({
    browserURL: CDP_URL,
    defaultViewport: null
  });

  const pages = await browser.pages();
  const page = pages[0];
  const frames = page.frames();
  const frm1 = frames.find(f => f.url().includes('task-editor'));

  if (!frm1) {
    console.error('Task editor frame not found');
    await browser.disconnect();
    return;
  }

  const compKeys = ['B and A', 'C and A', 'C and B'];
  const testRatings = {
    'B and A': 'Right Much Better',
    'C and A': 'Right Much Better',
    'C and B': 'Left Better'
  };

  for (const compKey of compKeys) {
    const val = testRatings[compKey];
    console.log(`\n--- Testing click for tab: ${compKey} ---`);
    
    // Click tab
    const clickTabResult = await frm1.evaluate((text) => {
      const tabs = Array.from(document.querySelectorAll('[role="tab"], button'));
      const tab = tabs.find(t => t.textContent.trim().toLowerCase() === text.trim().toLowerCase() || t.textContent.includes(text));
      if (tab) {
        tab.click();
        return { success: true, text: tab.textContent.trim(), classList: Array.from(tab.classList) };
      }
      return { success: false };
    }, compKey);
    console.log('Tab click result:', clickTabResult);

    await sleep(1000);

    // Verify which radiogroups are visible
    const visibleGroups = await frm1.evaluate(() => {
      const groups = Array.from(document.querySelectorAll('.radio-buttons, [role="radiogroup"]')).map((g, idx) => {
        const style = window.getComputedStyle(g);
        return {
          index: idx + 1,
          legend: g.querySelector('.legend, legend')?.textContent.trim() || '',
          offsetHeight: g.offsetHeight,
          visible: style.display !== 'none' && style.visibility !== 'hidden' && g.offsetHeight > 0
        };
      });
      return groups.filter(g => g.visible);
    });
    console.log('Visible radiogroups after tab click:', visibleGroups);

    // Click the radio button
    const clickRadioResult = await frm1.evaluate((cat, target) => {
      const groups = Array.from(document.querySelectorAll('.radio-buttons, [role="radiogroup"]')).filter(g => {
        const style = window.getComputedStyle(g);
        return style.display !== 'none' && style.visibility !== 'hidden' && g.offsetHeight > 0;
      });

      for (const group of groups) {
        const legend = group.querySelector('.legend')?.textContent || '';
        let matchesCategory = false;
        if (legend.toLowerCase().includes('compare responses')) matchesCategory = true;

        if (matchesCategory) {
          const labels = Array.from(group.querySelectorAll('label'));
          for (const label of labels) {
            const text = label.textContent.trim().toLowerCase();
            const targetStr = target.trim().toLowerCase();
            if (text === targetStr) {
              const radio = label.querySelector('input[type="radio"]') || document.getElementById(label.getAttribute('for'));
              if (radio) {
                radio.click();
                return { success: true, legend: legend, clickedLabel: label.textContent.trim(), checked: radio.checked };
              }
            }
          }
        }
      }
      return { success: false };
    }, 'Comparison', val);
    console.log('Radio click result:', clickRadioResult);
  }

  // Final check of what is checked in comparison radiogroups
  const finalState = await frm1.evaluate(() => {
    const rgs = Array.from(document.querySelectorAll('.radio-buttons, [role="radiogroup"]')).slice(12, 15); // RadioGroups 13, 14, 15
    return rgs.map((rg, idx) => {
      const legend = rg.querySelector('.legend, legend')?.textContent.trim() || '';
      const checkedOption = Array.from(rg.querySelectorAll('label')).find(l => {
        const radio = l.querySelector('input[type="radio"]') || document.getElementById(l.getAttribute('for'));
        return radio ? radio.checked : false;
      })?.textContent.trim() || 'None';
      return {
        tabIndex: idx + 13,
        legend,
        checkedOption
      };
    });
  });
  console.log('\n=== FINAL STATE OF COMPARISON RADIOS ===');
  console.log(finalState);

  await browser.disconnect();
}

main().catch(console.error);
