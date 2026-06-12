const puppeteer = require('puppeteer-core');
const fs = require('fs');

const CDP_URL = 'http://127.0.0.1:9235';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log('Connecting to browser via CDP...');
  const browser = await puppeteer.connect({
    browserURL: CDP_URL,
    defaultViewport: null
  });

  const pages = await browser.pages();
  const page = pages[0];

  console.log('✓ Connected to Annotation Tool page');

  // Find the frm1 frame
  const frames = page.frames();
  const frm1 = frames.find(f => f.name() === 'frm1');

  if (!frm1) {
    console.error('Error: Frame "frm1" not found!');
    await browser.disconnect();
    return;
  }

  console.log('✓ Found "frm1" frame');

  // Get user request
  const userRequest = await frm1.evaluate(() => {
    // Find the User Request area
    const headers = Array.from(document.querySelectorAll('h1, h2, div, p'));
    let requestText = 'Not found';
    for (const h of headers) {
      if (h.textContent.trim() === 'User Request') {
        const container = h.closest('div');
        if (container) {
          requestText = container.innerText;
          break;
        }
      }
    }
    return requestText;
  });

  console.log('\n=======================================');
  console.log('USER REQUEST & LOCALE:');
  console.log('=======================================');
  console.log(userRequest);

  // Get responses by clicking tabs
  const tabTexts = ['Response A', 'Response B', 'Response C'];
  const responses = {};

  for (let i = 0; i < tabTexts.length; i++) {
    const tabText = tabTexts[i];
    console.log(`\n--- Fetching ${tabText}... ---`);
    
    // Click tab
    const clicked = await frm1.evaluate((text) => {
      const tabs = Array.from(document.querySelectorAll('[role="tab"], button'));
      const tab = tabs.find(t => t.textContent.includes(text));
      if (tab) {
        tab.click();
        return true;
      }
      return false;
    }, tabText);

    if (clicked) {
      await sleep(1000);
      // Get the text from the corresponding panel
      const panelText = await frm1.evaluate((index) => {
        // Look for panel by class or role
        const panels = Array.from(document.querySelectorAll('[role="tabpanel"], div'));
        // Find panels that are visible and contain robot emoji or Response text
        const visiblePanels = panels.filter(p => {
          const style = window.getComputedStyle(p);
          return style.display !== 'none' && style.visibility !== 'hidden' && p.offsetHeight > 0;
        });
        
        // Find the panel text content
        for (const p of visiblePanels) {
          if (p.textContent.includes('Response') && (p.textContent.includes('Ah,') || p.textContent.includes('Grover') || p.textContent.length > 100)) {
            // Let's filter out headers and only return the body text
            return p.innerText;
          }
        }
        return document.body.innerText; // fallback
      }, i);
      
      responses[tabText] = panelText;
      console.log(panelText.substring(0, 500) + (panelText.length > 500 ? '...' : ''));
    } else {
      console.log(`Failed to click tab for ${tabText}`);
    }
  }

  // Save the extracted details to a file for analysis
  fs.writeFileSync('/tmp/extracted_task.json', JSON.stringify({ userRequest, responses }, null, 2));
  console.log('\nTask data successfully written to /tmp/extracted_task.json');

  await browser.disconnect();
}

main().catch(console.error);
