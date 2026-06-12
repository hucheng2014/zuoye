/** 自动关闭常见阻断弹窗 */
async function dismissPopups(page, logger) {
  const log = logger || (() => {});

  // Disclaimer
  const disclaimer = page.locator('div[role="dialog"]', { hasText: /Disclaimer/i });
  if (await disclaimer.count()) {
    const accept = disclaimer.locator('button', { hasText: /^Accept$/i }).first();
    if (await accept.isVisible().catch(() => false)) {
      await accept.click({ timeout: 3000 }).catch(() => {});
      log('Dismissed Disclaimer dialog (Accept)');
      await page.waitForTimeout(1500);
    }
  }

  // Generic Accept on any visible dialog
  const dialogs = page.locator('div[role="dialog"]');
  const n = await dialogs.count();
  for (let i = 0; i < n; i++) {
    const dlg = dialogs.nth(i);
    if (!(await dlg.isVisible().catch(() => false))) continue;
    for (const label of ['Accept', 'OK', 'Got it', 'Close', 'Dismiss']) {
      const btn = dlg.locator('button', { hasText: new RegExp(`^${label}$`, 'i') }).first();
      if (await btn.isVisible().catch(() => false)) {
        await btn.click({ timeout: 2000 }).catch(() => {});
        log(`Dismissed dialog via "${label}"`);
        await page.waitForTimeout(1000);
        break;
      }
    }
  }
}

module.exports = { dismissPopups };
