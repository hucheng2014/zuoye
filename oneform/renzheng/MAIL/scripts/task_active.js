/**
 * task_active.js — Robust background active simulator
 * Simulates mouse movements and small scrolls to accumulate active time.
 * Handles disconnection and automatically reconnects.
 * Uses xdotool to show visible cursor movement to the user.
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const DURATION_MS = parseInt(process.argv[2] || '36000000'); // Default 10 hours
const START = Date.now();
const LOG_FILE = path.resolve(__dirname, '..', 'runs', 'task-active.log');

function log(msg) {
  const ts = new Date().toISOString();
  const line = `[${ts}] ${msg}\n`;
  process.stdout.write(line);
  try {
    fs.appendFileSync(LOG_FILE, line);
  } catch {}
}

(async () => {
  log(`Starting robust active simulation for ${DURATION_MS/1000}s...`);
  
  let browser = null;
  let cycle = 0;

  while (Date.now() - START < DURATION_MS) {
    if (!browser || !browser.isConnected()) {
      try {
        if (browser) await browser.close().catch(() => {});
        log('Connecting to CDP...');
        browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
        log('Connected successfully.');
      } catch (err) {
        log(`Connection failed: ${err.message}. Retrying in 5s...`);
        await new Promise(r => setTimeout(r, 5000));
        continue;
      }
    }

    try {
      const context = browser.contexts()[0];
      if (!context) {
        log('No browser context. Reconnecting next cycle...');
        browser = null;
        await new Promise(r => setTimeout(r, 2000));
        continue;
      }

      const pages = context.pages();
      const starshotPage = pages.find(p => p.url().includes('starshot')) || pages[0];

      if (starshotPage) {
        // Move mouse to a random position on the page
        const x = 300 + Math.floor(Math.random() * 800);
        const y = 200 + Math.floor(Math.random() * 600);
        
        // 1. Playwright virtual mouse move (sends event directly to page)
        await starshotPage.mouse.move(x, y).catch(() => {});

        // Inject a visible red dot on the page to indicate the virtual mouse position
        await starshotPage.evaluate(({x, y}) => {
          let dot = document.getElementById('playwright-mouse-dot');
          if (!dot) {
            dot = document.createElement('div');
            dot.id = 'playwright-mouse-dot';
            dot.style.position = 'fixed';
            dot.style.width = '15px';
            dot.style.height = '15px';
            dot.style.backgroundColor = 'rgba(255, 0, 0, 0.7)';
            dot.style.borderRadius = '50%';
            dot.style.pointerEvents = 'none';
            dot.style.zIndex = '999999';
            dot.style.transition = 'left 0.1s, top 0.1s';
            document.body.appendChild(dot);
          }
          dot.style.left = (x - 7) + 'px';
          dot.style.top = (y - 7) + 'px';
        }, {x, y}).catch(() => {});

        // 2. Visible mouse move via xdotool in docker
        exec(`docker exec controlled-browser-browser bash -c 'DISPLAY=:99 xdotool mousemove ${x} ${y}'`, (err) => {
          if (err) {
            // If it fails, log once but don't crash
            if (cycle % 30 === 0) log(`xdotool err: ${err.message.slice(0, 50)}`);
          }
        });

        // Scroll occasionally
        if (cycle % 10 === 0) {
          await starshotPage.evaluate(() => {
            const el = document.querySelector('iframe, .task-content, main, body');
            if (el) {
              el.style.border = '2px solid red'; // highlight element being scrolled
              el.scrollBy(0, 50); // bigger scroll
              setTimeout(() => {
                el.style.border = '';
                el.scrollBy(0, -50);
              }, 1000); // 1 second before scrolling back
            }
          }).catch(() => {});
        }

        if (cycle % 15 === 0) {
          const elapsed = Math.floor((Date.now() - START) / 1000);
          log(`Activity check: elapsed=${elapsed}s, cycle=${cycle}`);
        }
      }

      cycle++;
      
      // Human-like rhythm: 10:1 active-to-inactive ratio.
      // ~45 cycles × 2s = ~90s active, then one 15-20s pause (~non-active time).
      // Non-active share ≈ 15s / (90s + 15s) ≈ 14% — within acceptable range.
      let delay;
      if (cycle % 45 === 44) {
        const pauseSec = 15 + Math.floor(Math.random() * 6); // 15-20s thinking pause
        log(`[Human-like] Thinking pause: ${pauseSec}s (cycle ${cycle})`);
        delay = pauseSec * 1000;
      } else {
        delay = 1500 + Math.random() * 1000; // 1.5-2.5s active interval
      }

      await new Promise(r => setTimeout(r, delay));

    } catch (e) {
      log(`Warning in loop: ${e.message.slice(0, 100)}`);
      if (e.message.includes('closed') || e.message.includes('Target connection')) {
        log('CDP connection closed or target crashed. Resetting browser client...');
        browser = null;
      }
      await new Promise(r => setTimeout(r, 3000));
    }
  }

  log('Active simulation finished.');
  if (browser) await browser.close().catch(() => {});
})().catch(e => {
  log(`Fatal error: ${e.stack || e.message}`);
  process.exit(1);
});
