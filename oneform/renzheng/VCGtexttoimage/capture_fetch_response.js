const fs = require('fs');
const WebSocket = require('../node_modules/ws');
const CDP='http://127.0.0.1:9235';
async function connect(wsUrl){let id=0;const pending=new Map();const handlers=new Map();const ws=new WebSocket(wsUrl);await new Promise((res,rej)=>{const t=setTimeout(()=>rej(Error('open timeout')),5000);ws.once('open',()=>{clearTimeout(t);res()});ws.once('error',rej)});ws.on('message',d=>{const m=JSON.parse(d);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);clearTimeout(p.t);m.error?p.rej(Error(JSON.stringify(m.error))):p.res(m)}else if(m.method&&handlers.has(m.method)){for(const h of handlers.get(m.method))h(m.params||{})}});return{send(method,params={},timeout=15000){return new Promise((res,rej)=>{const mid=++id;const t=setTimeout(()=>{if(pending.delete(mid))rej(Error(method+' timeout'))},timeout);pending.set(mid,{res,rej,t});ws.send(JSON.stringify({id:mid,method,params}))})},on(method,h){if(!handlers.has(method))handlers.set(method,[]);handlers.get(method).push(h)},close(){ws.close()}}}
function safe(s){return s.replace(/[^\w\u4e00-\u9fa5.-]+/g,'_').replace(/_+/g,'_').replace(/^_|_$/g,'')}
(async()=>{
 const pages=(await (await fetch(CDP+'/json/list')).json()).filter(p=>p.type==='page');
 for(let i=0;i<pages.length;i++){
  const p=pages[i]; const client=await connect(p.webSocketDebuggerUrl); let done=false; let saved=null; let paused=0;
  client.on('Fetch.requestPaused', async e=>{
    paused++;
    console.log('paused',i+1, paused, e.request.method, e.resourceType, e.responseStatusCode, e.responseHeaders?.find(h=>h.name.toLowerCase()==='content-type')?.value, e.request.url.slice(0,160));
    if(done || e.request.method !== 'GET' || !e.request.url.includes('/transform/passthrough')) {
      try{await client.send('Fetch.continueRequest',{requestId:e.requestId},10000)}catch{}
      return;
    }
    try{
      const body=await client.send('Fetch.getResponseBody',{requestId:e.requestId},80000);
      const b=body.result; const buf=b.base64Encoded?Buffer.from(b.body,'base64'):Buffer.from(b.body,'utf8');
      const name=`${String(i+1).padStart(2,'0')}_${safe(p.title)}_fetch.bin`;
      fs.writeFileSync(name,buf);
      saved={title:p.title,url:e.request.url,status:e.responseStatusCode,headers:e.responseHeaders,file:name,len:buf.length,first:buf.subarray(0,16).toString('latin1').replace(/[^\x20-\x7E]/g,'.'),hex:buf.subarray(0,16).toString('hex')};
      fs.writeFileSync(name+'.json',JSON.stringify(saved,null,2));
      console.log('saved',name,buf.length,saved.first);
      done=true;
      // Return a tiny 204 response to release the browser; we already captured the body.
      await client.send('Fetch.fulfillRequest',{requestId:e.requestId,responseCode:204,responseHeaders:[{name:'Content-Length',value:'0'}],body:''},10000).catch(()=>{});
    }catch(err){
      console.error('capture error',err.message);
      try{await client.send('Fetch.continueRequest',{requestId:e.requestId},10000)}catch{}
    }
  });
  await client.send('Page.enable');
  await client.send('Fetch.enable',{patterns:[{urlPattern:'*transform/passthrough*',requestStage:'Response'}]});
  console.log('reload',i+1,p.title);
  await client.send('Page.reload',{ignoreCache:true},10000).catch(()=>{});
  const deadline=Date.now()+90000;
  while(!done && Date.now()<deadline){await new Promise(r=>setTimeout(r,1000));}
  await client.send('Fetch.disable').catch(()=>{});
  client.close();
  if(!done) throw Error('timeout capturing '+p.title);
 }
})();
