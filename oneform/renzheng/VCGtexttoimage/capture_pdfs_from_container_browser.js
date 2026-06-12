const fs = require('fs');
const path = require('path');
const WebSocket = require('../node_modules/ws');

const CDP = 'http://127.0.0.1:9235';

async function connect(wsUrl) {
  let id = 0;
  const pending = new Map();
  const handlers = new Map();
  const ws = new WebSocket(wsUrl);
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error('WebSocket open timeout')), 5000);
    ws.once('open', () => { clearTimeout(t); resolve(); });
    ws.once('error', reject);
  });
  ws.on('message', data => {
    const msg = JSON.parse(data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject, timer } = pending.get(msg.id);
      pending.delete(msg.id);
      clearTimeout(timer);
      if (msg.error) reject(new Error(JSON.stringify(msg.error)));
      else resolve(msg);
    } else if (msg.method && handlers.has(msg.method)) {
      for (const h of handlers.get(msg.method)) h(msg.params || {});
    }
  });
  return {
    send(method, params = {}, timeout = 15000) {
      return new Promise((resolve, reject) => {
        const mid = ++id;
        const timer = setTimeout(() => {
          if (pending.delete(mid)) reject(new Error(`${method} timeout`));
        }, timeout);
        pending.set(mid, { resolve, reject, timer });
        ws.send(JSON.stringify({ id: mid, method, params }));
      });
    },
    on(method, handler) {
      if (!handlers.has(method)) handlers.set(method, []);
      handlers.get(method).push(handler);
    },
    close() { ws.close(); }
  };
}

function safeName(title) {
  return title.replace(/[^\w\u4e00-\u9fa5.-]+/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '');
}

async function capturePage(page, index) {
  const client = await connect(page.webSocketDebuggerUrl);
  const candidates = new Map();
  const extraHeaders = new Map();

  client.on('Network.requestWillBeSent', e => {
    const url = e.request?.url || '';
    if (url.includes('/transform/passthrough') || /\.pdf(?:$|[?#])/i.test(url)) {
      candidates.set(e.requestId, {
        requestId: e.requestId,
        url,
        method: e.request.method,
        reqHeaders: e.request.headers || {},
        type: e.type,
        status: null,
        mimeType: null,
        finished: false,
        failed: false,
        errorText: null,
        encodedDataLength: 0
      });
    }
  });
  client.on('Network.requestWillBeSentExtraInfo', e => {
    if (candidates.has(e.requestId)) extraHeaders.set(e.requestId, e.headers || {});
  });
  client.on('Network.responseReceived', e => {
    if (candidates.has(e.requestId)) {
      const c = candidates.get(e.requestId);
      c.status = e.response.status;
      c.mimeType = e.response.mimeType;
      c.resHeaders = e.response.headers || {};
    }
  });
  client.on('Network.loadingFinished', e => {
    if (candidates.has(e.requestId)) {
      const c = candidates.get(e.requestId);
      c.finished = true;
      c.encodedDataLength = e.encodedDataLength;
    }
  });
  client.on('Network.loadingFailed', e => {
    if (candidates.has(e.requestId)) {
      const c = candidates.get(e.requestId);
      c.failed = true;
      c.errorText = e.errorText;
    }
  });

  try {
    await client.send('Page.enable');
    await client.send('Runtime.enable');
    await client.send('Network.enable', {
      maxTotalBufferSize: 120 * 1024 * 1024,
      maxResourceBufferSize: 80 * 1024 * 1024
    });
    await client.send('Network.setCacheDisabled', { cacheDisabled: true });

    console.log(`Reloading tab ${index}: ${page.title}`);
    await client.send('Page.reload', { ignoreCache: true }, 10000).catch(() => {});

    const deadline = Date.now() + 65000;
    let lastCount = -1;
    while (Date.now() < deadline) {
      const vals = [...candidates.values()];
      const finished = vals.filter(c => c.finished && !c.failed);
      if (vals.length !== lastCount) {
        lastCount = vals.length;
        console.log(`  observed ${vals.length} PDF-related request(s)`);
      }
      const usableList = finished
        .filter(c => c.status === 200 && c.method === 'GET' && (c.encodedDataLength || 0) > 100000)
        .sort((a, b) => (b.encodedDataLength || 0) - (a.encodedDataLength || 0));
      for (const usable of usableList) {
        console.log(`  trying ${usable.requestId} method=${usable.method} status=${usable.status} mime=${usable.mimeType} bytes=${usable.encodedDataLength}`);
        let body;
        try {
          body = await client.send('Network.getResponseBody', { requestId: usable.requestId }, 30000);
        } catch (e) {
          usable.bodyError = e.message;
          console.log(`    body unavailable: ${e.message}`);
          continue;
        }
        const b = body.result;
        const buf = b.base64Encoded ? Buffer.from(b.body, 'base64') : Buffer.from(b.body, 'utf8');
        if (buf.length < 100000) {
          usable.bodyError = `body too small: ${buf.length}`;
          continue;
        }
        const name = `${String(index).padStart(2, '0')}_${safeName(page.title)}.bin`;
        fs.writeFileSync(name, buf);
        const meta = {
          title: page.title,
          pageUrl: page.url,
          capturedUrl: usable.url,
          status: usable.status,
          mimeType: usable.mimeType,
          encodedDataLength: usable.encodedDataLength,
          savedFile: path.resolve(name),
          firstBytesHex: buf.subarray(0, 16).toString('hex'),
          firstBytesAscii: buf.subarray(0, 16).toString('latin1').replace(/[^\x20-\x7E]/g, '.'),
          requestHeaders: { ...usable.reqHeaders, ...extraHeaders.get(usable.requestId) },
          responseHeaders: usable.resHeaders
        };
        fs.writeFileSync(name + '.json', JSON.stringify(meta, null, 2));
        console.log(`  saved ${name} (${buf.length} bytes), first=${meta.firstBytesAscii}`);
        return meta;
      }
      await new Promise(r => setTimeout(r, 1000));
    }
    const debug = [...candidates.values()].map(c => ({url:c.url,status:c.status,mimeType:c.mimeType,finished:c.finished,failed:c.failed,errorText:c.errorText,encodedDataLength:c.encodedDataLength}));
    fs.writeFileSync(`debug_${index}_${safeName(page.title)}.json`, JSON.stringify(debug, null, 2));
    throw new Error(`No usable PDF response captured for ${page.title}`);
  } finally {
    client.close();
  }
}

(async () => {
  const pages = (await (await fetch(`${CDP}/json/list`)).json()).filter(p => p.type === 'page');
  console.log(`Found ${pages.length} page tab(s)`);
  const metas = [];
  for (let i = 0; i < pages.length; i++) {
    metas.push(await capturePage(pages[i], i + 1));
  }
  fs.writeFileSync('captured_pdfs_manifest.json', JSON.stringify(metas, null, 2));
  console.log('DONE');
})().catch(err => {
  console.error('FATAL', err.stack || err.message);
  process.exit(1);
});
