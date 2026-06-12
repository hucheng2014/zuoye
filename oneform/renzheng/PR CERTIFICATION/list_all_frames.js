const puppeteer = require('puppeteer-core');

const CDP_URL = 'http://127.0.0.1:9235';

async function main() {
  console.log('Connecting to browser via CDP...');
  const browser = await puppeteer.connect({
    browserURL: CDP_URL,
    defaultViewport: null
  });

  const pages = await browser.pages();
  const page = pages[0];

  console.log('✓ Connected to page:', await page.title());
  console.log('URL:', await page.url());

  const frames = page.frames();
  console.log(`\nFound ${frames.length} frames:`);
  
  for (let i = 0; i < frames.length; i++) {
    const frame = frames[i];
    console.log(`Frame ${i}:`);
    console.log(`  Name: "${frame.name()}"`);
    console.log(`  URL: "${frame.url()}"`);
    
    // Check if we can find radios in this frame
    try {
      const radioCount = await frame.evaluate(() => {
        return document.querySelectorAll('input[type="radio"]').length;
      });
      const bodyText = await frame.evaluate(() => {
        return document.body ? document.body.innerText.substring(0, 300) : 'No body';
      });
      console.log(`  Radios count: ${radioCount}`);
      console.log(`  Text snippet: "${bodyText.replace(/\n/g, ' ')}"`);
    } catch (e) {
      console.log(`  Error evaluating in frame: ${e.message}`);
    }
  }

  await browser.disconnect();
}

main().catch(console.error);
