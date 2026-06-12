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
  const frm1 = frames.find(f => f.url().includes('task-editor'));

  // Helper to click Next Task button
  const clickNextTask = async (context, name) => {
    return await context.evaluate((ctxName) => {
      const buttons = Array.from(document.querySelectorAll('button, div[role="button"], a'));
      const nextBtn = buttons.find(b => {
        const t = b.textContent.trim().toLowerCase();
        return t === 'next task' || t.includes('next task') || t === 'next';
      });
      if (nextBtn && nextBtn.offsetParent !== null) {
        nextBtn.click();
        return { success: true, message: `Clicked Next Task button in ${ctxName}!` };
      }
      return { success: false };
    }, name);
  };

  // Try top level first
  let res = await clickNextTask(page, 'top level');
  console.log('Top level check:', res);

  if (!res.success && frm1) {
    // Try inside frm1
    res = await clickNextTask(frm1, 'frm1');
    console.log('frm1 check:', res);
  }

  if (res.success) {
    console.log('⏳ Waiting 6 seconds for new task to load...');
    await sleep(6000);
  } else {
    console.log('Could not find Next Task button. Page might have already loaded or we need to wait.');
  }

  await browser.disconnect();
}

main().catch(console.error);
