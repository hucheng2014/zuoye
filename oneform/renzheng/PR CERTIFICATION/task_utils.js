/**
 * Task fingerprinting + stale-ratings guards for PR Certification.
 * Copy pattern from TAMESSAGE/scripts/task_utils.js — refuse submit on mismatch.
 */
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const RUNS = path.join(ROOT, 'runs');
const TASK_FILE = path.join(ROOT, 'current_task.json');
const RATINGS_FILE = path.join(ROOT, 'current_ratings.json');
const ACTIVE_FP_FILE = path.join(RUNS, 'active-fingerprint.txt');
const GRADING_LOCK = path.join(RUNS, 'grading.lock');
const NEEDS_GRADING = path.join(RUNS, 'needs_grading.flag');

const IF_LABELS = new Set(['Not following', 'Partially following', 'Fully following']);
const LOC_LABELS = new Set(['Yes (issues present)', 'No (no issues)']);
const CONCISION_LABELS = new Set(['Bad', 'Acceptable', 'Good']);
const TRUTH_LABELS = new Set(['Not Truthful', 'Partially Truthful', 'Truthful']);
const SAT_LABELS = new Set([
  'Highly Unsatisfying',
  'Slightly Unsatisfying',
  'Slightly Satisfying',
  'Highly Satisfying',
]);
const COMP_LABELS = new Set([
  'Left Much Better', 'Left Better', 'Left Slightly Better', 'Same',
  'Right Slightly Better', 'Right Better', 'Right Much Better',
]);
const DESC_LABELS = new Set(['It could have been made shorter', 'It could have been made longer']);
const LOC_ISSUE_LABELS = new Set([
  'Unlocalized information',
  'Overly-localized content',
  'Spelling',
  'Tone',
  'Non-local perspective',
  'Vocabulary',
  'Awkward or unnatural writing',
  'Formatting & punctuation',
  'Grammar',
  'Phrase or idiom',
  'Units of measurement',
  'Wrong language',
  'Other',
]);

function ensureRuns() {
  fs.mkdirSync(RUNS, { recursive: true });
}

function cleanText(t) {
  return (t || '').replace(/\u00a0/g, ' ').trim();
}

function normalizeUserRequest(text) {
  const t = cleanText(text);
  const userIdx = t.indexOf('User\n');
  let slice = userIdx >= 0 ? t.slice(userIdx) : t;
  const end = slice.search(/\nPredicted Category:|\nResponses\n|\nRESPONSES\n|Does the response follow|🤖️ Response/);
  slice = end > 0 ? slice.slice(0, end) : slice;
  return cleanText(slice).slice(0, 2000);
}

/** Strip chars that break JSON/API proxies when embedded in LLM prompts */
function sanitizeForPrompt(text, maxLen = 2800) {
  return String(text || '')
    .replace(/\u0000/g, '')
    .replace(/[\uD800-\uDFFF]/g, '')
    .replace(/\\/g, '＼')
    .slice(0, maxLen);
}

function normalizeResponseBody(text) {
  let t = cleanText(text);
  if (t.includes('Does the response follow')) {
    t = t.split('Does the response follow')[0];
  }
  const idx = t.indexOf('🤖️ Response');
  if (idx >= 0) t = t.slice(idx);
  return cleanText(t);
}

/** Canonical comparison key: "B and A" → "A and B" */
function comparisonTabToKey(tabLabel) {
  const m = String(tabLabel || '').match(/([ABC])\s+and\s+([ABC])/i);
  if (!m) return null;
  const letters = [m[1].toUpperCase(), m[2].toUpperCase()].sort();
  return `${letters[0]} and ${letters[1]}`;
}

function getResponseKeys(task) {
  if (Array.isArray(task?.responseKeys) && task.responseKeys.length) {
    return task.responseKeys;
  }
  const fromObj = Object.keys(task?.responses || {})
    .filter((k) => /^Response [ABC]$/i.test(k))
    .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
  if (fromObj.length) return fromObj;
  return ['Response A', 'Response B', 'Response C'];
}

function getResponseLetters(task) {
  return getResponseKeys(task).map((k) => k.replace(/^Response\s+/i, '').trim());
}

function getComparisonPairsFromTask(task) {
  if (Array.isArray(task?.comparisonKeys) && task.comparisonKeys.length) {
    return task.comparisonKeys;
  }
  const letters = getResponseLetters(task);
  const pairs = [];
  for (let i = 0; i < letters.length; i++) {
    for (let j = i + 1; j < letters.length; j++) {
      pairs.push(`${letters[i]} and ${letters[j]}`);
    }
  }
  return pairs;
}

/** Run inside task-editor frame to detect 2- or 3-response layout. */
function detectLayoutInFrame() {
  const text = document.body.innerText;
  const respTotalM = text.match(/RESPONSES\s*\d+\/(\d+)\s*Complete/i);
  const cmpTotalM = text.match(/Compare\s*\d+\/(\d+)\s*Complete/i);
  const allTabs = [...document.querySelectorAll('[role="tab"]')].map((t) => t.textContent.trim());
  const responseTabs = allTabs.filter((t) => /^Response [ABC]$/i.test(t));
  const comparisonTabs = allTabs.filter((t) => /^[ABC]\s+and\s+[ABC]$/i.test(t));
  const responseCount = responseTabs.length || parseInt(respTotalM?.[1] || '0', 10) || 3;
  const comparisonCount = comparisonTabs.length || parseInt(cmpTotalM?.[1] || '0', 10) || (
    responseCount === 2 ? 1 : 3
  );
  return {
    responseCount,
    comparisonCount,
    responseTabs,
    comparisonTabs,
    comparisonKeys: comparisonTabs.map((t) => {
      const m = t.match(/([ABC])\s+and\s+([ABC])/i);
      if (!m) return null;
      const letters = [m[1].toUpperCase(), m[2].toUpperCase()].sort();
      return `${letters[0]} and ${letters[1]}`;
    }).filter(Boolean),
  };
}

function cleanPanelText(panelText) {
  let cleaned = panelText || '';
  if (cleaned.includes('Does the response follow')) {
    cleaned = cleaned.split('Does the response follow')[0];
  }
  if (cleaned.includes('🤖️ Response')) {
    cleaned = cleaned.substring(cleaned.indexOf('🤖️ Response'));
  }
  return cleanText(cleaned);
}

function fingerprintFromTask(task) {
  const keys = getResponseKeys(task);
  const payload = [
    task.locale || '',
    String(keys.length),
    normalizeUserRequest(task.userRequest),
    ...keys.map((k) => normalizeResponseBody(task.responses?.[k])),
  ].join('|||');
  return crypto.createHash('sha256').update(payload).digest('hex').slice(0, 16);
}

function enrichTask(task) {
  const fp = fingerprintFromTask(task);
  return {
    ...task,
    fingerprint: fp,
    extractedAt: task.extractedAt || new Date().toISOString(),
  };
}

function saveTask(task) {
  ensureRuns();
  const enriched = enrichTask(task);
  const prevFp = readActiveFingerprint();
  fs.writeFileSync(TASK_FILE, JSON.stringify(enriched, null, 2));
  fs.writeFileSync(ACTIVE_FP_FILE, enriched.fingerprint);
  if (prevFp && prevFp !== enriched.fingerprint) {
    invalidateRatings(`new task fingerprint ${enriched.fingerprint} (was ${prevFp})`);
    fs.writeFileSync(NEEDS_GRADING, enriched.fingerprint);
  }
  return enriched;
}

function readActiveFingerprint() {
  try {
    return fs.readFileSync(ACTIVE_FP_FILE, 'utf8').trim() || null;
  } catch {
    return null;
  }
}

function loadTaskFile() {
  if (!fs.existsSync(TASK_FILE)) return null;
  return JSON.parse(fs.readFileSync(TASK_FILE, 'utf8'));
}

function loadRatingsFile() {
  if (!fs.existsSync(RATINGS_FILE)) return null;
  return JSON.parse(fs.readFileSync(RATINGS_FILE, 'utf8'));
}

function invalidateRatings(reason) {
  ensureRuns();
  if (fs.existsSync(RATINGS_FILE)) {
    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
    const dest = path.join(RUNS, `stale_ratings_${stamp}.json`);
    fs.renameSync(RATINGS_FILE, dest);
  }
  try { fs.unlinkSync(path.join(RUNS, 'ready.flag')); } catch {}
  if (reason) {
    fs.appendFileSync(path.join(RUNS, 'stale_guard.log'), `[${new Date().toISOString()}] INVALIDATED: ${reason}\n`);
  }
}

const RATIONALE_DIM_CHECKS = [
  { key: 'instructionFollowing', patterns: [/instruction\s+following/i, /following\s+instructions/i] },
  { key: 'localization', patterns: [/localization/i] },
  { key: 'concision', patterns: [/concision/i] },
  { key: 'truthfulness', patterns: [/truthfulness/i] },
  { key: 'satisfaction', patterns: [/satisfaction/i] },
];

/** Extract per-response rationale blocks after "RESPONSE X:" headers. */
function extractRationaleBlocks(rationale) {
  const text = String(rationale || '').trim();
  const blocks = {};
  for (const letter of ['A', 'B', 'C']) {
    const headerRe = new RegExp(`RESPONSE\\s+${letter}\\s*:`, 'i');
    const match = headerRe.exec(text);
    if (!match) {
      blocks[letter] = null;
      continue;
    }
    const start = match.index + match[0].length;
    const nextRe = /RESPONSE\s+[ABC]\s*:/gi;
    nextRe.lastIndex = start;
    const next = nextRe.exec(text);
    blocks[letter] = text.slice(start, next ? next.index : text.length).trim();
  }
  return blocks;
}

/**
 * PR V5 rationale structure gate: per-response blocks with all scored dimensions + summary.
 * Rejects dimension-first "All three responses..." essays without RESPONSE A/B/C sections.
 */
function validateRationaleStructure(rationale, responseLetters = ['A', 'B', 'C']) {
  const issues = [];
  const text = String(rationale || '').trim();
  const letters = responseLetters.length ? responseLetters : ['A', 'B', 'C'];
  const minLen = letters.length === 2 ? 120 : 200;
  if (!text) return ['rationale empty'];
  if (text.length < minLen) {
    issues.push(`rationale too short for structure check (${text.length} chars, need ≥${minLen})`);
  }

  if (!/RESPONSE\s+A\s*:/i.test(text)) {
    if (/^instruction\s+following\s*:/i.test(text) || /^localization\s*:/i.test(text)) {
      issues.push('rationale uses dimension-first format; must use RESPONSE A/B/C blocks');
    }
  }

  const blocks = extractRationaleBlocks(text);
  for (const letter of letters) {
    const block = blocks[letter];
    if (!block) {
      issues.push(`missing "RESPONSE ${letter}:" section`);
      continue;
    }
    if (block.length < 80) {
      issues.push(`RESPONSE ${letter} block too short (${block.length} chars)`);
    }
    for (const { key, patterns } of RATIONALE_DIM_CHECKS) {
      if (!patterns.some((p) => p.test(block))) {
        issues.push(`RESPONSE ${letter} missing ${key} discussion`);
      }
    }
  }

  const summaryMatch = text.match(/preference\s+summary\s*:?([\s\S]*)$/i);
  if (!summaryMatch) {
    issues.push('missing "Preference Summary" section at end');
  } else if (summaryMatch[1].trim().length < 40) {
    issues.push('Preference Summary too short');
  } else if (/\b(left|right)\s+(much\s+)?better\b/i.test(summaryMatch[1])) {
    issues.push('Preference Summary must not use Left/Right Better jargon');
  }

  return issues;
}

function validateRatingsShape(ratings, task) {
  const issues = [];
  if (!ratings || typeof ratings !== 'object') {
    return ['ratings not an object'];
  }
  const respKeys = task ? getResponseKeys(task) : getResponseKeys({ responses: ratings.responses });
  const compKeys = task ? getComparisonPairsFromTask(task) : getComparisonPairsFromTask({ responses: ratings.responses, comparisonKeys: Object.keys(ratings.comparisons || {}) });
  const respLetters = respKeys.map((k) => k.replace(/^Response\s+/i, ''));

  if (!ratings.fingerprint) issues.push('missing ratings.fingerprint');
  if (!ratings.rationale || ratings.rationale.length < 50) {
    issues.push(`rationale too short (${ratings.rationale?.length || 0})`);
  } else {
    issues.push(...validateRationaleStructure(ratings.rationale, respLetters));
  }
  for (const key of respKeys) {
    const r = ratings.responses?.[key];
    if (!r) { issues.push(`missing ${key}`); continue; }
    if (!IF_LABELS.has(r.instructionFollowing)) issues.push(`${key} bad IF`);
    if (!LOC_LABELS.has(r.localization)) issues.push(`${key} bad localization`);
    if (!CONCISION_LABELS.has(r.concision)) issues.push(`${key} bad concision`);
    if (!TRUTH_LABELS.has(r.truthfulness)) issues.push(`${key} bad truthfulness`);
    if (!SAT_LABELS.has(r.satisfaction)) issues.push(`${key} bad satisfaction`);
    if (r.concision === 'Acceptable' || r.concision === 'Bad') {
      if (!r.description || !DESC_LABELS.has(r.description)) {
        issues.push(`${key} ${r.concision} requires description`);
      }
    }
    if (r.localization === 'Yes (issues present)') {
      if (!Array.isArray(r.localizationIssues) || r.localizationIssues.length === 0) {
        issues.push(`${key} localization Yes requires localizationIssues[]`);
      } else {
        for (const issue of r.localizationIssues) {
          if (!LOC_ISSUE_LABELS.has(issue)) {
            issues.push(`${key} bad localizationIssue: ${issue}`);
          }
        }
      }
    }
  }
  for (const key of compKeys) {
    const v = ratings.comparisons?.[key];
    if (!v || !COMP_LABELS.has(v)) issues.push(`bad comparison ${key}`);
  }
  for (const key of Object.keys(ratings.comparisons || {})) {
    if (!compKeys.includes(key)) issues.push(`unexpected comparison ${key}`);
  }
  return issues;
}

const SAT_RANK = {
  'Highly Unsatisfying': 0,
  'Slightly Unsatisfying': 1,
  'Slightly Satisfying': 2,
  'Highly Satisfying': 3,
};

/** Derive pairwise label from satisfaction gap (left vs right in key order). */
function satisfactionToComparison(leftSat, rightSat) {
  const l = SAT_RANK[leftSat];
  const r = SAT_RANK[rightSat];
  if (l == null || r == null) return null;
  const diff = l - r;
  if (diff === 0) return 'Same';
  const abs = Math.abs(diff);
  if (diff > 0) {
    if (abs === 1) return 'Left Slightly Better';
    if (abs === 2) return 'Left Better';
    return 'Left Much Better';
  }
  if (abs === 1) return 'Right Slightly Better';
  if (abs === 2) return 'Right Better';
  return 'Right Much Better';
}

/** Overwrite comparisons from satisfaction scores — fixes LLM Left/Right inversions. */
function normalizeComparisons(ratings, task) {
  if (!ratings?.responses) return ratings;
  ratings.comparisons = ratings.comparisons || {};
  const pairs = getComparisonPairsFromTask(task || { responses: ratings.responses, comparisonKeys: Object.keys(ratings.comparisons) });
  const next = {};
  for (const key of pairs) {
    const [left, right] = key.split(' and ');
    const fixed = satisfactionToComparison(
      ratings.responses[`Response ${left}`]?.satisfaction,
      ratings.responses[`Response ${right}`]?.satisfaction
    );
    if (fixed) next[key] = fixed;
  }
  ratings.comparisons = next;
  return ratings;
}

function validateRatingsForTask(task, ratings) {
  const issues = validateRatingsShape(ratings, task);
  if (!task?.fingerprint) issues.push('task missing fingerprint');
  if (!ratings?.fingerprint) issues.push('ratings missing fingerprint');
  if (task?.fingerprint && ratings?.fingerprint && task.fingerprint !== ratings.fingerprint) {
    issues.push(`FINGERPRINT MISMATCH task=${task.fingerprint} ratings=${ratings.fingerprint}`);
  }
  return { ok: issues.length === 0, issues };
}

function assertRatingsReady() {
  const task = loadTaskFile();
  const ratings = loadRatingsFile();
  if (!task) {
    throw new Error('STALE GUARD: current_task.json missing — extract first');
  }
  if (!ratings) {
    throw new Error('STALE GUARD: current_ratings.json missing — grade not ready');
  }
  if (fs.existsSync(GRADING_LOCK)) {
    const age = Date.now() - fs.statSync(GRADING_LOCK).mtimeMs;
    if (age < 120000) {
      throw new Error('STALE GUARD: grading in progress');
    }
  }
  const result = validateRatingsForTask(task, ratings);
  if (!result.ok) {
    throw new Error(`STALE GUARD: ${result.issues.join('; ')}`);
  }
  return { task, ratings };
}

function ratingsReadyStrict() {
  try {
    assertRatingsReady();
    return true;
  } catch {
    return false;
  }
}

async function readPanelTextFromFrame(frm) {
  return frm.evaluate(() => {
    const panels = Array.from(document.querySelectorAll('[role="tabpanel"], div')).filter((p) => {
      const style = window.getComputedStyle(p);
      return style.display !== 'none' && style.visibility !== 'hidden' && p.offsetHeight > 0;
    });
    for (const p of panels) {
      if (p.textContent.includes('Response') && p.textContent.length > 50) {
        return p.innerText;
      }
    }
    return '';
  });
}

async function extractTaskFromPage(page) {
  const frm = page.frames().find((f) => f.url().includes('task-editor'));
  if (!frm) throw new Error('task-editor frame not found');

  const taskText = await frm.evaluate(() => {
    let locale = 'en_US';
    for (const h of document.querySelectorAll('h1, h2, div, p, span')) {
      if (h.textContent.trim().startsWith('Locale:')) {
        locale = h.textContent.trim().replace('Locale:', '').trim();
      }
    }
    let requestText = '';
    const promptContainer = document.querySelector('.user-request, blockquote, [class*="user-request"]');
    if (promptContainer) requestText = promptContainer.innerText;
    if (!requestText || requestText.length < 5) {
      requestText = document.body.innerText.substring(0, 2000);
    }
    return { requestText, locale };
  });

  const layout = await frm.evaluate(detectLayoutInFrame);
  const responses = {};
  for (const tabText of layout.responseTabs) {
    const clicked = await frm.evaluate((text) => {
      const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
      const tab = tabs.find((t) => t.textContent.trim() === text);
      if (tab) { tab.click(); return true; }
      return false;
    }, tabText);
    if (!clicked) continue;
    await page.waitForTimeout(500);
    const panelText = await readPanelTextFromFrame(frm);
    responses[tabText] = cleanPanelText(panelText);
  }

  return enrichTask({
    locale: taskText.locale,
    userRequest: taskText.requestText,
    responses,
    responseKeys: layout.responseTabs,
    responseCount: layout.responseCount,
    comparisonKeys: layout.comparisonKeys,
    comparisonTabLabels: layout.comparisonTabs,
    comparisonCount: layout.comparisonCount,
  });
}

/** Puppeteer task-editor frame — for submit-time live fingerprint (single CDP session). */
async function extractTaskFromPuppeteerFrame(frm1, sleepMs = 500) {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const taskText = await frm1.evaluate(() => {
    let locale = 'en_US';
    for (const h of document.querySelectorAll('h1, h2, div, p, span')) {
      if (h.textContent.trim().startsWith('Locale:')) {
        locale = h.textContent.trim().replace('Locale:', '').trim();
      }
    }
    let requestText = '';
    const promptContainer = document.querySelector('.user-request, blockquote, [class*="user-request"]');
    if (promptContainer) requestText = promptContainer.innerText;
    if (!requestText || requestText.length < 5) {
      requestText = document.body.innerText.substring(0, 2000);
    }
    return { requestText, locale };
  });

  const layout = await frm1.evaluate(detectLayoutInFrame);
  const responses = {};
  for (const tabText of layout.responseTabs) {
    const clicked = await frm1.evaluate((text) => {
      const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
      const tab = tabs.find((t) => t.textContent.trim() === text);
      if (tab) { tab.click(); return true; }
      return false;
    }, tabText);
    if (!clicked) continue;
    await sleep(sleepMs);
    const panelText = await frm1.evaluate(() => {
      const panels = Array.from(document.querySelectorAll('[role="tabpanel"], div')).filter((p) => {
        const style = window.getComputedStyle(p);
        return style.display !== 'none' && style.visibility !== 'hidden' && p.offsetHeight > 0;
      });
      for (const p of panels) {
        if (p.textContent.includes('Response') && p.textContent.length > 50) {
          return p.innerText;
        }
      }
      return '';
    });
    responses[tabText] = cleanPanelText(panelText);
  }

  return enrichTask({
    locale: taskText.locale,
    userRequest: taskText.requestText,
    responses,
    responseKeys: layout.responseTabs,
    responseCount: layout.responseCount,
    comparisonKeys: layout.comparisonKeys,
    comparisonTabLabels: layout.comparisonTabs,
    comparisonCount: layout.comparisonCount,
  });
}

module.exports = {
  ROOT,
  RUNS,
  TASK_FILE,
  RATINGS_FILE,
  ACTIVE_FP_FILE,
  GRADING_LOCK,
  NEEDS_GRADING,
  fingerprintFromTask,
  enrichTask,
  saveTask,
  loadTaskFile,
  loadRatingsFile,
  invalidateRatings,
  validateRatingsShape,
  validateRationaleStructure,
  extractRationaleBlocks,
  validateRatingsForTask,
  assertRatingsReady,
  ratingsReadyStrict,
  normalizeComparisons,
  satisfactionToComparison,
  extractTaskFromPage,
  extractTaskFromPuppeteerFrame,
  normalizeUserRequest,
  sanitizeForPrompt,
  getResponseKeys,
  getResponseLetters,
  getComparisonPairsFromTask,
  comparisonTabToKey,
  detectLayoutInFrame,
  DESC_LABELS,
  LOC_ISSUE_LABELS,
};
