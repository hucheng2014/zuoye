const fs = require('fs');
const { chromium } = require('playwright-core');

const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

// Reuse the already-authenticated persistent profile that was created for iLabel work.
const USER_DATA_DIR = 'C:\\Users\\BERN7P\\codex-browser\\edge-profile-41393';

const TARGET_URL = 'https://ilabel.weixin.qq.com/mission/41398/label';
const STATUS_PATH = 'C:\\Users\\BERN7P\\codex-browser\\open_41398.status.json';

async function main() {
  const context = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless: false,
    executablePath: EDGE_PATH,
    viewport: null,
    args: ['--new-window', '--start-maximized'],
  });

  const page = context.pages()[0] || (await context.newPage());
  await page.bringToFront();
  await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: 120000 });
  await page.waitForTimeout(2500);

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

