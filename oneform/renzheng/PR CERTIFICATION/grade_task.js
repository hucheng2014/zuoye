/**
 * LLM independent grader — DEPRECATED: LLM API no longer used.
 * Agent writes current_ratings.json manually after reading current_task.json.
 * This file is kept for reference only; task_bridge and auto_grade_daemon do NOT call it.
 */
const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');
const { URL } = require('url');
const {
  TASK_FILE,
  RATINGS_FILE,
  GRADING_LOCK,
  NEEDS_GRADING,
  loadTaskFile,
  enrichTask,
  validateRatingsShape,
  validateRatingsForTask,
  normalizeComparisons,
  normalizeUserRequest,
  sanitizeForPrompt,
  getResponseKeys,
  getComparisonPairsFromTask,
  ROOT,
  RUNS,
} = require('./task_utils');

const MODEL = process.env.PR_LLM_MODEL || process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-6';
const LOG_FILE = path.join(RUNS, 'grade.log');

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  fs.mkdirSync(RUNS, { recursive: true });
  fs.appendFileSync(LOG_FILE, line + '\n', { flag: 'a' });
}

function loadCredentials() {
  if (process.env.ANTHROPIC_BASE_URL && (process.env.ANTHROPIC_AUTH_TOKEN || process.env.ANTHROPIC_API_KEY)) {
    return;
  }
  const settingsPath = path.join(require('os').homedir(), '.claude', 'settings.json');
  if (fs.existsSync(settingsPath)) {
    const data = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
    for (const [key, value] of Object.entries(data.env || {})) {
      if (key.startsWith('ANTHROPIC') && value && !process.env[key]) {
        process.env[key] = String(value);
      }
    }
  }
  if (!process.env.ANTHROPIC_BASE_URL || !(process.env.ANTHROPIC_AUTH_TOKEN || process.env.ANTHROPIC_API_KEY)) {
    throw new Error('Missing Anthropic credentials (ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN)');
  }
}

function loadSopExcerpt() {
  const p = path.join(ROOT, 'PR_V5_Certification_tips_中文详细总结.md');
  if (fs.existsSync(p)) return fs.readFileSync(p, 'utf8').slice(0, 5000);
  return 'Grade IF, Localization, Concision, Truthfulness, Satisfaction independently per PR V5.';
}

function httpRequest(url, options, body) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const lib = u.protocol === 'https:' ? https : http;
    const req = lib.request(url, options, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        const raw = Buffer.concat(chunks).toString('utf8');
        if (res.statusCode >= 400) {
          reject(new Error(`HTTP ${res.statusCode}: ${raw.slice(0, 500)}`));
          return;
        }
        resolve(raw);
      });
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

async function llmRequest(prompt) {
  loadCredentials();
  const base = process.env.ANTHROPIC_BASE_URL.replace(/\/$/, '');
  const token = process.env.ANTHROPIC_AUTH_TOKEN || process.env.ANTHROPIC_API_KEY;
  const body = JSON.stringify({
    model: MODEL,
    max_tokens: 4096,
    messages: [{ role: 'user', content: prompt }],
  });
  const raw = await httpRequest(
    `${base}/v1/messages`,
    {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'content-length': Buffer.byteLength(body),
        'x-api-key': token,
        'anthropic-version': '2023-06-01',
      },
    },
    body
  );
  const data = JSON.parse(raw);
  let text = '';
  for (const block of data.content || []) {
    if (block.type === 'text') text += block.text;
  }
  text = text.trim();
  if (text.startsWith('```')) {
    text = text.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '');
  }
  return text;
}

function buildResponseSchemaBlock() {
  return `{
      "instructionFollowing": "Not following|Partially following|Fully following",
      "localization": "Yes (issues present)|No (no issues)",
      "localizationIssues": ["(REQUIRED array if localization Yes — pick from rule 10)"],
      "concision": "Bad|Acceptable|Good",
      "description": "(REQUIRED if concision is Acceptable or Bad)",
      "truthfulness": "Not Truthful|Partially Truthful|Truthful",
      "satisfaction": "Highly Unsatisfying|Slightly Unsatisfying|Slightly Satisfying|Highly Satisfying"
    }`;
}

function buildPrompt(task) {
  const sop = sanitizeForPrompt(loadSopExcerpt(), 4500);
  const userReq = sanitizeForPrompt(normalizeUserRequest(task.userRequest), 2000);
  const respKeys = getResponseKeys(task);
  const compKeys = getComparisonPairsFromTask(task);
  const respSections = respKeys.map((key) => {
    const letter = key.replace(/^Response\s+/i, '');
    return `RESPONSE ${letter}:\n${sanitizeForPrompt(task.responses?.[key], 2500)}`;
  }).join('\n\n');
  const respSchema = respKeys.map((key) => `    "${key}": ${buildResponseSchemaBlock()}`).join(',\n');
  const compSchema = compKeys.map((key) => `    "${key}": "Left Much Better|Left Better|Left Slightly Better|Same|Right Slightly Better|Right Better|Right Much Better"`).join(',\n');
  const rationaleLetters = respKeys.map((k) => k.replace(/^Response\s+/i, '')).join(', ');
  const responseCount = respKeys.length;

  return `You are an expert Preference Ranking v5 grader. Judge ONLY this single task independently.

Hard rules:
1. Read the user request and ALL ${responseCount} responses in full before scoring.
2. Grade each dimension independently — do not let one dimension bias another.
3. Q&A tasks: if the model attempted to answer, do NOT deduct Instruction Following for factual errors; deduct Truthfulness only.
4. Explicit format/word-count constraints missed → Instruction Following (Partially following or Not following).
5. Any minor issue on a dimension → that response CANNOT be Highly Satisfying.
6. Comparisons must match satisfaction logic: 1-level gap → Better; same level → Slightly Better or Same; 2+ levels → Much Better.
7. Rationale MUST use this EXACT structure (English only):
   RESPONSE A:
   Instruction Following: ...
   Localization: ...
   Concision: ...
   Truthfulness: ...
   Satisfaction: ...
   (repeat for each response: ${rationaleLetters})
   Preference Summary: ... (natural language; do NOT write "Left Better" or "Right Better")
8. Never write dimension-first summaries like "Instruction Following: All responses...". Each response gets its own block.
9. If Concision is "Acceptable" OR "Bad", you MUST include "description": "It could have been made shorter" OR "It could have been made longer" (required for form fill).
10. If localization is "Yes (issues present)", you MUST include "localizationIssues": ["..."] with 1+ values from: Unlocalized information, Overly-localized content, Spelling, Tone, Non-local perspective, Vocabulary, Awkward or unnatural writing, Formatting & punctuation, Grammar, Phrase or idiom, Units of measurement, Wrong language, Other.
11. Output ONLY valid JSON — no markdown fences. The "rationale" value must be valid JSON (escape newlines as \\n inside the string).
12. This task has ${responseCount} response(s) and ${compKeys.length} comparison(s). Do NOT invent extra responses or comparisons.

SOP reference:
${sop}

Task locale: ${task.locale}
Task fingerprint: ${task.fingerprint}
Response count: ${responseCount}

USER REQUEST:
${userReq}

${respSections}

Return JSON exactly matching this schema:
{
  "fingerprint": "${task.fingerprint}",
  "responses": {
${respSchema}
  },
  "comparisons": {
${compSchema}
  },
  "rationale": "MUST follow RESPONSE block template from rule 7, then Preference Summary"
}`;
}

function escapeJsonString(s) {
  return s
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\r/g, '')
    .replace(/\n/g, '\\n')
    .replace(/\t/g, '\\t');
}

function parseRatingsJson(text) {
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start < 0 || end < 0) throw new Error('LLM did not return JSON object');
  const slice = text.slice(start, end + 1);
  try {
    return JSON.parse(slice);
  } catch (firstErr) {
    const ratIdx = slice.indexOf('"rationale"');
    if (ratIdx < 0) throw firstErr;
    const afterColon = slice.indexOf('"', slice.indexOf(':', ratIdx) + 1);
    const lastBrace = slice.lastIndexOf('}');
    const beforeClose = slice.lastIndexOf('"', lastBrace);
    if (afterColon < 0 || beforeClose <= afterColon) throw firstErr;
    const rawRationale = slice.slice(afterColon + 1, beforeClose);
    const fixed = `${slice.slice(0, afterColon + 1)}${escapeJsonString(rawRationale)}${slice.slice(beforeClose)}`;
    return JSON.parse(fixed);
  }
}

async function gradeTask(task) {
  const prompt = buildPrompt(task);
  let lastErr;
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      log(`LLM grade attempt ${attempt} fingerprint=${task.fingerprint}`);
      const raw = await llmRequest(prompt);
      const ratings = parseRatingsJson(raw);
      ratings.fingerprint = task.fingerprint;
      ratings.gradedAt = new Date().toISOString();
      ratings.ratingMethod = 'llm_per_task_v1';
      ratings.locale = task.locale;
      normalizeComparisons(ratings, task);

      const shapeIssues = validateRatingsShape(ratings, task);
      if (shapeIssues.length) {
        throw new Error(`shape invalid: ${shapeIssues.join('; ')}`);
      }
      const match = validateRatingsForTask(task, ratings);
      if (!match.ok) {
        throw new Error(`validation failed: ${match.issues.join('; ')}`);
      }
      return ratings;
    } catch (e) {
      lastErr = e;
      log(`attempt ${attempt} failed: ${e.message}`);
    }
  }
  throw lastErr;
}

async function main() {
  fs.mkdirSync(RUNS, { recursive: true });
  if (fs.existsSync(GRADING_LOCK)) {
    const age = Date.now() - fs.statSync(GRADING_LOCK).mtimeMs;
    if (age < 120000) {
      log(`grading already in progress (${Math.round(age / 1000)}s)`);
      process.exit(0);
    }
    log(`stale grading.lock (${Math.round(age / 1000)}s) — removing`);
    fs.unlinkSync(GRADING_LOCK);
  }
  fs.writeFileSync(GRADING_LOCK, String(process.pid));

  try {
    let task = loadTaskFile();
    if (!task) throw new Error('current_task.json missing');
    if (!task.fingerprint) task = enrichTask(task);

    const existing = (() => {
      try { return JSON.parse(fs.readFileSync(RATINGS_FILE, 'utf8')); } catch { return null; }
    })();
    if (existing?.fingerprint === task.fingerprint) {
      const v = validateRatingsForTask(task, existing);
      if (v.ok) {
        log(`ratings already valid for fingerprint=${task.fingerprint}`);
        try { fs.unlinkSync(NEEDS_GRADING); } catch {}
        return;
      }
    }

    const ratings = await gradeTask(task);
    fs.writeFileSync(RATINGS_FILE, JSON.stringify(ratings, null, 2));
    try { fs.unlinkSync(NEEDS_GRADING); } catch {}
    log(`wrote current_ratings.json fingerprint=${ratings.fingerprint} rationaleLen=${ratings.rationale.length}`);
  } finally {
    try { fs.unlinkSync(GRADING_LOCK); } catch {}
  }
}

if (require.main === module) {
  main().catch((e) => {
    log(`FATAL: ${e.message}`);
    process.exit(1);
  });
}

module.exports = { gradeTask, buildPrompt };
