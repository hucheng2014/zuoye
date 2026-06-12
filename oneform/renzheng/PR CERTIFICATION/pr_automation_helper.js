const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const { CDP_URL, CDP_FALLBACK, DELAY } = require('./config');
const {
  extractTaskFromPuppeteerFrame,
  getResponseKeys,
} = require('./task_utils');
const { verifyFormSubmittableOn, verifyBeforeSubmitOn } = require('./verify_task');

async function connectBrowser() {
  for (const url of [CDP_URL, CDP_FALLBACK]) {
    try {
      return await puppeteer.connect({ browserURL: url, defaultViewport: null });
    } catch (e) {
      if (url === CDP_FALLBACK) throw e;
    }
  }
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/** Scroll task-editor inner container to top so radio Y coords are positive. */
async function scrollTaskEditorToResponses(frm1) {
  await frm1.evaluate(() => {
    const container = document.querySelector('.Box-sc-18eybku-0.autPh') ||
      [...document.querySelectorAll('*')].find((el) => el.scrollHeight > el.clientHeight + 50);
    if (container) {
      container.scrollTop = 0;
      container.scrollTo?.({ top: 0, behavior: 'instant' });
    }
    const tablist = document.querySelectorAll('[role=tablist]')[0];
    tablist?.scrollIntoView({ block: 'start', behavior: 'instant' });
    const panel = tablist?.querySelector('[role=tab][aria-selected=true]');
    const panelId = panel?.getAttribute('aria-controls');
    const firstRadio = panelId
      ? document.getElementById(panelId)?.querySelector('.radio-buttons, [role=radiogroup]')
      : null;
    firstRadio?.scrollIntoView({ block: 'start', behavior: 'instant' });
  });
  await sleep(500);
}

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

async function getPanelIdForResponse(frm1, key) {
  return frm1.evaluate((text) => {
    const tab = [...document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')].find(
      (t) => t.textContent.trim() === text || t.textContent.trim() === `Complete ${text}`
    );
    return tab?.getAttribute('aria-controls') || null;
  }, key);
}

/** Trigger React onChange on a radio inside a specific tab panel (reliable per field testing). */
async function clickRadioInPanelReact(frm1, panelId, radioValue) {
  return frm1.evaluate((pid, val) => {
    const propsKey = Object.keys(document.querySelector('input[type=radio]') || {}).find((k) =>
      k.startsWith('__reactProps')
    );
    if (!propsKey) return { ok: false, error: 'no __reactProps key' };
    const panel = document.getElementById(pid);
    const radio = panel?.querySelector(`input[type=radio][value="${val}"]`);
    if (!radio) return { ok: false, error: `radio ${val} not in panel ${pid}` };
    const props = radio[propsKey];
    if (!props?.onChange) return { ok: false, error: `no onChange for ${val}` };
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
    return { ok: true };
  }, panelId, radioValue);
}

async function waitForDescriptionInPanel(frm1, panelId) {
  await frm1.waitForFunction(
    (pid) => {
      const panel = document.getElementById(pid);
      if (!panel) return false;
      return [...panel.querySelectorAll('.radio-buttons, [role=radiogroup]')].some((g) => {
        const legend = g.querySelector('.legend')?.textContent || '';
        return /describe the response/i.test(legend) && g.querySelectorAll('input[type=radio]').length > 0;
      });
    },
    { timeout: 8000 },
    panelId
  ).catch(() => {});
  await sleep(400);
}

async function clickAtFramePoint(frm1, x, y) {
  const page = frm1.page();
  const frameEl = await frm1.frameElement();
  const fbox = frameEl ? await frameEl.boundingBox() : null;
  if (!fbox) throw new Error('task-editor frame has no bounding box');
  const clickX = fbox.x + x;
  const clickY = fbox.y + y;
  console.log(`[clickAtFramePoint] iframe=(${fbox.x},${fbox.y},${fbox.width},${fbox.height}) el=(${x},${y}) click=(${clickX},${clickY})`);
  await page.mouse.click(clickX, clickY);
}

async function getResponseTabStates(frm1) {
  return frm1.evaluate(() => {
    const tabs = [...document.querySelectorAll('[role=tablist]')[0].querySelectorAll('[role=tab]')];
    const out = {};
    for (const t of tabs) {
      const text = t.textContent.trim();
      if (/response a/i.test(text)) out['Response A'] = text;
      else if (/response b/i.test(text)) out['Response B'] = text;
      else if (/response c/i.test(text)) out['Response C'] = text;
    }
    return out;
  });
}

function isResponseTabComplete(tabText) {
  return /^Complete\s+Response\s+/i.test(String(tabText || ''));
}

async function waitForResponseTabComplete(frm1, key, timeoutMs = 10000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const states = await getResponseTabStates(frm1);
    if (isResponseTabComplete(states[key])) return true;
    await sleep(300);
  }
  return false;
}

/** Leave current response tab to commit — use next response tab or compare tab, never go backward. */
async function commitResponseTab(frm1, key, responseKeys) {
  const idx = responseKeys.indexOf(key);
  const nextKey = responseKeys[idx + 1];
  if (nextKey) {
    await clickResponseTab(frm1, nextKey);
    return;
  }
  // Click compare tab with real mouse
  const page = frm1.page();
  const frameEl = await frm1.frameElement();
  const fbox = frameEl ? await frameEl.boundingBox() : null;
  if (fbox) {
    const pos = await frm1.evaluate(() => {
      const compareList = document.querySelectorAll('[role=tablist]')[1];
      const tab = compareList?.querySelector('[role=tab]');
      if (!tab) return null;
      tab.scrollIntoView({ block: 'center', behavior: 'instant' });
      const r = tab.getBoundingClientRect();
      return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
    });
    if (pos) {
      await page.mouse.click(fbox.x + pos.x, fbox.y + pos.y);
    }
  } else {
    await frm1.evaluate(() => {
      const compareList = document.querySelectorAll('[role=tablist]')[1];
      const tab = compareList?.querySelector('[role=tab]');
      if (tab) tab.click();
    });
  }
  await sleep(DELAY.tab);
}

// Connect to browser and get the task editor frame
async function getFrame() {
  const browser = await connectBrowser();

  const pages = await browser.pages();
  const page = pages.find((p) => p.url().includes('starshot')) || pages[0];
  await dismissDisclaimer(page).catch(() => {});
  const frames = page.frames();
  // Find the frame that has 'task-editor' in its URL
  const frm1 = frames.find(f => f.url().includes('task-editor'));

  return { browser, page, frm1 };
}

// Dismiss top-level Disclaimer / enrollment dialogs on starshot page
async function dismissDisclaimer(page) {
  return page.evaluate(() => {
    const visible = (el) => el && el.offsetParent !== null;
    for (const btn of document.querySelectorAll('button,[role=button]')) {
      if (!visible(btn)) continue;
      if (/^accept$/i.test(btn.textContent.trim())) {
        const ctx = (btn.closest('dialog,[role=dialog]')?.textContent || document.body.innerText || '');
        if (/disclaimer|enroll|privacy/i.test(ctx)) {
          btn.click();
          return true;
        }
      }
    }
    return false;
  });
}

// Check for ACCEPT button and click it if present
async function checkAndAccept() {
  const { browser, page, frm1 } = await getFrame();
  await dismissDisclaimer(page).catch(() => {});
  if (!frm1) {
    console.error('Task editor frame not found');
    await browser.disconnect();
    return false;
  }

  const clicked = await frm1.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const acceptBtn = buttons.find(b => b.textContent.toUpperCase().includes('ACCEPT'));
    if (acceptBtn && acceptBtn.offsetParent !== null) {
      acceptBtn.click();
      return true;
    }
    return false;
  });

  await browser.disconnect();
  return clicked;
}

// Extract current task content
async function extractTask() {
  const { browser, frm1 } = await getFrame();
  if (!frm1) {
    throw new Error('Task editor frame not found');
  }
  const task = await extractTaskFromPuppeteerFrame(frm1, 500);
  await browser.disconnect();
  return task;
}

// Click a radio button based on current visible labels and EXACT label text match
async function clickRadioByLabel(frm1, categoryName, targetLabel, opts = {}) {
  const scopeMode = opts.scope || 'active-tabpanel';
  const found = await frm1.evaluate((cat, target, scopeMode) => {
    const root = (() => {
      if (scopeMode === 'document') return document;
      if (scopeMode === 'compare-panel') {
        const compareList = [...document.querySelectorAll('[role=tablist]')].find(
          (tl) => [...tl.querySelectorAll('[role=tab]')].some((t) => /and/i.test(t.textContent))
        );
        const cTab = compareList?.querySelector('[role=tab][aria-selected=true]') ||
          compareList?.querySelector('[role=tab]');
        const cPanelId = cTab?.getAttribute('aria-controls');
        if (cPanelId) {
          const p = document.getElementById(cPanelId);
          if (p) return p;
        }
        const panel = [...document.querySelectorAll('[role=tabpanel]')].find(
          (p) => /compare responses/i.test(p.textContent)
        );
        return panel || document;
      }
      // response-panel: panel tied to selected response tab via aria-controls
      const respList = document.querySelectorAll('[role=tablist]')[0];
      const rTab = respList?.querySelector('[role=tab][aria-selected=true]') ||
        respList?.querySelector('[role=tab]');
      const rPanelId = rTab?.getAttribute('aria-controls');
      if (rPanelId) {
        const p = document.getElementById(rPanelId);
        if (p) return p;
      }
      const panel = [...document.querySelectorAll('[role=tabpanel]')].find(
        (p) => p.offsetHeight > 0 && !/compare responses/i.test(p.textContent)
      );
      return panel || document;
    })();
    const groups = Array.from(root.querySelectorAll('.radio-buttons, [role="radiogroup"]')).filter(g => {
      const style = window.getComputedStyle(g);
      return style.display !== 'none' && style.visibility !== 'hidden' && g.offsetHeight > 0;
    });

    for (const group of groups) {
      const legend = group.querySelector('.legend')?.textContent || '';
      let matchesCategory = false;

      if (cat === 'IF' && legend.toLowerCase().includes('instructions')) matchesCategory = true;
      else if (cat === 'Localization' && legend.toLowerCase().includes('localization')) matchesCategory = true;
      else if (cat === 'Concision' && legend.toLowerCase().includes('concise')) matchesCategory = true;
      else if (cat === 'Truthfulness' && legend.toLowerCase().includes('truthful')) matchesCategory = true;
      else if (cat === 'Satisfaction' && legend.toLowerCase().includes('satisfying')) matchesCategory = true;
      else if (cat === 'Comparison' && legend.toLowerCase().includes('compare responses')) matchesCategory = true;
      else if (cat === 'Description' && legend.toLowerCase().includes('describe the response')) matchesCategory = true;

      if (matchesCategory) {
        const valueMap = {
          'not following': 'not_following_instructions',
          'partially following': 'partially_following_instructions',
          'fully following': 'following_instructions',
          'yes (issues present)': 'issues',
          'no (no issues)': 'no_issues',
          'bad': 'bad',
          'acceptable': 'acceptable',
          'good': 'good',
          'it could have been made shorter': 'make_shorter',
          'it could have been made longer': 'make_longer',
          'not truthful': 'not_truthful',
          'partially truthful': 'partially_truthful',
          'truthful': 'truthful',
          'highly unsatisfying': 'not_satisfying',
          'slightly unsatisfying': 'slightly_unsatisfying',
          'slightly satisfying': 'satisfying',
          'highly satisfying': 'highly_satisfying',
          'same': 'A=B',
          'left much better': 'A>>>B',
          'left better': 'A>>B',
          'left slightly better': 'A>B',
          'right slightly better': 'B>A',
          'right better': 'B>>A',
          'right much better': 'B>>>A',
        };
        const targetStr = target.trim().toLowerCase();
        const wantValue = valueMap[targetStr];
        if (wantValue) {
          const radio = group.querySelector(`input[type="radio"][value="${wantValue}"]`);
          if (radio) {
            // Prefer the visible .radio-button div over hidden label/input
            const visBtn = radio.closest('.radio-button');
            const label = radio.closest('label') || group.querySelector(`label[for="${radio.id}"]`);
            const el = (visBtn && visBtn.offsetHeight > 0) ? visBtn : (label && label.offsetHeight > 0) ? label : radio;
            const rect = el.getBoundingClientRect();
            return {
              success: true,
              legend,
              clickedLabel: target,
              forId: radio.id || null,
              x: rect.left + rect.width / 2,
              y: rect.top + rect.height / 2,
            };
          }
        }
        const labels = Array.from(group.querySelectorAll('label'));
        for (const label of labels) {
          const text = label.textContent.trim().toLowerCase();
          let isMatch = (text === targetStr);
          if (!isMatch && cat === 'Satisfaction') {
            isMatch = text.endsWith(targetStr);
          }
          if (isMatch) {
            const radio = label.querySelector('input[type="radio"]') || document.getElementById(label.getAttribute('for'));
            if (radio) {
              const rect = label.getBoundingClientRect();
              return {
                success: true,
                legend,
                clickedLabel: label.textContent.trim(),
                forId: radio.id || null,
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2,
              };
            }
          }
        }
      }
    }
    return { success: false, error: `Could not find radio in ${cat} with exact label matching "${target}"` };
  }, categoryName, targetLabel, scopeMode);

  if (!found.success) return found;
  if (scopeMode === 'active-tabpanel' || scopeMode === 'response-panel') {
    await scrollTaskEditorToResponses(frm1);
  }
  const pt = await frm1.evaluate((cat, target, scopeMode) => {
    const pick = (el, legend, clickedLabel) => {
      if (!el) return null;
      el.scrollIntoView({ block: 'center', behavior: 'instant' });
      const r = el.getBoundingClientRect();
      return {
        success: true,
        legend,
        clickedLabel,
        x: r.left + r.width / 2,
        y: r.top + r.height / 2,
      };
    };
    const root = (() => {
      if (scopeMode === 'compare-panel') {
        const compareList = document.querySelectorAll('[role=tablist]')[1];
        const cTab = compareList?.querySelector('[role=tab][aria-selected=true]') ||
          compareList?.querySelector('[role=tab]');
        const pid = cTab?.getAttribute('aria-controls');
        return pid ? document.getElementById(pid) : document;
      }
      const rTab = document.querySelectorAll('[role=tablist]')[0]?.querySelector('[role=tab][aria-selected=true]');
      const pid = rTab?.getAttribute('aria-controls');
      return pid ? document.getElementById(pid) : document;
    })();
    const valueMap = {
      'not following': 'not_following_instructions',
      'partially following': 'partially_following_instructions',
      'fully following': 'following_instructions',
      'yes (issues present)': 'issues',
      'no (no issues)': 'no_issues',
      bad: 'bad',
      acceptable: 'acceptable',
      good: 'good',
      'it could have been made shorter': 'make_shorter',
      'it could have been made longer': 'make_longer',
      'not truthful': 'not_truthful',
      'partially truthful': 'partially_truthful',
      truthful: 'truthful',
      'highly unsatisfying': 'not_satisfying',
      'slightly unsatisfying': 'slightly_unsatisfying',
      'slightly satisfying': 'satisfying',
      'highly satisfying': 'highly_satisfying',
      same: 'A=B',
      'left much better': 'A>>>B',
      'left better': 'A>>B',
      'left slightly better': 'A>B',
      'right slightly better': 'B>A',
      'right better': 'B>>A',
      'right much better': 'B>>>A',
    };
    const targetStr = target.trim().toLowerCase();
    const wantValue = valueMap[targetStr];
    const groups = [...root.querySelectorAll('.radio-buttons, [role="radiogroup"]')].filter((g) => g.offsetHeight > 0);
    for (const group of groups) {
      const legend = group.querySelector('.legend')?.textContent || '';
      let match = false;
      if (cat === 'IF' && /instructions/i.test(legend)) match = true;
      else if (cat === 'Localization' && /localization/i.test(legend)) match = true;
      else if (cat === 'Concision' && /concise/i.test(legend)) match = true;
      else if (cat === 'Truthfulness' && /truthful/i.test(legend)) match = true;
      else if (cat === 'Satisfaction' && /satisfying/i.test(legend)) match = true;
      else if (cat === 'Comparison' && /compare responses/i.test(legend)) match = true;
      else if (cat === 'Description' && /describe the response/i.test(legend)) match = true;
      if (!match) continue;
      if (wantValue) {
        const radio = group.querySelector(`input[type=radio][value="${wantValue}"]`);
        // Prefer visible .radio-button div over hidden label/input
        const visBtn = radio?.closest('.radio-button');
        const lbl = radio?.closest('label');
        const el = (visBtn && visBtn.offsetHeight > 0) ? visBtn : (lbl && lbl.offsetHeight > 0) ? lbl : radio;
        const hit = pick(el, legend, target);
        if (hit) return hit;
      }
      for (const label of group.querySelectorAll('label')) {
        const text = label.textContent.trim().toLowerCase();
        let isMatch = text === targetStr;
        if (!isMatch && cat === 'Satisfaction') isMatch = text.endsWith(targetStr);
        if (isMatch) {
          // Prefer visible .radio-button parent
          const visBtn = label.closest('.radio-button');
          const el = (visBtn && visBtn.offsetHeight > 0) ? visBtn : label;
          const hit = pick(el, legend, label.textContent.trim());
          if (hit) return hit;
        }
      }
    }
    return { success: false, error: `no click point for ${cat}` };
  }, categoryName, targetLabel, scopeMode);
  if (!pt.success) return pt;
  // Chat log fix: scroll container must be at top or Y is negative and clicks miss.
  if (pt.y < 5 && (scopeMode === 'active-tabpanel' || scopeMode === 'response-panel')) {
    await scrollTaskEditorToResponses(frm1);
    const pt2 = await frm1.evaluate((cat, target, scopeMode) => {
      const pick = (el, legend, clickedLabel) => {
        if (!el) return null;
        el.scrollIntoView({ block: 'center', behavior: 'instant' });
        const r = el.getBoundingClientRect();
        return { success: true, legend, clickedLabel, x: r.left + r.width / 2, y: r.top + r.height / 2 };
      };
      const rTab = document.querySelectorAll('[role=tablist]')[0]?.querySelector('[role=tab][aria-selected=true]');
      const pid = rTab?.getAttribute('aria-controls');
      const root = pid ? document.getElementById(pid) : document;
      const valueMap = { 'fully following': 'following_instructions', 'partially following': 'partially_following_instructions', 'no (no issues)': 'no_issues', bad: 'bad', acceptable: 'acceptable', 'it could have been made shorter': 'make_shorter', truthful: 'truthful', 'slightly satisfying': 'satisfying', same: 'A=B' };
      const wantValue = valueMap[target.trim().toLowerCase()];
      const groups = [...root.querySelectorAll('.radio-buttons, [role=radiogroup]')].filter((g) => g.offsetHeight > 0);
      for (const group of groups) {
        const legend = group.querySelector('.legend')?.textContent || '';
        let match = false;
        if (cat === 'IF' && /instructions/i.test(legend)) match = true;
        else if (cat === 'Localization' && /localization/i.test(legend)) match = true;
        else if (cat === 'Concision' && /concise/i.test(legend)) match = true;
        else if (cat === 'Truthfulness' && /truthful/i.test(legend)) match = true;
        else if (cat === 'Satisfaction' && /satisfying/i.test(legend)) match = true;
        else if (cat === 'Comparison' && /compare responses/i.test(legend)) match = true;
        else if (cat === 'Description' && /describe the response/i.test(legend)) match = true;
        if (!match) continue;
        if (wantValue) {
          const radio = group.querySelector(`input[type=radio][value="${wantValue}"]`);
          const visBtn = radio?.closest('.radio-button');
          const el = visBtn?.offsetHeight > 0 ? visBtn : radio?.closest('label') || radio;
          const hit = pick(el, legend, target);
          if (hit) return hit;
        }
      }
      return { success: false, error: `no click point after scroll for ${cat}` };
    }, categoryName, targetLabel, scopeMode);
    if (pt2.success) Object.assign(pt, pt2);
  }
  if (pt.y < 5) {
    return { success: false, error: `radio off-screen y=${pt.y} cat=${categoryName} label=${targetLabel}` };
  }
  // Chat log fix (08:22): ONLY clickAtFramePoint — ElementHandle clicks miss React state.
  await clickAtFramePoint(frm1, pt.x, pt.y);
  await sleep(DELAY.radio);
  return { success: true, method: 'clickAtFramePoint', legend: pt.legend, clickedLabel: pt.clickedLabel, x: pt.x, y: pt.y };
}

async function clickResponseTab(frm1, key) {
  // Use real mouse click via page.mouse for React compatibility
  const page = frm1.page();
  const frameEl = await frm1.frameElement();
  const fbox = frameEl ? await frameEl.boundingBox() : null;
  if (fbox) {
    const pos = await frm1.evaluate((text) => {
      const respList = document.querySelectorAll('[role=tablist]')[0];
      const tab = respList && [...respList.querySelectorAll('[role=tab]')].find(
        (t) => t.textContent.trim() === text || t.textContent.trim() === `Complete ${text}`
      );
      if (!tab) return null;
      tab.scrollIntoView({ block: 'center', behavior: 'instant' });
      const r = tab.getBoundingClientRect();
      return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
    }, key);
    if (pos) {
      await page.mouse.click(fbox.x + pos.x, fbox.y + pos.y);
    }
  } else {
    // Fallback to JS click
    await frm1.evaluate((text) => {
      const respList = document.querySelectorAll('[role=tablist]')[0];
      const tab = respList && [...respList.querySelectorAll('[role=tab]')].find(
        (t) => t.textContent.trim() === text || t.textContent.trim() === `Complete ${text}`
      );
      if (tab) { tab.click(); tab.dispatchEvent(new Event('click', { bubbles: true })); }
    }, key);
  }
  for (let i = 0; i < 10; i++) {
    const sel = await frm1.evaluate((text) => {
      const tab = document.querySelectorAll('[role=tablist]')[0]?.querySelector('[role=tab][aria-selected=true]');
      const t = tab?.textContent?.trim() || '';
      return t === text || t === `Complete ${text}`;
    }, key);
    if (sel) break;
    await sleep(200);
  }
  await sleep(300);
}

const RADIO_VALUE_MAP = {
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

async function fillOneResponse(frm1, key, rData) {
  await clickResponseTab(frm1, key);
  await scrollTaskEditorToResponses(frm1);
  const panelId = await getPanelIdForResponse(frm1, key);
  if (!panelId) throw new Error(`${key}: no panel id`);

  const steps = [
    ['IF', rData.instructionFollowing],
    ['Localization', rData.localization],
    ['Concision', rData.concision],
    rData.description ? ['Description', rData.description] : null,
    ['Truthfulness', rData.truthfulness],
    ['Satisfaction', rData.satisfaction],
  ].filter(Boolean);

  for (const [cat, label] of steps) {
    if (cat === 'Description') {
      await waitForDescriptionInPanel(frm1, panelId);
    }
    const radioVal = RATING_VALUE_MAP[label];
    if (!radioVal) throw new Error(`${key}: unknown label "${label}"`);
    // Primary: real mouse via clickAtFramePoint (chat log fix). Fallback: React onChange.
    const clicked = await clickRadioByLabel(frm1, cat, label, { scope: 'active-tabpanel' });
    if (!clicked.success) {
      const res = await clickRadioInPanelReact(frm1, panelId, radioVal);
      if (!res.ok) throw new Error(`${key}: ${cat} "${label}" failed: ${clicked.error}; ${res.error}`);
    }
    console.log(`[fillOneResponse] ${key} ${cat}=${label} (${radioVal})`);
    await sleep(DELAY.radio);
  }
  if (rData.localization === 'Yes (issues present)' && rData.localizationIssues?.length) {
    for (const issue of rData.localizationIssues) {
      await frm1.evaluate((issueText) => {
        const tab = document.querySelectorAll('[role=tablist]')[0]?.querySelector('[role=tab][aria-selected=true]');
        const panel = tab ? document.getElementById(tab.getAttribute('aria-controls')) : null;
        const target = issueText.trim().toLowerCase();
        for (const cb of (panel || document).querySelectorAll('input[type=checkbox]')) {
          const lab = (cb.labels?.[0]?.textContent || '').trim().toLowerCase();
          if (lab === target && !cb.checked) cb.click();
        }
      }, issue);
      await sleep(DELAY.radio);
    }
  }
}

async function fillResponseRatings(frm1, ratings, opts = {}) {
  const logFn = opts.log || console.log;
  const responseKeys = getResponseKeys({ responses: ratings.responses });

  for (const key of responseKeys) {
    const states = await getResponseTabStates(frm1);
    if (isResponseTabComplete(states[key])) {
      logFn(`${key} already Complete — skip`);
      continue;
    }
    const rData = ratings.responses[key];
    if (!rData) continue;
    logFn(`Rating ${key}...`);
    await fillOneResponse(frm1, key, rData);
    // Commit by moving forward only (A→B→Compare). Never click back to A after B.
    await commitResponseTab(frm1, key, responseKeys);
    const committed = await waitForResponseTabComplete(frm1, key, 12000);
    logFn(`${key} commit: ${committed ? 'Complete' : 'pending'} (tab=${(await getResponseTabStates(frm1))[key]})`);
  }
}

async function fillCompareAndRationale(frm1, ratings) {
  const compKeys = Object.keys(ratings.comparisons || {});
  for (const rawCompKey of compKeys) {
    const rawVal = ratings.comparisons[rawCompKey];
    if (!rawVal) continue;
    console.log(`Processing comparison for key: "${rawCompKey}" with value: "${rawVal}"`);
    const matchResult = await frm1.evaluate((keyText) => {
      const tabs = Array.from(document.querySelectorAll('[role=tab], button')).map((t) => t.textContent.trim());
      const keyParts = keyText.toUpperCase().split(/\s+and\s+/i);
      if (keyParts.length !== 2) return { success: false, error: `Invalid key format: ${keyText}` };
      const k0 = keyParts[0].trim();
      const k1 = keyParts[1].trim();
      let matchedTabText = null;
      for (const tabText of tabs) {
        const tUpper = tabText.toUpperCase();
        if (tUpper.includes(k0) && tUpper.includes(k1) && tUpper.includes('AND')) {
          matchedTabText = tabText;
          break;
        }
      }
      if (!matchedTabText) return { success: false, error: `No matching tab for ${keyText}` };
      const tabParts = matchedTabText.toUpperCase().split(/\s+and\s+/i);
      const isReversed = keyParts[0].trim() !== tabParts[0].trim();
      const tabEl = [...document.querySelectorAll('[role=tab], button')].find((t) => t.textContent.trim() === matchedTabText);
      if (tabEl) { tabEl.click(); return { success: true, isReversed }; }
      return { success: false, error: 'click failed' };
    }, rawCompKey);
    if (!matchResult.success) throw new Error(`Comparison tab ${rawCompKey}: ${matchResult.error}`);
    let val = rawVal.trim();
    if (matchResult.isReversed) {
      if (rawVal.startsWith('Left')) val = rawVal.replace('Left', 'Right');
      else if (rawVal.startsWith('Right')) val = rawVal.replace('Right', 'Left');
    }
    const comparePanelId = await frm1.evaluate(() => {
      const tab = document.querySelectorAll('[role=tablist]')[1]?.querySelector('[role=tab]');
      return tab?.getAttribute('aria-controls') || null;
    });
    const domVal = COMPARE_VALUE_MAP[val] || val;
    let compOk = false;
    if (comparePanelId) {
      const r = await clickRadioInPanelReact(frm1, comparePanelId, domVal);
      compOk = r.ok;
    }
    if (!compOk) {
      const res = await clickRadioByLabel(frm1, 'Comparison', val, { scope: 'compare-panel' });
      if (!res.success) throw new Error(`Comparison ${rawCompKey} failed: ${res.error}`);
    }
    await sleep(DELAY.comp);
  }
  if (!ratings.rationale) return;
  const filled = await frm1.evaluate((text) => {
    const isRationale = (el) => {
      if (el.placeholder?.includes('Describe your task')) return false;
      const block = el.closest('div[class]')?.parentElement?.textContent || '';
      return block.includes('reasons for your gradings') || block.includes('gradings');
    };
    let el = [...document.querySelectorAll('textarea')].find(isRationale);
    if (!el) el = document.querySelector('textarea:not([placeholder*="Describe your task"])');
    if (!el) return { ok: false, len: 0 };
    el.scrollIntoView({ block: 'center' });
    const propsKey = Object.keys(el).find((k) => k.startsWith('__reactProps'));
    if (propsKey && el[propsKey]?.onChange) {
      const evt = {
        target: { value: text },
        currentTarget: { value: text },
        preventDefault: () => {},
        stopPropagation: () => {},
        nativeEvent: new Event('input'),
        type: 'input',
        persist: () => {},
      };
      el[propsKey].onChange(evt);
    } else {
      const native = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value');
      native?.set?.call(el, text);
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    }
    return { ok: true, len: el.value.length };
  }, ratings.rationale);
  console.log('Rationale filled:', filled);
  if (!filled.ok || filled.len < 50) {
    const sel = await frm1.evaluate(() => {
      const el = [...document.querySelectorAll('textarea')].find((t) => !t.placeholder?.includes('Describe your task'));
      return el ? `#${el.id}` || 'textarea' : null;
    });
    if (sel) { await frm1.focus(sel); await frm1.type(sel, ratings.rationale, { delay: 0 }); }
  }
  await sleep(DELAY.rationale);
}

// Fill all ratings (no submit)
async function fillRatings(frm1, ratings) {
  if (!frm1) throw new Error('Task editor frame not found');
  await fillResponseRatings(frm1, ratings);
  await fillCompareAndRationale(frm1, ratings);
}

function responsesComplete(form) {
  const t = form.responsesExpected != null ? `${form.responsesExpected}/${form.responsesExpected}` : null;
  return t && form.responsesComplete === t;
}

/**
 * Fill form + re-check until submittable (responses/compare/rationale/Submit ready).
 * Retries fill on incomplete sections — does NOT click Submit.
 */
async function fillAndVerifySubmittable(page, frm1, ratings, opts = {}) {
  const maxAttempts = opts.maxAttempts || 3;
  const logFn = opts.log || ((msg) => console.log(msg));
  const runsDir = path.join(__dirname, 'runs');
  fs.mkdirSync(runsDir, { recursive: true });
  let last = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    logFn(`[fill-verify] attempt ${attempt}/${maxAttempts} — responses first`);
    await fillResponseRatings(frm1, ratings, { log: logFn });
    await sleep(opts.settleMs || 1500);
    last = await verifyFormSubmittableOn(page, frm1);
    if (responsesComplete(last.form)) {
      await fillCompareAndRationale(frm1, ratings);
      await sleep(800);
      last = await verifyFormSubmittableOn(page, frm1);
    }
    if (last.ok) {
      logFn(`[fill-verify] OK ${JSON.stringify(last.form)}`);
      fs.writeFileSync(path.join(runsDir, 'submittable.flag'), new Date().toISOString());
      return { ok: true, attempt, form: last.form };
    }
    logFn(`[fill-verify] incomplete: ${last.issues.join('; ')}`);
    await sleep(800);
  }

  try { fs.unlinkSync(path.join(runsDir, 'submittable.flag')); } catch {}
  return { ok: false, issues: last?.issues || ['fill-verify failed'], form: last?.form };
}

/** Full pre-submit gate: file ratings + TPT + form submittable. */
async function assertReadyToSubmit(page, frm1, ratings) {
  const fillResult = await fillAndVerifySubmittable(page, frm1, ratings);
  if (!fillResult.ok) {
    return { ok: false, stage: 'form', issues: fillResult.issues, form: fillResult.form };
  }
  const pre = await verifyBeforeSubmitOn(page, frm1, { skipRatings: true });
  if (!pre.ok) {
    return { ok: false, stage: 'pre-submit', issues: pre.issues, form: pre.form, tpt: pre.tpt };
  }
  return { ok: true, form: pre.form, tpt: pre.tpt, attempts: fillResult.attempt };
}

// Submit + confirm + next task
async function finalizeSubmit(browser, page, frm1) {
  if (!frm1) throw new Error('Task editor frame not found');

  // 4. Click Submit (only when valid)
  console.log('Clicking SUBMIT...');
  const submitClicked = await frm1.evaluate(() => {
    const btn = document.querySelector('.submit-button') || Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Submit');
    if (!btn || btn.disabled || btn.textContent.includes('Invalid')) return { ok: false, label: btn?.textContent?.trim() };
    btn.click();
    return { ok: true, label: btn.textContent.trim() };
  });
  console.log('Submit button:', submitClicked);
  if (!submitClicked.ok) {
    throw new Error(`Cannot submit: ${submitClicked.label || 'button not ready'}`);
  }
  await sleep(DELAY.submit);

  // 5. Handle confirmation modal (iframe + top page)
  console.log('Handling confirmation modal...');
  const confirmFn = `(() => {
    const roots = [document, ...Array.from(document.querySelectorAll('iframe')).map(f => { try { return f.contentDocument; } catch(e) { return null; } }).filter(Boolean)];
    for (const doc of roots) {
      const modals = Array.from(doc.querySelectorAll('div, section, dialog')).filter(el => el.textContent.includes('Do you want to submit'));
      if (modals.length) {
        const modal = modals[modals.length - 1];
        const submitBtn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.trim() === 'Submit');
        if (submitBtn) { submitBtn.click(); return true; }
      }
      const vis = Array.from(doc.querySelectorAll('button')).filter(b => b.textContent.trim() === 'Submit' && b.offsetParent !== null);
      for (const b of vis) {
        const ctx = b.closest('div,section,dialog')?.textContent || '';
        if (ctx.includes('Do you want to submit')) { b.click(); return true; }
      }
    }
    return false;
  })()`;
  // 确认弹窗常在 starshot 顶层，优先点顶层 Submit
  let confirmed = await page.evaluate(() => {
    const body = document.body.innerText;
    if (!/do you want to submit/i.test(body)) return false;
    const btn = [...document.querySelectorAll('button,[role=button]')].find(
      (b) => b.textContent.trim() === 'Submit' && b.offsetParent
    );
    if (btn) { btn.click(); return true; }
    return false;
  });
  if (!confirmed) confirmed = await page.evaluate(confirmFn);
  if (!confirmed) confirmed = await frm1.evaluate(confirmFn);
  if (!confirmed) {
    for (let i = 0; i < 8 && !confirmed; i++) {
      await sleep(500);
      confirmed = await page.evaluate(() => {
        const btn = [...document.querySelectorAll('button,[role=button]')].find(
          (b) => b.textContent.trim() === 'Submit' && b.offsetParent &&
            /do you want to submit/i.test(document.body.innerText)
        );
        if (btn) { btn.click(); return true; }
        return false;
      });
      if (!confirmed) confirmed = await page.evaluate(confirmFn);
      if (!confirmed) confirmed = await frm1.evaluate(confirmFn);
    }
  }
  await sleep(DELAY.confirm);

  // 6. Click NEXT TASK
  console.log('Clicking NEXT TASK...');
  let nextClicked = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button, div[role="button"], a'));
    const nextBtn = buttons.find(b => {
      const t = b.textContent.trim().toLowerCase();
      return t === 'next task' || t.includes('next task') || t === 'next';
    });
    if (nextBtn && nextBtn.offsetParent !== null) {
      nextBtn.click();
      return true;
    }
    return false;
  });
  if (!nextClicked) {
    nextClicked = await frm1.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button, div[role="button"], a'));
      const nextBtn = buttons.find(b => {
        const t = b.textContent.trim().toLowerCase();
        return t === 'next task' || t.includes('next task') || t === 'next';
      });
      if (nextBtn && nextBtn.offsetParent !== null) { nextBtn.click(); return true; }
      return false;
    });
  }
  await sleep(DELAY.next);

  // Signal watchdog to restart keepalive for next task
  const runsDir = path.join(__dirname, 'runs');
  fs.mkdirSync(runsDir, { recursive: true });
  fs.writeFileSync(path.join(runsDir, 'submitted.flag'), new Date().toISOString());
  try { fs.unlinkSync(path.join(runsDir, 'ready.flag')); } catch {}

  return { success: true, nextClicked, confirmed };
}

async function submitRatings(ratings) {
  const { browser, page, frm1 } = await getFrame();
  if (!frm1) throw new Error('Task editor frame not found');
  const ready = await assertReadyToSubmit(page, frm1, ratings);
  if (!ready.ok) {
    throw new Error(`${ready.stage || 'pre-submit'}: ${(ready.issues || []).join('; ')}`);
  }
  const result = await finalizeSubmit(browser, page, frm1);
  await browser.disconnect();
  return result;
}

module.exports = {
  dismissDisclaimer,
  checkAndAccept,
  extractTask,
  fillRatings,
  fillAndVerifySubmittable,
  assertReadyToSubmit,
  finalizeSubmit,
  submitRatings,
  sleep,
  getFrame,
  scrollTaskEditorToResponses,
  clickRadioByLabel,
  clickResponseTab,
};
