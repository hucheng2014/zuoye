const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright-core');

const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const TARGET_URL = 'https://ilabel.weixin.qq.com/login';
const STATUS_PATH = path.join(__dirname, 'open_ilabel.status.json');

async function main() {
  const context = await chromium.launchPersistentContext(
    path.join(__dirname, 'edge-profile'),
    {
      headless: false,
      executablePath: EDGE_PATH,
      viewport: null,
      args: ['--new-window', '--start-maximized'],
    },
  );

  const existingPages = context.pages();
  const page = existingPages[0] || (await context.newPage());
  await page.bringToFront();
  await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: 120000 });

  fs.writeFileSync(
    STATUS_PATH,
    JSON.stringify(
      {
        ok: true,
        url: page.url(),
        title: await page.title(),
        openedAt: new Date().toISOString(),
      },
      null,
      2,
    ),
    'utf8',
  );

  await new Promise(() => {});
}

main().catch((error) => {
  fs.writeFileSync(
    STATUS_PATH,
    JSON.stringify(
      {
        ok: false,
        error: String(error && error.stack ? error.stack : error),
        failedAt: new Date().toISOString(),
      },
      null,
      2,
    ),
    'utf8',
  );
  process.exit(1);
});
