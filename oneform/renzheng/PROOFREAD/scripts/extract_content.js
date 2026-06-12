require('./_timeout');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9233');
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];
  
  const frames = page.frames();
  const taskFrame = frames.find(f => f.url().includes('task-editor'));
  if (!taskFrame) { console.log('No task-editor frame'); await browser.close(); return; }
  
  // Extract input text
  const content = await taskFrame.evaluate(() => {
    // Find the input section
    const allText = document.body.innerText;
    return allText.slice(0, 2000);
  });
  console.log('Task text:', content);
  console.log('---');
  
  // Get the srcdoc frames for diff content
  const srcdocFrames = page.frames().filter(f => f.url() === 'about:srcdoc');
  console.log('Number of srcdoc frames:', srcdocFrames.length);
  
  for (let i = 0; i < srcdocFrames.length; i++) {
    const rawContent = await srcdocFrames[i].evaluate(() => {
      const raw = document.querySelector('#raw-content');
      const parsed = document.querySelector('#parsed-content');
      return { 
        raw: raw?.textContent?.trim(),
        parsed: parsed?.innerHTML?.slice(0, 500)
      };
    });
    console.log(`Frame ${i}:`, JSON.stringify(rawContent));
  }
  
  await browser.close();
})().catch(e => console.error(e));
