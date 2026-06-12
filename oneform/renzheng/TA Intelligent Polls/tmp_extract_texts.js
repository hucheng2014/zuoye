const { chromium } = require('../node_modules/playwright');
(async()=>{const browser=await chromium.connectOverCDP('http://127.0.0.1:9235'); const page=browser.contexts()[0].pages()[0]; await page.waitForTimeout(1000); const frame=page.frames().find(f=>f.url().includes('/task-editor/')); const data=await frame.evaluate(()=>{
 function path(el){let s=[]; for(let e=el; e&&e.nodeType===1&&s.length<5; e=e.parentElement){let p=e.tagName.toLowerCase(); if(e.id)p+='#'+e.id; if(e.className&&typeof e.className==='string')p+='.'+e.className.split(/\s+/).slice(0,2).join('.'); s.unshift(p)} return s.join('>')}
 const els=[...document.querySelectorAll('body *')];
 return els.map((el,i)=>({i,path:path(el),text:(el.innerText||el.textContent||'').trim().replace(/\s+/g,' ').slice(0,500),rect:(()=>{let r=el.getBoundingClientRect();return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}})(), display:getComputedStyle(el).display, visibility:getComputedStyle(el).visibility})).filter(e=>e.text && e.rect.w>0 && e.rect.h>0);
});
 for(const e of data){ if(/Me:|Poll Title|Poll Options|User|Predicted|Title|Options|Pizza|Burg|Theater|Opera|Next|Should|No poll|Poll is|Complete|following|composition|grounded|satisfying/i.test(e.text)) console.log(JSON.stringify(e)); }
 console.log('count',data.length); await browser.close();})();