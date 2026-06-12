require('./_timeout');
const { chromium } = require('playwright');

const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function clickAndForce(frame, selector) {
  return frame.evaluate((sel) => {
    const el = document.querySelector(sel);
    if (!el) return { ok: false, reason: 'not_found', sel };
    el.focus();
    el.click();
    const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'checked').set;
    nativeSetter.call(el, true);
    el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
    el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    return { ok: !!el.checked, name: el.name, value: el.value, checked: el.checked };
  }, selector);
}

(async () => {
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  const frame = page.frames().find(f => f.url().includes('task-editor'));
  if (!frame) throw new Error('task-editor frame not found');

  // 1) Switch to Response A
  await frame.evaluate(() => {
    const tab = Array.from(document.querySelectorAll('[role="tab"]')).find(t => t.textContent.includes('Response A'));
    if (tab) tab.click();
  });
  await page.waitForTimeout(600);

  // 2) Ensure q1 is has_grammar_errors (page-level)
  await clickAndForce(frame, 'input[type="radio"][value="has_grammar_errors"]');
  await page.waitForTimeout(200);

  // 3) For Response A q2 group, explicitly target by first visible q2 name if possible
  const groupInfo = await frame.evaluate(() => {
    const visibleQ2 = Array.from(document.querySelectorAll('input[type="radio"][value="no_edits"]'))
      .find(r => r.offsetParent !== null);
    if (visibleQ2) return { name: visibleQ2.name, mode: 'visible' };
    const fallback = document.querySelector('input[type="radio"][value="no_edits"]');
    return fallback ? { name: fallback.name, mode: 'fallback' } : null;
  });

  if (!groupInfo) throw new Error('no no_edits radio found');

  const sel = `input[type=\"radio\"][name=\"${groupInfo.name}\"][value=\"no_edits\"]`;
  const res = await clickAndForce(frame, sel);

  await page.waitForTimeout(500);

  const verify = await frame.evaluate((name) => {
    const vals = Array.from(document.querySelectorAll(`input[type="radio"][name="${name}"]`)).map(r => ({
      value: r.value,
      checked: r.checked,
      visible: r.offsetParent !== null
    }));
    return vals;
  }, groupInfo.name);

  console.log(JSON.stringify({ groupInfo, res, verify }, null, 2));
})();
