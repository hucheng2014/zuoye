require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  
  const frames = page.frames();
  const taskFrame = frames.find(f => f.url().includes('task-editor'));
  if (!taskFrame) { console.log('No task-editor frame'); await browser.close(); return; }
  
  const state = await taskFrame.evaluate(() => {
    // Get all visible buttons
    const buttons = [...document.querySelectorAll('button')].filter(b => b.offsetWidth > 0).map(b => ({
      text: b.innerText?.trim(),
      ariaLabel: b.getAttribute('aria-label'),
      disabled: b.disabled
    }));
    
    // Get control names to identify the task
    const radios = [...document.querySelectorAll('input[type="radio"]')];
    const controlNames = [...new Set(radios.map(r => r.name))];
    const checkedRadios = radios.filter(r => r.checked).map(r => r.name + '=' + r.value);
    
    // Get any progress indicators
    const allText = document.body.innerText.slice(0, 1000);
    
    return { buttons, controlNames, checkedRadios, allText };
  });
  console.log('State:', JSON.stringify(state, null, 2));
  
  await browser.close();
})().catch(e => console.error(e));
