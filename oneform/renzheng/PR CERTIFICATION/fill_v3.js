#!/usr/bin/env node
/**
 * Fill form - correct version: JS tab click + ElementHandle radio click on visible panel only.
 */
const path = require('path');
const fs = require('fs');
const { getFrame } = require('./pr_automation_helper');
const { verifyFormSubmittableOn } = require('./verify_task');

const RUNS = path.join(__dirname, 'runs');

function log(msg) { console.log(`[${new Date().toISOString()}] ${msg}`); }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const ratings = JSON.parse(fs.readFileSync(path.join(__dirname, 'current_ratings.json'), 'utf8'));
  log(`fill start fingerprint=${ratings.fingerprint}`);
  
  const { browser, page, frm1 } = await getFrame();
  if (!frm1) { log('FATAL: no frame'); process.exit(1); }
  
  const existing = await verifyFormSubmittableOn(page, frm1);
  if (existing.ok) {
    log(`form already complete`);
    await browser.disconnect();
    process.exit(0);
  }
  
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

  const responseKeys = ['Response A', 'Response B'];
  
  for (const key of responseKeys) {
    const rData = ratings.responses[key];
    if (!rData) continue;
    
    log(`=== Filling ${key} ===`);
    
    // JS click to switch tab (works better than coordinate click)
    await frm1.evaluate((text) => {
      const tabs = document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]');
      [...tabs].find(t => t.textContent.includes(text))?.click();
    }, key);
    await sleep(800);
    
    // Get visible panel ID
    const panelId = await frm1.evaluate(() => {
      const panels = document.querySelectorAll('[role=tabpanel]');
      for (const p of panels) {
        if (getComputedStyle(p).display !== 'none') return p.id;
      }
      return null;
    });
    log(`  Panel: ${panelId}`);
    
    // Build radio values in correct order
    const radioVals = [
      VALUE_MAP[rData.instructionFollowing],
      VALUE_MAP[rData.localization],
      VALUE_MAP[rData.concision],
    ];
    // Wait for Description to appear, then add
    if (rData.description) {
      // First click concision, then wait for description
      await sleep(400);
      const descReady = await frm1.evaluate((pid) => {
        const panel = document.getElementById(pid);
        const groups = panel.querySelectorAll('.radio-buttons');
        return [...groups].some(g => /describe the response/i.test(g.querySelector('.legend')?.textContent || ''));
      }, panelId);
      if (descReady) {
        radioVals.push(VALUE_MAP[rData.description]);
      }
    }
    radioVals.push(VALUE_MAP[rData.truthfulness]);
    radioVals.push(VALUE_MAP[rData.satisfaction]);
    
    // Click each radio using ElementHandle
    for (const val of radioVals) {
      const handle = await frm1.evaluateHandle((pid, v) => {
        const panel = document.getElementById(pid);
        const radio = panel?.querySelector(`input[type=radio][value="${v}"]`);
        if (!radio) return null;
        const btn = radio.closest('.radio-button');
        if (btn && btn.offsetHeight > 0) {
          btn.scrollIntoView({ block: 'center', behavior: 'instant' });
          return btn;
        }
        const lbl = radio.closest('label');
        if (lbl && lbl.offsetHeight > 0) {
          lbl.scrollIntoView({ block: 'center', behavior: 'instant' });
          return lbl;
        }
        // If both offsetHeight=0, still return radio for React onChange call
        const propsKey = Object.keys(radio).find(k => k.startsWith('__reactProps'));
        if (propsKey && radio[propsKey]?.onChange) {
          const evt = {
            target: { value: v, checked: true, type: 'radio', name: radio.name },
            currentTarget: { value: v, checked: true, type: 'radio', name: radio.name },
            preventDefault: () => {}, stopPropagation: () => {},
            nativeEvent: new Event('change'), type: 'change', persist: () => {},
          };
          radio[propsKey].onChange(evt);
          radio.checked = true;
          return '__react_done__';
        }
        return radio; // fallback
      }, panelId, val);
      
      const el = handle?.asElement?.();
      if (el && el !== '__react_done__') {
        await el.click();
        log(`  ${val}: clicked`);
      } else if (el === '__react_done__') {
        log(`  ${val}: react`);
      } else {
        log(`  ${val}: NOT FOUND (trying __reactProps fallback)`);
        // Direct React onChange as last resort
        await frm1.evaluate((pid, v) => {
          const panel = document.getElementById(pid);
          const radio = panel?.querySelector(`input[type=radio][value="${v}"]`);
          if (!radio) return;
          const propsKey = Object.keys(radio).find(k => k.startsWith('__reactProps'));
          if (propsKey && radio[propsKey]?.onChange) {
            const evt = {
              target: { value: v, checked: true, type: 'radio', name: radio.name },
              currentTarget: { value: v, checked: true, type: 'radio', name: radio.name },
              preventDefault: () => {}, stopPropagation: () => {},
              nativeEvent: new Event('change'), type: 'change', persist: () => {},
            };
            radio[propsKey].onChange(evt);
            radio.checked = true;
          }
        }, panelId, val);
      }
      await sleep(400);
    }
    
    // Check tab state
    await sleep(1000);
    const states = await frm1.evaluate(() => {
      const tabs = document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]');
      return [...tabs].map(t => t.textContent.trim());
    });
    log(`  Tab states: ${JSON.stringify(states)}`);
  }
  
  // Fill Compare
  log(`=== Filling Compare ===`);
  const compVal = ratings.comparisons?.['A and B'];
  if (compVal) {
    // Switch to Compare tab via JS
    await frm1.evaluate(() => {
      const tabs = document.querySelectorAll('[role=tablist]')[1];
      tabs?.querySelector('[role=tab]')?.click();
    });
    await sleep(500);
    
    const compDomVal = { Same: 'A=B' }[compVal] || compVal;
    const comparePanelId = await frm1.evaluate(() => {
      const tabs = document.querySelectorAll('[role=tablist]')[1];
      const sel = tabs?.querySelector('[role=tab][aria-selected=true]');
      return sel?.getAttribute('aria-controls');
    });
    
    const handle = await frm1.evaluateHandle((pid, v) => {
      const panel = document.getElementById(pid);
      const radio = panel?.querySelector(`input[type=radio][value="${v}"]`);
      const btn = radio?.closest('.radio-button');
      if (btn && btn.offsetHeight > 0) { btn.scrollIntoView({ block: 'center' }); return btn; }
      return radio?.closest('label') || radio;
    }, comparePanelId, compDomVal);
    
    const el = handle?.asElement?.();
    if (el) {
      await el.click();
      log(`  ${compDomVal}: clicked`);
    }
    await sleep(500);
  }
  
  // Fill Rationale
  if (ratings.rationale) {
    log(`=== Filling Rationale ===`);
    await frm1.evaluate(() => {
      const tabs = document.querySelectorAll('[role=tablist]')[1];
      tabs?.querySelector('[role=tab]')?.click();
    });
    await sleep(500);
    
    const taHandle = await frm1.evaluateHandle(() => {
      const ta = document.querySelector('textarea');
      if (ta) ta.scrollIntoView({ block: 'center', behavior: 'instant' });
      return ta;
    });
    
    if (taHandle?.asElement()) {
      await taHandle.asElement().click({ clickCount: 3 });
      await sleep(200);
      await page.keyboard.press('Backspace');
      await sleep(300);
      await page.keyboard.type(ratings.rationale, { delay: 2 });
      log(`  Rationale typed (${ratings.rationale.length} chars)`);
    }
    await sleep(1000);
  }
  
  // Final verify
  await sleep(2000);
  const result = await verifyFormSubmittableOn(page, frm1);
  log(`Final: ${JSON.stringify(result)}`);
  
  if (result.ok) {
    fs.mkdirSync(RUNS, { recursive: true });
    fs.writeFileSync(path.join(RUNS, 'form_filled.flag'), JSON.stringify({
      fingerprint: ratings.fingerprint, at: new Date().toISOString(), form: result.form,
    }, null, 2));
    fs.writeFileSync(path.join(RUNS, 'submittable.flag'), new Date().toISOString());
    log('fill OK');
  } else {
    log(`Issues: ${result.issues?.join('; ')}`);
  }
  
  await browser.disconnect();
  process.exit(result.ok ? 0 : 1);
}

main().catch(e => { log(`FATAL: ${e.message}`); console.error(e); process.exit(1); });
