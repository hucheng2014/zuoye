const puppeteer = require('puppeteer-core');

const CDP_URL = 'http://127.0.0.1:9235';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log('Connecting to browser...');
  const browser = await puppeteer.connect({
    browserURL: CDP_URL,
    defaultViewport: null
  });

  const pages = await browser.pages();
  const page = pages[0];
  const frames = page.frames();
  // Find frame dynamically by URL
  const frm1 = frames.find(f => f.url().includes('task-editor'));

  if (!frm1) {
    console.error('Task editor frame not found');
    await browser.disconnect();
    return;
  }

  // Helper to find and click the modal Submit button
  const clickResult = await frm1.evaluate(() => {
    // Look for all buttons containing "Submit"
    const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
    console.log('Found buttons:', buttons.map(b => `${b.tagName}: "${b.textContent.trim()}"`));

    // We want the "Submit" button inside the modal dialog
    const modalContainers = Array.from(document.querySelectorAll('div, section, dialog')).filter(el => {
      return el.textContent.includes('Do you want to submit');
    });

    if (modalContainers.length > 0) {
      console.log('Found modal container!');
      const modal = modalContainers[modalContainers.length - 1]; // get the innermost or last one
      const modalButtons = Array.from(modal.querySelectorAll('button'));
      const submitBtn = modalButtons.find(b => b.textContent.trim() === 'Submit');
      if (submitBtn) {
        submitBtn.click();
        return { success: true, message: 'Clicked Submit button inside the modal!' };
      }
    }

    // Fallback: click the button with text "Submit" that is visible and not the main page submit button
    const submitButtons = buttons.filter(b => b.textContent.trim() === 'Submit' && b.offsetParent !== null);
    if (submitButtons.length > 0) {
      for (const btn of submitButtons) {
        const parentText = btn.parentElement?.textContent || '';
        if (parentText.includes('Do you want to submit') || btn.closest('[class*="modal"]') || btn.closest('[class*="dialog"]')) {
          btn.click();
          return { success: true, message: 'Clicked Submit button via fallback modal search!' };
        }
      }
      
      const lastBtn = submitButtons[submitButtons.length - 1];
      lastBtn.click();
      return { success: true, message: 'Clicked the last visible Submit button!' };
    }

    return { success: false, error: 'Could not find modal Submit button' };
  });

  console.log('Click result:', clickResult);
  await sleep(4000); // Wait for submission and NEXT TASK modal

  // Now check if NEXT TASK button exists at top level and click it
  console.log('Checking for NEXT TASK button at top level...');
  const nextClicked = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button, div[role="button"], a'));
    const nextBtn = buttons.find(b => {
      const t = b.textContent.trim().toLowerCase();
      return t === 'next task' || t.includes('next task') || t === 'next';
    });
    if (nextBtn && nextBtn.offsetParent !== null) {
      nextBtn.click();
      return true;
    }
    return false;
  });
  console.log('Next Task clicked at top level:', nextClicked);

  if (!nextClicked && frm1) {
    console.log('Checking for NEXT TASK button inside frame...');
    const nextClickedFrm1 = await frm1.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button, div[role="button"], a'));
      const nextBtn = buttons.find(b => {
        const t = b.textContent.trim().toLowerCase();
        return t === 'next task' || t.includes('next task') || t === 'next';
      });
      if (nextBtn && nextBtn.offsetParent !== null) {
        nextBtn.click();
        return true;
      }
      return false;
    });
    console.log('Next Task clicked inside frame:', nextClickedFrm1);
  }

  await browser.disconnect();
}

main().catch(console.error);
