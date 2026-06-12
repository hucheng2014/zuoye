/**
 * check_form.js — Verify the Intelligent Polls form is fully filled.
 *
 * Checks all visible radio groups to ensure every group has a selection.
 * Used after fill_task.js to verify completeness before submission.
 *
 * Usage:
 *   node scripts/check_form.js
 */

require('./_timeout');
const { chromium } = require('playwright');

const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';
const FALLBACK_CDP = 'http://127.0.0.1:9232';

async function main() {
  let browser;
  for (const ep of [CDP, FALLBACK_CDP]) {
    try { browser = await chromium.connectOverCDP(ep); break; } catch {}
  }
  if (!browser) throw new Error('No CDP endpoint available');

  try {
    const ctx = browser.contexts()[0];
    const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
    const frame = page.frames().find(f => f.url().includes('task-editor'));
    if (!frame) { console.log('No task-editor frame found.'); return; }

    // Dismiss dialog if present
    const dialog = page.locator('[aria-label="Task Overview"]');
    if (await dialog.count() > 0) {
      const startBtn = dialog.locator('button:has-text("Start")');
      if (await startBtn.count() > 0) {
        await startBtn.first().click({ timeout: 3000 });
        await page.waitForTimeout(500);
      }
    }

    // Get all visible radios
    const visible = await frame.locator('input[type="radio"]').evaluateAll(els =>
      els.filter(el => el.offsetParent !== null).map(el => ({
        name: el.name, value: el.value, checked: el.checked,
        label: (el.closest('label')?.innerText || '').trim().slice(0, 80),
      }))
    );

    // Group by name
    const groups = {};
    for (const v of visible) {
      if (!groups[v.name]) groups[v.name] = { checked: false, values: [], labels: [] };
      groups[v.name].values.push(v.value);
      groups[v.name].labels.push(v.label);
      if (v.checked) groups[v.name].checked = true;
    }

    console.log('=== FORM VALIDATION ===');
    let allGood = true;
    for (const [name, g] of Object.entries(groups)) {
      const status = g.checked ? '✅' : '❌';
      console.log(`${status} Group "${name}": checked=${g.checked} options=${JSON.stringify(g.values)}`);
      if (!g.checked) allGood = false;
    }

    // Check for validation errors
    const errors = await frame.locator('[class*="error"], [class*="validation-error"]').evaluateAll(els =>
      els.filter(el => el.offsetParent !== null).map(el => (el.innerText || '').trim().slice(0, 100)).filter(t => t)
    );
    if (errors.length) {
      console.log('\n❌ VALIDATION ERRORS:', errors);
      allGood = false;
    }

    // Check completion text
    const formText = await frame.locator('body').innerText({ timeout: 2000 }).catch(() => '');
    const completeMatch = formText.match(/(\d+\/\d+) Complete/);
    console.log(`\nCompletion status: ${completeMatch ? completeMatch[0] : 'Not found'}`);

    if (allGood) {
      console.log('\n✅ ALL RADIO GROUPS HAVE SELECTIONS — SAFE TO SUBMIT');
    } else {
      console.log('\n❌ INCOMPLETE FORM — DO NOT SUBMIT');
    }
  } finally {
    await browser.close();
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
