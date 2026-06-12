#!/usr/bin/env node
/**
 * capture_tutorial_screenshots.js — Capture tutorial page screenshots via CDP.
 *
 * Usage:
 *   node capture_tutorial_screenshots.js --browser work-a --url <tutorial-url>
 *   node capture_tutorial_screenshots.js --browser work-a --task polls
 *   node capture_tutorial_screenshots.js --cdp http://127.0.0.1:9233 --url <url>
 *
 * Options:
 *   --browser <id>    Browser from browsers.json (work-a, work-b, etc.)
 *   --cdp <url>       Direct CDP endpoint URL
 *   --url <url>       Tutorial/training page URL to capture
 *   --task <type>     Task type (saves to knowledge/<type>/screenshots/)
 *   --output <dir>    Output directory (default: knowledge/<task>/screenshots/)
 *   --full-page       Capture full scrollable page (default: viewport only)
 *   --scroll          Capture multiple viewport screenshots while scrolling
 *   --delay <ms>      Delay between screenshots when scrolling (default: 1000)
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const WebSocket = require('ws');

const BROWSERS_PATH = path.join(__dirname, 'browsers.json');
const KNOWLEDGE_DIR = path.join(__dirname, '..', 'knowledge');

function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  if (i === -1) return def;
  return process.argv[i + 1] || def;
}
function flag(name) {
  return process.argv.includes('--' + name);
}

function httpGet(url, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, { timeout }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => { try { resolve(JSON.parse(d)); } catch { resolve(d); } });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  });
}

function cdpCommand(ws, method, params = {}, timeout = 15000) {
  return new Promise((resolve, reject) => {
    const id = Date.now() + Math.floor(Math.random() * 1000);
    const timer = setTimeout(() => reject(new Error(`CDP timeout: ${method}`)), timeout);
    const handler = raw => {
      const msg = JSON.parse(raw);
      if (msg.id === id) {
        clearTimeout(timer);
        ws.removeListener('message', handler);
        if (msg.error) reject(new Error(msg.error.message));
        else resolve(msg.result);
      }
    };
    ws.on('message', handler);
    ws.send(JSON.stringify({ id, method, params }));
  });
}

function connectWS(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    const timer = setTimeout(() => { ws.close(); reject(new Error('WS connect timeout')); }, 8000);
    ws.on('open', () => { clearTimeout(timer); resolve(ws); });
    ws.on('error', e => { clearTimeout(timer); reject(e); });
  });
}

async function getCDPEndpoint(browserId) {
  if (!fs.existsSync(BROWSERS_PATH)) {
    throw new Error('browsers.json not found');
  }
  const browsers = JSON.parse(fs.readFileSync(BROWSERS_PATH, 'utf8')).browsers;
  const browser = browsers.find(b => b.id === browserId);
  if (!browser) {
    throw new Error(`Browser "${browserId}" not found. Available: ${browsers.map(b => b.id).join(', ')}`);
  }
  return browser.cdp;
}

async function getPageWS(cdpBase) {
  const pages = await httpGet(`${cdpBase}/json/list`);
  if (!Array.isArray(pages) || pages.length === 0) {
    throw new Error('No browser pages found');
  }
  const page = pages.find(p => p.type === 'page') || pages[0];
  return page.webSocketDebuggerUrl;
}

async function captureScreenshot(ws, options = {}) {
  const params = { format: 'png', quality: 90 };
  if (options.fullPage) {
    params.captureBeyondViewport = true;
    const layout = await cdpCommand(ws, 'Page.getLayoutMetrics');
    const { width, height } = layout.contentSize || layout.cssContentSize;
    params.clip = { x: 0, y: 0, width, height, scale: 1 };
  }
  const result = await cdpCommand(ws, 'Page.captureScreenshot', params, 30000);
  return Buffer.from(result.data, 'base64');
}

async function scrollAndCapture(ws, delay = 1000) {
  const screenshots = [];

  const metrics = await cdpCommand(ws, 'Page.getLayoutMetrics');
  const viewportHeight = metrics.visualViewport?.clientHeight || 900;
  const totalHeight = (metrics.contentSize || metrics.cssContentSize).height;
  const steps = Math.ceil(totalHeight / (viewportHeight * 0.8));

  for (let i = 0; i < steps; i++) {
    const scrollY = i * viewportHeight * 0.8;
    await cdpCommand(ws, 'Runtime.evaluate', {
      expression: `window.scrollTo(0, ${scrollY})`,
      returnByValue: true
    });
    await new Promise(r => setTimeout(r, delay));

    const buf = await captureScreenshot(ws);
    screenshots.push({ index: i, scrollY, buffer: buf });
  }

  // scroll back to top
  await cdpCommand(ws, 'Runtime.evaluate', {
    expression: 'window.scrollTo(0, 0)',
    returnByValue: true
  });

  return screenshots;
}

async function navigateAndWait(ws, url) {
  await cdpCommand(ws, 'Page.enable');
  await cdpCommand(ws, 'Page.navigate', { url });
  await new Promise(r => setTimeout(r, 3000));
  await cdpCommand(ws, 'Runtime.evaluate', {
    expression: 'document.readyState',
    returnByValue: true,
    awaitPromise: false
  });
  await new Promise(r => setTimeout(r, 2000));
}

function resolveOutputDir(taskType) {
  const mapping = {
    ta_polls: 'polls', polls: 'polls',
    mail: 'mail', tamessage: 'mail',
    proofread: 'proofread',
    ad: 'ad', search_ads: 'ad',
    rqoae: 'rqoae', audio: 'rqoae'
  };
  const normalized = (taskType || '').toLowerCase().replace(/[_\s]+/g, '_');
  const dir = mapping[normalized] || normalized;
  return path.join(KNOWLEDGE_DIR, dir, 'screenshots');
}

async function main() {
  const browserId = arg('browser', null);
  let cdpBase = arg('cdp', null);
  const url = arg('url', null);
  const taskType = arg('task', null);
  const outputDir = arg('output', null) || (taskType ? resolveOutputDir(taskType) : null);
  const fullPage = flag('full-page');
  const doScroll = flag('scroll');
  const delay = parseInt(arg('delay', '1000'), 10);

  if (!cdpBase && !browserId) {
    console.error('Usage: node capture_tutorial_screenshots.js --browser <id> [--url <url>] [--task <type>]');
    process.exit(1);
  }

  if (!outputDir) {
    console.error('Specify --task <type> or --output <dir> for screenshot destination');
    process.exit(1);
  }

  // resolve CDP endpoint
  if (!cdpBase) {
    cdpBase = await getCDPEndpoint(browserId);
  }

  // ensure output dir
  fs.mkdirSync(outputDir, { recursive: true });

  console.log(`CDP: ${cdpBase}`);
  console.log(`Output: ${outputDir}`);

  // connect
  const wsUrl = await getPageWS(cdpBase);
  const ws = await connectWS(wsUrl);
  console.log('Connected to browser');

  try {
    // navigate if URL provided
    if (url) {
      console.log(`Navigating to: ${url}`);
      await navigateAndWait(ws, url);
    }

    // get current page info
    const pageInfo = await cdpCommand(ws, 'Runtime.evaluate', {
      expression: 'JSON.stringify({ title: document.title, url: location.href })',
      returnByValue: true
    });
    const info = JSON.parse(pageInfo.result.value);
    console.log(`Page: ${info.title}`);
    console.log(`URL: ${info.url}`);

    const manifest = {
      captured_at: new Date().toISOString(),
      page_title: info.title,
      page_url: info.url,
      task_type: taskType,
      screenshots: []
    };

    if (doScroll) {
      console.log(`Capturing scroll screenshots (delay: ${delay}ms)...`);
      const shots = await scrollAndCapture(ws, delay);
      for (const shot of shots) {
        const filename = `scroll_${String(shot.index).padStart(3, '0')}.png`;
        fs.writeFileSync(path.join(outputDir, filename), shot.buffer);
        manifest.screenshots.push({
          file: filename,
          index: shot.index,
          scroll_y: shot.scrollY
        });
        console.log(`  Saved: ${filename} (scrollY: ${shot.scrollY})`);
      }
    } else {
      const filename = fullPage ? 'full_page.png' : 'viewport.png';
      console.log(`Capturing ${fullPage ? 'full page' : 'viewport'}...`);
      const buf = await captureScreenshot(ws, { fullPage });
      fs.writeFileSync(path.join(outputDir, filename), buf);
      manifest.screenshots.push({ file: filename, type: fullPage ? 'full_page' : 'viewport' });
      console.log(`  Saved: ${filename} (${(buf.length / 1024).toFixed(1)}KB)`);
    }

    // save manifest
    const manifestPath = path.join(outputDir, 'manifest.json');
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
    console.log(`Manifest: ${manifestPath}`);
    console.log(`Done — ${manifest.screenshots.length} screenshot(s) captured`);
  } finally {
    ws.close();
  }
}

main().catch(e => {
  console.error(`Error: ${e.message}`);
  process.exit(1);
});
