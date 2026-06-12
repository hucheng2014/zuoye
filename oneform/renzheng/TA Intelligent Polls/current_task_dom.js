const { chromium } = require('../node_modules/playwright');
function extractJsonFromCreateTaskAPI(html){
  const idx = html.indexOf('createTaskAPI(');
  if (idx < 0) throw new Error('createTaskAPI not found');
  const comma = html.indexOf(',', idx);
  if (comma < 0) throw new Error('comma not found');
  let start = html.indexOf('{', comma);
  if (start < 0) throw new Error('json start not found');
  let depth = 0, inStr = false, esc = false;
  for (let i=start; i<html.length; i++) {
    const ch = html[i];
    if (inStr) { if (esc) esc=false; else if (ch==='\\') esc=true; else if (ch==='"') inStr=false; }
    else { if (ch==='"') inStr=true; else if (ch==='{') depth++; else if (ch==='}') { depth--; if(depth===0) return html.slice(start,i+1); } }
  }
  throw new Error('json end not found');
}
(async()=>{
 const b=await chromium.connectOverCDP('http://127.0.0.1:9235');
 const p=b.contexts()[0].pages()[0];
 const frames=p.frames();
 let item=null, source='';
 for(const f of frames){
   const html=await f.content().catch(e=>'');
   if(html.includes('createTaskAPI(')){
     try { item=JSON.parse(extractJsonFromCreateTaskAPI(html)); source=f.url(); break; } catch(e) { /* continue */ }
   }
 }
 const taskFrame=frames.find(f=>f.url().includes('/task-editor/'));
 const checked=taskFrame? await taskFrame.locator('input:checked').evaluateAll(els=>els.map(e=>({type:e.type,name:e.name,value:e.value}))).catch(e=>[]):[];
 const body=await p.locator('body').innerText().catch(e=>'');
 const noMore=/No more tasks available/i.test(body);
 console.log(JSON.stringify({noMore, source, prompt_id:item?.prompt_id, query_id:item?.query_id, locale:item?.locale, prompt:item?.prompt, outputs:item?.outputs, num_output:item?.num_output, checked}, null, 2));
 await b.close();
})();
