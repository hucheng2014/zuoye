require('./_timeout');
const { chromium } = require('playwright');

const CDP_ENDPOINTS = [
  process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233',
  'http://127.0.0.1:9232',
];

async function connect() {
  for (const ep of CDP_ENDPOINTS) {
    try { return { browser: await chromium.connectOverCDP(ep), endpoint: ep }; } catch {}
  }
  throw new Error('No CDP endpoint available');
}

function clean(t) { return (t || '').replace(/ /g, ' ').replace(/[ \t]+\n/g, '\n').trim(); }

async function main() {
  const { browser, endpoint } = await connect();
  try {
    const ctx = browser.contexts()[0];
    if (!ctx) throw new Error('No browser context');
    const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
    if (!page) throw new Error('No page');

    const taskFrame = page.frames().find(f => f.url().includes('task-editor'));
    if (!taskFrame) throw new Error('task-editor frame not found');

    await page.waitForTimeout(300);

    const srcdocFrames = page.frames().filter(f => f.url() === 'about:srcdoc');

    const frameTexts = [];
    const results = await Promise.allSettled(
      srcdocFrames.map(f => f.locator('body').innerText({ timeout: 300 }).then(clean))
    );
    for (const r of results) {
      if (r.status === 'fulfilled' && r.value) frameTexts.push(r.value);
    }

    const inputText = frameTexts[0] || '';

    let responseA = '', responseB = '', responseC = '';
    const diffTexts = [];
    const cleanTexts = [];
    for (const t of frameTexts) {
      if (t.startsWith('Proposed edits')) diffTexts.push(t);
      else if (t !== inputText && !t.startsWith('Response ') && !t.includes('Dimension') && !t.includes('Correctness')) {
        cleanTexts.push(t);
      }
    }

    // Pairwise frame labels help identify responses
    for (const t of frameTexts) {
      if (t.startsWith('Response A (right)') || t.startsWith('Response A (left)')) {
        const rtext = t.replace(/^Response A \((right|left)\)\n?/, '').trim();
        if (!responseA && rtext && !rtext.includes('class TextParser')) responseA = rtext;
      }
      if (t.startsWith('Response B (right)') || t.startsWith('Response B (left)')) {
        const rtext = t.replace(/^Response B \((right|left)\)\n?/, '').trim();
        if (!responseB && rtext && !rtext.includes('class TextParser')) responseB = rtext;
      }
      if (t.startsWith('Response C (right)') || t.startsWith('Response C (left)')) {
        const rtext = t.replace(/^Response C \((right|left)\)\n?/, '').trim();
        if (!responseC && rtext && !rtext.includes('class TextParser')) responseC = rtext;
      }
    }

    // Fallback: use clean texts in order
    if (!responseA && cleanTexts.length >= 2) responseA = cleanTexts[1] || '';
    if (!responseB && cleanTexts.length >= 3) responseB = cleanTexts[2] || '';
    if (!responseC && cleanTexts.length >= 4) responseC = cleanTexts[3] || '';

    // Extract diffs
    const diffs = diffTexts.map(d => {
      const lines = d.split('\n');
      return lines.find(l => l.includes('[-') || l.includes('{+')) || lines[1] || '';
    });

    // Get all controls
    const controls = await taskFrame.locator('input, textarea').evaluateAll(els =>
      els.map((el, i) => ({
        i, tag: el.tagName, type: el.getAttribute('type'),
        name: el.getAttribute('name'), value: el.value || '',
        checked: el.checked || false,
      }))
    );

    // Get form text
    const formText = clean(await taskFrame.locator('body').innerText({ timeout: 2000 }).catch(() => ''));

    // Extract locale
    const localeMatch = formText.match(/Locale:\s*(\S+)/);

    const output = {
      extractedAt: new Date().toISOString(),
      cdpEndpoint: endpoint,
      pageUrl: page.url(),
      locale: localeMatch ? localeMatch[1] : 'unknown',
      inputText,
      responseA,
      responseB,
      responseC,
      diffs,
      controls,
      formTextPreview: formText.slice(0, 2000),
    };

    console.log(JSON.stringify(output, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch(e => { console.error(e.stack || e.message); process.exit(1); });
