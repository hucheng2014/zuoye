const { chromium } = require('playwright');
const fs = require('fs');

async function main() {
  const cdpUrl = 'http://127.0.0.1:9235';
  console.log(`Connecting to CDP: ${cdpUrl}`);
  const browser = await chromium.connectOverCDP(cdpUrl);
  
  // Find the correct context and page
  const contexts = browser.contexts();
  let targetPage = null;
  
  for (const ctx of contexts) {
    const pages = ctx.pages();
    for (const p of pages) {
      const title = await p.title();
      const url = p.url();
      console.log(`Found page: Title: "${title}" | URL: "${url}"`);
      if (title.includes("WT Mail Smart Reply (MSR) Feedback_May22") || url.includes("Feedback%2FWT%20Mail")) {
        targetPage = p;
        break;
      }
    }
    if (targetPage) break;
  }
  
  if (!targetPage) {
    console.error("Target page not found!");
    await browser.close();
    process.exit(1);
  }
  
  console.log(`Target page matched: "${await targetPage.title()}"`);
  console.log("Setting up network monitoring on target page...");
  
  const intercepted = [];
  
  targetPage.on('response', async (response) => {
    const url = response.url();
    const headers = response.headers();
    const contentType = headers['content-type'] || '';
    const status = response.status();
    
    if (status === 200 && (
      contentType.includes('pdf') || 
      contentType.includes('octet-stream') || 
      url.includes('download') || 
      url.includes('pdf') ||
      url.includes('GetFile') ||
      url.includes('passthrough')
    )) {
      console.log(`[Intercepted] Status: ${status} | Type: ${contentType} | URL: ${url.slice(0, 150)}`);
      intercepted.push({
        url,
        contentType,
        responseObj: response
      });
    }
  });
  
  console.log("Reloading the target page to trigger network requests...");
  await targetPage.reload({ waitUntil: 'networkidle' });
  console.log("Waiting 15 seconds for PDF loading to settle...");
  await targetPage.waitForTimeout(15000);
  
  console.log(`Total intercepted matching responses: ${intercepted.length}`);
  
  let saved = false;
  for (let i = 0; i < intercepted.length; i++) {
    const r = intercepted[i];
    console.log(`Attempting to read body for response ${i}: ${r.contentType} | URL: ${r.url.slice(0, 100)}`);
    try {
      const buffer = await r.responseObj.body();
      console.log(`Successfully read body. Size: ${buffer.length} bytes.`);
      
      // Save all files with index so we don't lose anything
      const outPathIndexed = `/Users/xaa/zuoye/oneform/renzheng/MAIL/intercepted_${i}.bin`;
      fs.writeFileSync(outPathIndexed, buffer);
      console.log(`Saved response ${i} to ${outPathIndexed}`);

      // Save the real PDF (the large octet-stream from passthrough or pdf content-type)
      if ((r.contentType.includes('octet-stream') || r.contentType.includes('pdf')) && buffer.length > 100000) {
        const outPath = `/Users/xaa/zuoye/oneform/renzheng/MAIL/WT_Mail_Smart_Reply_MSR_Feedback_May22.pdf`;
        fs.writeFileSync(outPath, buffer);
        console.log(`Saved genuine PDF to ${outPath}`);
        saved = true;
      }
    } catch (e) {
      console.log(`Could not read response body: ${e.message}`);
    }
  }
  
  if (saved) {
    console.log("PDF successfully captured!");
  } else {
    console.log("Failed to capture PDF buffer.");
  }
  
  await browser.close();
}

main().catch(e => {
  console.error('Error in main:', e);
});
