const { chromium } = require('../node_modules/playwright');
(async()=>{const browser=await chromium.connectOverCDP('http://127.0.0.1:9235'); const page=browser.contexts()[0].pages()[0]; const frame=page.frames().find(f=>f.url().includes('/task-editor/')); const data=await frame.evaluate(()=>{
 const out={};
 out.localStorage={}; for(let i=0;i<localStorage.length;i++){let k=localStorage.key(i); out.localStorage[k]=localStorage.getItem(k)?.slice(0,5000);}
 out.sessionStorage={}; for(let i=0;i<sessionStorage.length;i++){let k=sessionStorage.key(i); out.sessionStorage[k]=sessionStorage.getItem(k)?.slice(0,5000);}
 out.windowKeys=Object.keys(window).filter(k=>/task|data|poll|answer|schema|redux|apollo|store|star|scil|label/i.test(k)).slice(0,200);
 out.bodyDataset={...document.body.dataset};
 const scripts=[...document.scripts].map(s=>({src:s.src, text:s.textContent.slice(0,200)})); out.scripts=scripts;
 return out;
}); console.log(JSON.stringify(data,null,2)); await browser.close();})();