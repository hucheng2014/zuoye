const { chromium } = require('playwright');

const CDP_ENDPOINT = process.env.MAIL_CDP_ENDPOINT || 'http://127.0.0.1:9233';
const TARGET_SECONDS = parseInt(process.argv[2] || '600', 10);

async function getTimerValue(page) {
  return await page.evaluate(() => {
    // Look for text in divs/spans that looks like a timer
    const elements = Array.from(document.querySelectorAll('div, span, p'));
    for (const el of elements) {
      const txt = (el.innerText || el.textContent || '').trim();
      if (/^\d+[smh]$/i.test(txt)) return txt;
      if (/^\d+:\d+(:\d+)?$/.test(txt)) return txt;
    }
    return null;
  });
}

function parseTimerToSeconds(str) {
  if (!str) return 0;
  
  // Format: "123s"
  let match = str.match(/^(\d+)s$/i);
  if (match) return parseInt(match[1], 10);
  
  // Format: "10m"
  match = str.match(/^(\d+)m$/i);
  if (match) return parseInt(match[1], 10) * 60;
  
  // Format: "1h"
  match = str.match(/^(\d+)h$/i);
  if (match) return parseInt(match[1], 10) * 3600;

  // Format: "MM:SS" or "HH:MM:SS"
  if (str.includes(':')) {
    const parts = str.split(':').map(Number);
    if (parts.length === 2) {
      return parts[0] * 60 + parts[1];
    } else if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
    }
  }
  
  return 0;
}

async function main() {
  console.log(`Waiting for active timer to reach ${TARGET_SECONDS}s...`);
  
  while (true) {
    let browser;
    try {
      browser = await chromium.connectOverCDP(CDP_ENDPOINT);
      const context = browser.contexts()[0];
      if (!context) throw new Error('No context');
      const page = context.pages().find((p) => p.url().includes('starshot.scilliance.com')) || context.pages()[0];
      if (!page) throw new Error('No page');
      
      const timerStr = await getTimerValue(page);
      const seconds = parseTimerToSeconds(timerStr);
      
      console.log(`[${new Date().toLocaleTimeString()}] Timer text: "${timerStr || 'not found'}" => ${seconds}s / ${TARGET_SECONDS}s`);
      
      if (seconds >= TARGET_SECONDS) {
        console.log(`Success: Active timer reached ${seconds}s (target ${TARGET_SECONDS}s).`);
        break;
      }
    } catch (err) {
      console.error(`Error checking timer: ${err.message}. Retrying in 10s...`);
    } finally {
      if (browser) await browser.close().catch(() => {});
    }
    
    await new Promise((r) => setTimeout(r, 10000));
  }
}

main().catch(console.error);
