const { chromium } = require('../node_modules/playwright');
(async()=>{
 const browser=await chromium.connectOverCDP('http://127.0.0.1:9235');
 const page=browser.contexts()[0].pages()[0];
 await page.screenshot({path:'page.png', fullPage:true});
 console.log('shot');
 await browser.close();
})();