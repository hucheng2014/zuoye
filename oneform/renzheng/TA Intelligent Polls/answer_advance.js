const { chromium } = require('../node_modules/playwright');
const spec = JSON.parse(process.argv[2]);
function cssEscapeValue(v){ return v.replace(/\\/g,'\\\\').replace(/"/g,'\\"'); }
(async()=>{
 const b=await chromium.connectOverCDP('http://127.0.0.1:9235');
 const p=b.contexts()[0].pages()[0];
 const frame=p.frames().find(f=>f.url().includes('/task-editor/'));
 if(!frame) throw new Error('task frame not found');
 await frame.waitForTimeout(300);
 const radios=spec.radios || spec;
 for (const value of radios) {
   const sel = `input[type="radio"][value="${cssEscapeValue(value)}"]`;
   const count = await frame.locator(sel).count();
   console.log('radio', value, 'count', count);
   if (count < 1) throw new Error('No radio '+value);
   if (count > 1 && !spec.allowMultipleSameValue) console.log('warning: multiple radios for value', value);
   // if duplicate values, choose first visible/attached not checked
   await frame.locator(sel).first().check({force:true, timeout:5000});
   await frame.waitForTimeout(100);
 }
 for (const value of (spec.checkboxes || [])) {
   const sel = `input[type="checkbox"][value="${cssEscapeValue(value)}"]`;
   const count = await frame.locator(sel).count();
   console.log('checkbox', value, 'count', count);
   if (count < 1) throw new Error('No checkbox '+value);
   await frame.locator(sel).first().check({force:true, timeout:5000});
   await frame.waitForTimeout(100);
 }
 if (spec.comment) {
   const ta=frame.locator('textarea').first();
   if (await ta.count()) await ta.fill(spec.comment);
 }
 const checked = await frame.locator('input:checked').evaluateAll(els => els.map(e=>({type:e.type,name:e.name,value:e.value})));
 console.log('checked', checked);
 if (spec.submit !== false) {
   await frame.getByRole('button', {name:/^Submit$/}).click({timeout:8000});
   console.log('clicked frame submit');
   // click confirmation if it appears
   const confirm = p.locator('#starshot_submit_task_button');
   try { await confirm.waitFor({state:'visible', timeout:5000}); await confirm.click(); console.log('clicked confirm submit'); } catch(e) { console.log('no confirm:', e.message.split('\n')[0]); }
   if (spec.next !== false) {
     const next = p.locator('#starshot_next_task_button');
     try { await next.waitFor({state:'visible', timeout:10000}); await next.click(); console.log('clicked next'); } catch(e) { console.log('no next:', e.message.split('\n')[0]); }
   }
   await p.waitForTimeout(spec.wait || 3000);
 }
 await b.close();
})();
