const { chromium } = require('../node_modules/playwright');
const answers = JSON.parse(process.argv[2]);
(async()=>{
 const browser=await chromium.connectOverCDP('http://127.0.0.1:9235');
 const page=browser.contexts()[0].pages()[0];
 const frame=page.frames().find(f=>f.url().includes('/task-editor/'));
 if(!frame) throw new Error('task frame not found');
 await frame.waitForTimeout(500);
 for (const value of answers) {
   const loc = frame.locator(`input[type="radio"][value="${value}"]`).first();
   const count = await frame.locator(`input[type="radio"][value="${value}"]`).count();
   console.log('checking', value, 'count', count);
   if(count < 1) throw new Error('No radio value '+value);
   await loc.check({force:true, timeout:5000});
 }
 const checked = await frame.locator('input[type=radio]:checked').evaluateAll(els => els.map(e=>({name:e.name,value:e.value})));
 console.log('checked', checked);
 await frame.getByRole('button', {name:/^Submit$/}).click({timeout:5000});
 console.log('submitted');
 await frame.waitForTimeout(2000);
 await browser.close();
})();
