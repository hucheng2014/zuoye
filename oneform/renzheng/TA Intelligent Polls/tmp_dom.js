const { chromium } = require('../node_modules/playwright');
(async()=>{
 const browser=await chromium.connectOverCDP('http://127.0.0.1:9235');
 const page=browser.contexts()[0].pages()[0];
 const frame=page.frames().find(f=>f.url().includes('/task-editor/'));
 await frame.waitForLoadState('domcontentloaded').catch(()=>{});
 const data=await frame.evaluate(()=>{
   const els=[...document.querySelectorAll('input,button,textarea,select,label,[role=radio],[role=button]')];
   return els.map((el,i)=>({i,tag:el.tagName,type:el.getAttribute('type'),role:el.getAttribute('role'),id:el.id,name:el.getAttribute('name'),value:el.getAttribute('value'),checked:el.checked,disabled:el.disabled,aria:el.getAttribute('aria-label'),text:(el.innerText||el.textContent||'').trim().replace(/\s+/g,' ').slice(0,300),html:el.outerHTML.slice(0,500)}));
 });
 console.log(JSON.stringify(data,null,2));
 await browser.close();
})();