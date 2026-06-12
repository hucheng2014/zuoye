#!/usr/bin/env node
/**
 * Fill form using React __reactProps.onChange directly.
 * Based on successful pattern from conversation history.
 */
const path = require('path');
const fs = require('fs');
const { getFrame, clickResponseTab } = require('./pr_automation_helper');
const { loadTaskFile, validateRatingsForTask } = require('./task_utils');
const { verifyFormSubmittableOn } = require('./verify_task');

const RUNS = path.join(__dirname, 'runs');
const FORM_FILLED = path.join(RUNS, 'form_filled.flag');

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

const RATING_VALUE_MAP = {
  'Not following': 'not_following_instructions',
  'Partially following': 'partially_following_instructions',
  'Fully following': 'following_instructions',
  'Yes (issues present)': 'issues',
  'No (no issues)': 'no_issues',
  Bad: 'bad',
  Acceptable: 'acceptable',
  Good: 'good',
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

const COMPARE_VALUE_MAP = {
  Same: 'A=B',
  'Left Much Better': 'A>>>B',
  'Left Better': 'A>>B',
  'Left Slightly Better': 'A>B',
  'Right Slightly Better': 'B>A',
  'Right Better': 'B>>A',
  'Right Much Better': 'B>>>A',
};

async function getResponseKeys(frm1) {
  return frm1.evaluate(() => {
    const tabs = [...document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')];
    return tabs.map(t => t.textContent.trim().replace(/^Complete\s+/, ''));
  });
}

async function getPanelIdForResponse(frm1, key) {
  return frm1.evaluate((text) => {
    const tabs = document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]');
    const tab = [...tabs].find(t => t.textContent.includes(text));
    return tab?.getAttribute('aria-controls') || null;
  }, key);
}

async function clickRadioReact(frm1, panelId, radioValue) {
  return frm1.evaluate((pid, val) => {
    // Find the __reactProps key
    const firstRadio = document.querySelector('input[type=radio]');
    if (!firstRadio) return { ok: false, error: 'no radio inputs at all' };
    const propsKey = Object.keys(firstRadio).find(k => k.startsWith('__reactProps') || k.startsWith('__reactFiber'));
    
    // Find the radio by value within the panel
    const panel = document.getElementById(pid);
    const radio = panel?.querySelector(`input[type=radio][value="${val}"]`);
    if (!radio) return { ok: false, error: `radio value="${val}" not found in panel ${pid}` };
    
    // Try __reactProps approach
    if (propsKey) {
      const props = radio[propsKey];
      if (props?.onChange) {
        const evt = {
          target: { value: val, checked: true, type: 'radio', name: radio.name },
          currentTarget: { value: val, checked: true, type: 'radio', name: radio.name },
          preventDefault: () => {},
          stopPropagation: () => {},
          nativeEvent: new Event('change'),
          type: 'change',
          persist: () => {},
        };
        props.onChange(evt);
        radio.checked = true;
        return { ok: true, method: '__reactProps' };
      }
    }
    
    // Try __reactFiber approach (alternate React internal)
    const fiberKey = Object.keys(radio).find(k => k.startsWith('__reactFiber'));
    if (fiberKey) {
      let fiber = radio[fiberKey];
      while (fiber) {
        if (fiber.memoizedProps?.onChange) {
          const evt = {
            target: { value: val, checked: true, type: 'radio', name: radio.name },
            currentTarget: { value: val, checked: true, type: 'radio', name: radio.name },
            preventDefault: () => {},
            stopPropagation: () => {},
            type: 'change',
            persist: () => {},
          };
          fiber.memoizedProps.onChange(evt);
          radio.checked = true;
          return { ok: true, method: '__reactFiber' };
        }
        fiber = fiber.return;
      }
    }
    
    // Fallback: click + dispatch native events
    radio.focus();
    radio.click();
    radio.dispatchEvent(new Event('change', { bubbles: true }));
    radio.dispatchEvent(new Event('input', { bubbles: true }));
    radio.checked = true;
    return { ok: true, method: 'native' };
  }, panelId, radioValue);
}

async function waitForDescriptionInPanel(frm1, panelId, timeoutMs = 8000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const found = await frm1.evaluate((pid) => {
      const panel = document.getElementById(pid);
      if (!panel) return false;
      const groups = [...panel.querySelectorAll('.radio-buttons, [role="radiogroup"]')];
      return groups.some(g => {
        const legend = g.querySelector('.legend')?.textContent || '';
        return /describe the response/i.test(legend);
      });
    }, panelId);
    if (found) return;
    await sleep(300);
  }
}

async function fillOneResponseReact(frm1, key, rData) {
  log(`=== Filling ${key} ===`);
  await clickResponseTab(frm1, key);
  await sleep(800);
  
  const panelId = await getPanelIdForResponse(frm1, key);
  log(`  Panel: ${panelId}`);
  
  const steps = [
    { cat: 'IF', val: RATING_VALUE_MAP[rData.instructionFollowing] },
    { cat: 'Localization', val: RATING_VALUE_MAP[rData.localization] },
    { cat: 'Concision', val: RATING_VALUE_MAP[rData.concision] },
  ];
  
  // Click IF, Localization, Concision first
  for (const s of steps) {
    if (!s.val) throw new Error(`${key}: no value for ${s.cat}`);
    const res = await clickRadioReact(frm1, panelId, s.val);
    log(`  ${s.cat}(${s.val}): ${res.ok ? 'OK' : res.error}`);
    await sleep(500);
  }
  
  // Wait for Description if needed
  if (rData.description) {
    log(`  Waiting for Description group...`);
    await waitForDescriptionInPanel(frm1, panelId);
    const descVal = RATING_VALUE_MAP[rData.description];
    const res = await clickRadioReact(frm1, panelId, descVal);
    log(`  Description(${descVal}): ${res.ok ? 'OK' : res.error}`);
    await sleep(500);
  }
  
  // Truthfulness
  const truthVal = RATING_VALUE_MAP[rData.truthfulness];
  const truthRes = await clickRadioReact(frm1, panelId, truthVal);
  log(`  Truthfulness(${truthVal}): ${truthRes.ok ? 'OK' : truthRes.error}`);
  await sleep(500);
  
  // Satisfaction
  const satVal = RATING_VALUE_MAP[rData.satisfaction];
  const satRes = await clickRadioReact(frm1, panelId, satVal);
  log(`  Satisfaction(${satVal}): ${satRes.ok ? 'OK' : satRes.error}`);
  await sleep(500);
  
  // Localization issues checkboxes
  if (rData.localization === 'Yes (issues present)' && rData.localizationIssues?.length) {
    for (const issue of rData.localizationIssues) {
      await frm1.evaluate((pid, issueText) => {
        const panel = document.getElementById(pid);
        const target = issueText.trim().toLowerCase();
        for (const cb of (panel || document).querySelectorAll('input[type=checkbox]')) {
          const lab = (cb.labels?.[0]?.textContent || '').trim().toLowerCase();
          if (lab === target && !cb.checked) cb.click();
        }
      }, panelId, issue);
      await sleep(300);
    }
  }
  
  log(`  ${key} done`);
}

async function fillCompareReact(frm1, ratings) {
  const compKeys = Object.keys(ratings.comparisons || {});
  for (const compKey of compKeys) {
    const rawVal = ratings.comparisons[compKey];
    if (!rawVal) continue;
    
    log(`=== Filling Compare: ${compKey} = ${rawVal} ===`);
    
    // Click Compare tab
    await frm1.evaluate(() => {
      const tabs = document.querySelectorAll('[role=tablist]')[1];
      const tab = tabs?.querySelector('[role=tab]');
      if (tab) tab.click();
    });
    await sleep(500);
    
    // Get compare panel ID
    const comparePanelId = await frm1.evaluate(() => {
      const tabs = document.querySelectorAll('[role=tablist]')[1];
      const sel = tabs?.querySelector('[role=tab][aria-selected=true]');
      return sel?.getAttribute('aria-controls');
    });
    log(`  Compare panel: ${comparePanelId}`);
    
    const domVal = COMPARE_VALUE_MAP[rawVal] || rawVal;
    const res = await clickRadioReact(frm1, comparePanelId, domVal);
    log(`  Compare(${domVal}): ${res.ok ? 'OK' : res.error}`);
    await sleep(500);
  }
}

async function fillRationaleReact(page, frm1, rationale) {
  log(`=== Filling Rationale ===`);
  
  // Click Compare tab first
  await frm1.evaluate(() => {
    const tabs = document.querySelectorAll('[role=tablist]')[1];
    const tab = tabs?.querySelector('[role=tab]');
    if (tab) tab.click();
  });
  await sleep(500);
  
  // Get textarea handle and type
  const textareaHandle = await frm1.evaluateHandle(() => {
    const ta = document.querySelector('textarea');
    if (ta) ta.scrollIntoView({ block: 'center', behavior: 'instant' });
    return ta;
  });
  
  if (textareaHandle?.asElement()) {
    // Select all and clear
    await textareaHandle.asElement().click({ clickCount: 3 });
    await sleep(200);
    await page.keyboard.press('Backspace');
    await sleep(300);
    
    // Type rationale
    await page.keyboard.type(rationale, { delay: 3 });
    log(`  Rationale typed (${rationale.length} chars)`);
  } else {
    // Fallback via evaluate
    await frm1.evaluate((text) => {
      const el = document.querySelector('textarea');
      if (!el) return;
      el.focus();
      el.value = text;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    }, rationale);
    log(`  Rationale set via evaluate (${rationale.length} chars)`);
  }
  
  await sleep(1000);
}

async function commitAndCheck(frm1, key, responseKeys) {
  // Switch to next tab to commit current
  const idx = responseKeys.indexOf(key);
  const nextKey = responseKeys[idx + 1];
  if (nextKey) {
    await clickResponseTab(frm1, nextKey);
    await sleep(1500);
  }
  
  // Check if tab shows "Complete"
  const states = await frm1.evaluate(() => {
    const tabs = [...document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')];
    return tabs.map(t => t.textContent.trim());
  });
  log(`  Tab states: ${JSON.stringify(states)}`);
  return states.some(s => s.includes(`Complete ${key}`));
}

async function main() {
  const ratings = JSON.parse(fs.readFileSync(path.join(__dirname, 'current_ratings.json'), 'utf8'));
  log(`fill start fingerprint=${ratings.fingerprint}`);
  
  const { browser, page, frm1 } = await getFrame();
  if (!frm1) {
    log('FATAL: task-editor frame not found');
    process.exit(1);
  }
  
  // Check if already complete
  const existing = await verifyFormSubmittableOn(page, frm1);
  if (existing.ok) {
    log(`form already complete ${JSON.stringify(existing.form)}`);
    await browser.disconnect();
    process.exit(0);
  }
  
  const responseKeys = await getResponseKeys(frm1);
  log(`Response keys: ${JSON.stringify(responseKeys)}`);
  
  // Fill each response
  for (const key of responseKeys) {
    const rData = ratings.responses[key];
    if (!rData) continue;
    
    // Check if already complete
    const states = await frm1.evaluate(() => {
      const tabs = [...document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')];
      return tabs.map(t => t.textContent.trim());
    });
    if (states.some(s => s.includes(`Complete ${key}`))) {
      log(`${key} already Complete — skip`);
      continue;
    }
    
    await fillOneResponseReact(frm1, key, rData);
    const ok = await commitAndCheck(frm1, key, responseKeys);
    if (!ok) {
      log(`WARN: ${key} commit may have failed, but continuing...`);
    }
  }
  
  // Fill Compare
  await fillCompareReact(frm1, ratings);
  
  // Fill Rationale
  if (ratings.rationale) {
    await fillRationaleReact(page, frm1, ratings.rationale);
  }
  
  // Final verification
  await sleep(2000);
  const result = await verifyFormSubmittableOn(page, frm1);
  log(`Final verify: ${JSON.stringify(result)}`);
  
  if (result.ok) {
    fs.mkdirSync(RUNS, { recursive: true });
    fs.writeFileSync(FORM_FILLED, JSON.stringify({
      fingerprint: ratings.fingerprint,
      at: new Date().toISOString(),
      form: result.form,
    }, null, 2));
    fs.writeFileSync(path.join(RUNS, 'submittable.flag'), new Date().toISOString());
    log('fill OK');
  } else {
    log(`FATAL: fill failed - ${result.issues?.join('; ')}`);
  }
  
  await browser.disconnect();
  process.exit(result.ok ? 0 : 1);
}

main().catch(e => {
  log(`FATAL: ${e.message}`);
  console.error(e);
  process.exit(1);
});
