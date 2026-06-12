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
  const frm1 = frames.find(f => f.url().includes('task-editor'));

  if (!frm1) {
    console.error('Task editor frame not found');
    await browser.disconnect();
    return;
  }

  const fullPrompt = await frm1.evaluate(() => {
    const promptContainer = document.querySelector('.user-request, blockquote, [class*="user-request"]');
    return promptContainer ? promptContainer.innerText : document.body.innerText;
  });

  console.log('=== FULL USER PROMPT ===');
  console.log(fullPrompt);

  await browser.disconnect();
}

main().catch(console.error);
