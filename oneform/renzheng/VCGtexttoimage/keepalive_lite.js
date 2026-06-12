/**
 * keepalive_lite.js — Lightweight keepalive for VCG Eval Multi Side.
 *
 * Use this WHILE actively answering questions — it only prevents
 * the 10s inactivity cutoff without interfering with your clicks.
 * Does not scroll the iframe or hover images.
 *
 * Usage:
 *   node VCGtexttoimage/keepalive_lite.js
 *   # Ctrl+C to stop
 */

const { chromium } = require('playwright');

const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';
const FALLBACK_CDP = 'http://127.0.0.1:9232';

let running = true;
process.on('SIGINT', () => { running = false; });
process.on('SIGTERM', () => { running = false; });

function randInt(min, max) { return Math.floor(min + Math.random() * (max - min + 1)); }

async function connect() {
  for (const ep of [CDP, FALLBACK_CDP]) {
    try { return await chromium.connectOverCDP(ep); } catch {}
  }
  throw new Error('[keepalive_lite] No CDP endpoint');
}

(async () => {
  const browser = await connect();
  const ctx = browser.contexts()[0];
  if (!ctx) throw new Error('[keepalive_lite] No browser context');

  let page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  if (!page) throw new Error('[keepalive_lite] No page');

  console.log('[keepalive_lite] VCG — gentle keepalive (Ctrl+C to stop)');

  let cycle = 0;
  while (running) {
    try {
      page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];

      // Gentle mouse move only — won't interfere with manual clicks
      const x = randInt(50, 300);
      const y = randInt(50, 200);
      await page.mouse.move(x, y, { steps: randInt(2, 5) });

      // Occasional tiny scroll on outer page (not iframe)
      if (cycle % 3 === 0) {
        const dy = randInt(-20, 20);
        await page.evaluate((d) => window.scrollBy(0, d), dy);
      }

      const elapsed = Math.floor((Date.now() - start) / 1000);
      process.stdout.write(`\r[keepalive_lite] cycle=${cycle} elapsed=${elapsed}s  `);
      cycle++;

      await page.waitForTimeout(randInt(5000, 8000));
    } catch (e) {
      if (!running) break;
      if (e.message.includes('closed')) break;
      await new Promise(r => setTimeout(r, 3000));
    }
  }
  console.log('\n[keepalive_lite] Stopped.');
  await browser.close();
  process.exit(0);
})().catch(e => {
  console.error('[keepalive_lite] Fatal:', e.message);
  process.exit(1);
});

const start = Date.now();
