const fs = require('fs');
const WebSocket = require('../node_modules/ws');
const CDP = 'http://127.0.0.1:9235';
const LOG = 'capture_second_emoji.log';
function log(...a){ fs.appendFileSync(LOG, `[${new Date().toISOString()}] ${a.join(' ')}\n`); console.log(...a); }
async function connect(wsUrl){
  let id=0; const pending=new Map(); const handlers=new Map(); const ws=new WebSocket(wsUrl);
  await new Promise((res,rej)=>{const t=setTimeout(()=>rej(Error('open timeout')),5000); ws.once('open',()=>{clearTimeout(t);res()}); ws.once('error',rej);});
  ws.on('message', d=>{const m=JSON.parse(d); if(m.id&&pending.has(m.id)){const p=pending.get(m.id); pending.delete(m.id); clearTimeout(p.t); m.error?p.rej(Error(JSON.stringify(m.error))):p.res(m);} else if(m.method&&handlers.has(m.method)){for(const h of handlers.get(m.method)) h(m.params||{});}});
  return {send(method,params={},timeout=15000){return new Promise((res,rej)=>{const mid=++id; const t=setTimeout(()=>{if(pending.delete(mid)) rej(Error(method+' timeout'));},timeout); pending.set(mid,{res,rej,t}); ws.send(JSON.stringify({id:mid,method,params}));});}, on(method,h){ if(!handlers.has(method)) handlers.set(method,[]); handlers.get(method).push(h); }, close(){ws.close();}};
}
function safe(s){return s.replace(/[^\w\u4e00-\u9fa5.-]+/g,'_').replace(/_+/g,'_').replace(/^_|_$/g,'')}
(async()=>{
  fs.writeFileSync(LOG, '');
  const pages=(await (await fetch(CDP+'/json/list')).json()).filter(p=>p.type==='page');
  const p=pages.find(x=>/Emoji Evaluation Design/i.test(x.title) || /Emoji%20Evaluation%20Design/i.test(x.url));
  if(!p) throw Error('Emoji Evaluation Design tab not found');
  log('target', p.title, p.url);
  const client=await connect(p.webSocketDebuggerUrl);
  let done=false; let seen=0;
  client.on('Fetch.requestPaused', async e=>{
    seen++;
    const ct=(e.responseHeaders||[]).find(h=>h.name.toLowerCase()==='content-type')?.value || '';
    log('paused', seen, e.request.method, e.resourceType, e.responseStatusCode, ct, e.request.url.slice(0,180));
    if(done || e.request.method!=='GET' || !e.request.url.includes('/transform/passthrough')){
      try{ await client.send('Fetch.continueRequest',{requestId:e.requestId},10000); }catch(err){ log('continue error', err.message); }
      return;
    }
    try{
      log('getting response body...');
      const body=await client.send('Fetch.getResponseBody',{requestId:e.requestId},180000);
      const b=body.result; const buf=b.base64Encoded?Buffer.from(b.body,'base64'):Buffer.from(b.body,'utf8');
      const name=`02_${safe(p.title)}.pdf`;
      fs.writeFileSync(name, buf);
      const meta={title:p.title,pageUrl:p.url,capturedUrl:e.request.url,status:e.responseStatusCode,headers:e.responseHeaders,file:name,len:buf.length,first:buf.subarray(0,16).toString('latin1').replace(/[^\x20-\x7E]/g,'.'),hex:buf.subarray(0,16).toString('hex')};
      fs.writeFileSync(name+'.json', JSON.stringify(meta,null,2));
      log('saved', name, buf.length, meta.first);
      done=true;
      await client.send('Fetch.fulfillRequest',{requestId:e.requestId,responseCode:204,responseHeaders:[{name:'Content-Length',value:'0'}],body:''},10000).catch(()=>{});
    }catch(err){
      log('capture error', err.message);
      try{ await client.send('Fetch.continueRequest',{requestId:e.requestId},10000); }catch(e2){ log('continue after error failed', e2.message); }
    }
  });
  await client.send('Page.enable');
  await client.send('Fetch.enable',{patterns:[{urlPattern:'*transform/passthrough*',requestStage:'Response'}]});
  log('reload');
  await client.send('Page.reload',{ignoreCache:true},10000).catch(e=>log('reload returned', e.message));
  const deadline=Date.now()+210000;
  while(!done && Date.now()<deadline){ await new Promise(r=>setTimeout(r,2000)); log('poll done='+done+' seen='+seen); }
  await client.send('Fetch.disable').catch(()=>{});
  client.close();
  if(!done) throw Error('timeout capturing Emoji Evaluation Design');
})().catch(e=>{ log('FATAL', e.stack||e.message); process.exit(1); });
