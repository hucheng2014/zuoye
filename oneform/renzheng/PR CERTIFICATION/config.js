const SUBMIT_AT_SEC = parseInt(process.env.PR_SUBMIT_AT_SEC || '720', 10);
const CDP_URL = process.env.PR_CDP_URL || 'http://127.0.0.1:9233';
const CDP_FALLBACK = process.env.PR_CDP_FALLBACK || 'http://127.0.0.1:9232';

// Fast submit path: ratings must be ready BEFORE TPT hits 720s; submit should finish in ~30s.
const DELAY = {
  tab: 500,
  radio: 120,
  comp: 200,
  rationale: 150,
  submit: 800,
  confirm: 1200,
  next: 2000,
};

module.exports = { SUBMIT_AT_SEC, CDP_URL, CDP_FALLBACK, DELAY };
