const { chromium } = require('../node_modules/playwright');
(async()=>{
 const browser=await chromium.connectOverCDP('http://127.0.0.1:9235');
 const page=browser.contexts()[0].pages()[0];
 await page.waitForTimeout(1000);
 console.log('title', await page.title(), page.url());
 console.log('frames', page.frames().length);
 for (const [i, f] of page.frames().entries()) {
   console.log('\nFRAME',i, f.url(), f.name());
   const text=await f.locator('body').innerText({timeout:3000}).catch(e=>'ERR '+e.message);
   console.log(text.slice(0,4000));
   const html=await f.content().catch(e=>'ERR '+e.message);
   console.log('html head',html.slice(0,500).replace(/\n/g,' '));
 }
 const html = await page.content();
 console.log('main content len', html.length, html.slice(0,2000));
 await browser.close();
})();