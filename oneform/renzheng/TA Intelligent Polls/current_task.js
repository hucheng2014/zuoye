const { chromium } = require('../node_modules/playwright');
(async()=>{
 const b=await chromium.connectOverCDP('http://127.0.0.1:9235');
 const p=b.contexts()[0].pages()[0];
 const info=await p.evaluate(async()=>{
   const urls=performance.getEntriesByType('resource').map(e=>e.name).filter(n=>n.includes('/ds/items/'));
   const url=urls[urls.length-1];
   const res=await fetch(url,{credentials:'include'});
   const json=await res.json();
   return {url, item: json.assets.dict[0]};
 });
 const frame=p.frames().find(f=>f.url().includes('/task-editor/'));
 const checked=frame? await frame.locator('input:checked').evaluateAll(els=>els.map(e=>({type:e.type,name:e.name,value:e.value}))).catch(e=>[]):[];
 console.log(JSON.stringify({prompt_id:info.item.prompt_id, query_id:info.item.query_id, locale:info.item.locale, prompt:info.item.prompt, outputs:info.item.outputs, num_output:info.item.num_output, checked}, null, 2));
 await b.close();
})();
