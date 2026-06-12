require('./_timeout');
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const DOWNLOAD_DIR = '/Users/xaa/zuoye/oneform/renzheng/PROOFREAD/runs/downloads';

// Ensure download directory exists
if (!fs.existsSync(DOWNLOAD_DIR)) {
  fs.mkdirSync(DOWNLOAD_DIR, { recursive: true });
}

async function downloadFolderFiles(page, folderName, folderPath) {
  const baseUrl = "https://digitaltechedge.sharepoint.com/sites/IsaacLighthouse/Isaac%20Lighthouse/Forms/AllItems.aspx";
  const targetUrl = `${baseUrl}?id=${encodeURIComponent(folderPath)}`;
  
  console.log(`\n========================================`);
  console.log(`Processing Folder: ${folderName}`);
  console.log(`URL: ${targetUrl}`);
  console.log(`========================================`);
  
  await page.goto(targetUrl);
  await page.waitForTimeout(5000); // Wait for rows to load

  // Get list of file names from the page
  const fileNames = await page.evaluate(() => {
    const list = [];
    const rows = document.querySelectorAll('[role="row"]');
    rows.forEach(row => {
      const text = row.innerText.trim();
      const firstLine = text.split('\n')[0].trim();
      if (firstLine && firstLine !== "Name" && !firstLine.includes("Modified")) {
        list.push(firstLine);
      }
    });
    return list;
  });

  console.log(`Found files in ${folderName}:`, fileNames);

  // Filter out any video files (.mp4) and directory headers or empty items
  const filesToDownload = fileNames.filter(name => {
    const lower = name.toLowerCase();
    if (lower.endsWith('.mp4')) return false;
    if (lower === 'recording sessions' || lower === 'feedback' || lower === 'guidelines') return false;
    return true;
  });

  console.log(`Files to download (excluding videos):`, filesToDownload);

  for (const filename of filesToDownload) {
    console.log(`\nStarting download for: "${filename}"`);
    
    // Clear selection by reloading/navigating to ensure clean state
    await page.goto(targetUrl);
    await page.waitForTimeout(4000);

    // Locate the row for this file
    const row = page.locator('[role="row"]').filter({ hasText: filename });
    const checkbox = row.locator('[data-automationid="selection-checkbox"]');
    
    try {
      // Force click checkbox
      await checkbox.click({ force: true });
      console.log(`  Selected checkbox for "${filename}"`);
      await page.waitForTimeout(2000);

      // Set up download event listener
      console.log(`  Clicking Download button in toolbar...`);
      const downloadPromise = page.waitForEvent('download', { timeout: 15000 });
      
      // Click download button
      const downloadButton = page.locator('button:has-text("Download"), [title="Download"], [aria-label="Download"], [data-automationid="downloadCommand"]').first();
      await downloadButton.click();
      
      const download = await downloadPromise;
      const savePath = path.join(DOWNLOAD_DIR, filename);
      await download.saveAs(savePath);
      console.log(`  SUCCESS: Downloaded "${filename}" to ${savePath}`);
    } catch (e) {
      console.error(`  ERROR: Failed to download "${filename}":`, e.message);
      
      // Take screenshot of failure for debugging
      const failScreenshot = path.join(DOWNLOAD_DIR, `fail_${filename.replace(/[^a-z0-9]/gi, '_')}.png`);
      await page.screenshot({ path: failScreenshot });
      console.log(`  Saved failure screenshot to ${failScreenshot}`);
    }
  }
}

async function main() {
  const cdpUrl = 'http://127.0.0.1:9235';
  console.log(`Connecting to CDP: ${cdpUrl}`);
  const browser = await chromium.connectOverCDP(cdpUrl);
  const context = browser.contexts()[0];
  const page = context.pages()[0];

  const baseFolder = "/sites/IsaacLighthouse/Isaac Lighthouse/TC Guidelines/TA Proofread";
  
  // 1. Download files in Guidelines folder
  await downloadFolderFiles(page, "Guidelines", `${baseFolder}/Guidelines`);
  
  // 2. Download files in Feedback folder
  await downloadFolderFiles(page, "Feedback", `${baseFolder}/Feedback`);

  console.log("\n========================================");
  console.log("All downloads completed!");
  console.log("========================================");

  await browser.close();
}

main().catch(e => {
  console.error('Fatal Error:', e);
});
