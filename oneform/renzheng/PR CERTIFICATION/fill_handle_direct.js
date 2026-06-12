#!/usr/bin/env node
/**
 * Fill form using ElementHandle.click() on .radio-button elements.
 * Skips offsetHeight check for satisfaction radios.
 * Based on successful pattern from conversation (line ~10500).
 */
const path = require('path');
const fs = require('fs');
const { getFrame, clickResponseTab } = require('./pr_automation_helper');
const { verifyFormSubmittableOn } = require('./verify_task');

const RUNS = path.join(__dirname, 'runs');

function log(msg) { console.log(`[${new Date().toISOString()}] ${msg}`); }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function getResponseKeys(frm1) {
  return frm1.evaluate(() => {
    const tabs = [...document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')];
    return tabs.map(t => t.textContent.trim().replace(/^Complete\s+/, ''));
  });
}

async function fillOneViaElementHandle(frm1, key, rMap) {
  log(`=== Filling ${key} ===`);
  await clickResponseTab(frm1, key);
  await sleep(800);
  
  const radioValues = Object.values(rMap);
  for (const val of radioValues) {
    // Get ElementHandle for .radio-button, no offsetHeight check
    const handle = await frm1.evaluateHandle((v) => {
      // Search in all visible tabpanels
      const panels = document.querySelectorAll('[role=tabpanel]');
      for (const panel of panels) {
        if (getComputedStyle(panel).display === 'none') continue;
        const radio = panel.querySelector(`input[type=radio][value="${v}"]`);
        if (!radio) continue;
        const btn = radio.closest('.radio-button');
        if (btn) {
          btn.scrollIntoView({ block: 'center', behavior: 'instant' });
          return btn;
        }
        // Fallback: return the input itself wrapped in label
        const lbl = radio.closest('label');
        if (lbl) {
          lbl.scrollIntoView({ block: 'center', behavior: 'instant' });
          return lbl;
        }
        return radio;
      }
      return null;
    }, val);
    
    const el = handle?.asElement?.();
    if (el) {
      await el.click();
      log(`  ${val}: OK`);
    } else {
      log(`  ${val}: NOT FOUND`);
    }
    await sleep(400);
  }
  await sleep(500);
}

async function fillCompareViaElementHandle(frm1, compVal) {
  log(`=== Filling Compare: ${compVal} ===`);
  
  // Click Compare tab
  const handle_tab = await frm1.evaluateHandle(() => {
    const tabs = document.querySelectorAll('[role=tablist]')[1];
    const tab = tabs?.querySelector('[role=tab]');
    if (tab) tab.click();
    return tab;
  });
  await sleep(500);
  await handle_tab?.dispose?.();
  
  // Click the comparison radio
  const compDomVal = ({
    Same: 'A=B',
    'Left Much Better': 'A>>>B', 'Left Better': 'A>>B', 'Left Slightly Better': 'A>B',
    'Right Slightly Better': 'B>A', 'Right Better': 'B>>A', 'Right Much Better': 'B>>>A',
  })[compVal] || compVal;
  
  const handle = await frm1.evaluateHandle((v) => {
    const panels = document.querySelectorAll('[role=tabpanel]');
    for (const panel of panels) {
      if (getComputedStyle(panel).display === 'none') continue;
      const radio = panel.querySelector(`input[type=radio][value="${v}"]`);
      if (!radio) continue;
      const btn = radio.closest('.radio-button');
      if (btn) { btn.scrollIntoView({ block: 'center' }); return btn; }
      return radio.closest('label') || radio;
    }
    return null;
  }, compDomVal);
  
  const el = handle?.asElement?.();
  if (el) {
    await el.click();
    log(`  ${compDomVal}: OK`);
  } else {
    log(`  ${compDomVal}: NOT FOUND`);
  }
  await sleep(500);
}

async function fillRationaleViaElementHandle(page, frm1, rationale) {
  log(`=== Filling Rationale ===`);
  
  // Click Compare tab
  await frm1.evaluate(() => {
    const tabs = document.querySelectorAll('[role=tablist]')[1];
    const tab = tabs?.querySelector('[role=tab]');
    if (tab) tab.click();
  });
  await sleep(500);
  
  const textareaHandle = await frm1.evaluateHandle(() => {
    const ta = document.querySelector('textarea');
    if (ta) ta.scrollIntoView({ block: 'center', behavior: 'instant' });
    return ta;
  });
  
  if (textareaHandle?.asElement()) {
    await textareaHandle.asElement().click({ clickCount: 3 });
    await sleep(200);
    await page.keyboard.press('Backspace');
    await sleep(300);
    await page.keyboard.type(rationale, { delay: 2 });
    log(`  Rationale typed (${rationale.length} chars)`);
  }
  await sleep(1000);
}

async function main() {
  const ratings = JSON.parse(fs.readFileSync(path.join(__dirname, 'current_ratings.json'), 'utf8'));
  log(`fill start fingerprint=${ratings.fingerprint}`);
  
  const { browser, page, frm1 } = await getFrame();
  if (!frm1) { log('FATAL: no frame'); process.exit(1); }
  
  // Check if already complete
  const existing = await verifyFormSubmittableOn(page, frm1);
  if (existing.ok) {
    log(`form already complete ${JSON.stringify(existing.form)}`);
    await browser.disconnect();
    process.exit(0);
  }
  
  const responseKeys = await getResponseKeys(frm1);
  log(`Response keys: ${JSON.stringify(responseKeys)}`);
  
  const VALUE_MAP = {
    'Not following': 'not_following_instructions',
    'Partially following': 'partially_following_instructions',
    'Fully following': 'following_instructions',
    'Yes (issues present)': 'issues',
    'No (no issues)': 'no_issues',
    Bad: 'bad', Acceptable: 'acceptable', Good: 'good',
    'It could have been made shorter': 'make_shorter',
    'It could have been made longer': 'make_longer',
    'Not Truthful': 'not_truthful',
    'Partially Truthful': 'partially_truthful',
    Truthful: 'truthful',
    'Highly Unsatisfying': 'not_satisfying',
    'Slightly Unsatisfying': 'slightly_unsatisfying',
    'Slightly Satisfying': 'satisfying',
    'Highly Satisfying': 'highly_satisfying',
  };
  
  for (const key of responseKeys) {
    const rData = ratings.responses[key];
    if (!rData) continue;
    
    // Build value map for this response
    const rMap = {
      IF: VALUE_MAP[rData.instructionFollowing],
      localization: VALUE_MAP[rData.localization],
      concision: VALUE_MAP[rData.concision],
      truthfulness: VALUE_MAP[rData.truthfulness],
      satisfaction: VALUE_MAP[rData.satisfaction],
    };
    if (rData.description) {
      rMap.description = VALUE_MAP[rData.description];
    }
    
    await fillOneViaElementHandle(frm1, key, rMap);
    
    // Commit: switch to next tab
    const idx = responseKeys.indexOf(key);
    const nextKey = responseKeys[idx + 1];
    if (nextKey) {
      await clickResponseTab(frm1, nextKey);
      await sleep(1000);
    }
  }
  
  // Fill Compare
  const compKeys = Object.keys(ratings.comparisons || {});
  for (const ck of compKeys) {
    await fillCompareViaElementHandle(frm1, ratings.comparisons[ck]);
  }
  
  // Fill Rationale
  if (ratings.rationale) {
    await fillRationaleViaElementHandle(page, frm1, ratings.rationale);
  }
  
  // Final verify
  await sleep(2000);
  const result = await verifyFormSubmittableOn(page, frm1);
  log(`Final: ${JSON.stringify(result)}`);
  
  if (result.ok) {
    fs.mkdirSync(RUNS, { recursive: true });
    fs.writeFileSync(path.join(RUNS, 'form_filled.flag'), JSON.stringify({
      fingerprint: ratings.fingerprint,
      at: new Date().toISOString(),
      form: result.form,
    }, null, 2));
    fs.writeFileSync(path.join(RUNS, 'submittable.flag'), new Date().toISOString());
    log('fill OK');
  } else {
    log(`FATAL: ${result.issues?.join('; ')}`);
  }
  
  await browser.disconnect();
  process.exit(result.ok ? 0 : 1);
}

main().catch(e => { log(`FATAL: ${e.message}`); console.error(e); process.exit(1); });
