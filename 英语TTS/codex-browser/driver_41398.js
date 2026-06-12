const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright-core');

const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const USER_DATA_DIR = 'C:\\Users\\BERN7P\\codex-browser\\edge-profile-41393';
const TARGET_URL = 'https://ilabel.weixin.qq.com/mission/41398/label';

const STATUS_PATH = 'C:\\Users\\BERN7P\\codex-browser\\driver_41398.status.json';
const RPC_IN_PATH = 'C:\\Users\\BERN7P\\codex-browser\\driver_41398.in.json';
const RPC_OUT_PATH = 'C:\\Users\\BERN7P\\codex-browser\\driver_41398.out.json';

function writeJson(filePath, obj) {
  fs.writeFileSync(filePath, JSON.stringify(obj, null, 2), 'utf8');
}

async function extractItems(page) {
  return await page.evaluate(() => {
    const audios = [...document.querySelectorAll('audio')];
    const findRoot = (a) => {
      let r = a;
      for (let d = 0; d < 12 && r; d += 1, r = r.parentElement) {
        const t = r.innerText || '';
        if (t.includes('是否同一个人') && t.includes('音频内容')) return r;
      }
      return a.parentElement;
    };

    const getCheckedIndex = (g) => {
      const labels = [...g.querySelectorAll('label[role="radio"]')];
      return labels.findIndex(
        (x) => x.classList.contains('is-checked') || x.getAttribute('aria-checked') === 'true',
      );
    };

    const items = audios.map((a, i) => {
      const r = findRoot(a);
      const filename = (((r?.innerText || '').match(/目录[:：]\s*([^\n]+)/) || [])[1] || '').trim();
      const groups = [...(r?.querySelectorAll('[role="radiogroup"]') || [])].map((g) =>
        getCheckedIndex(g),
      );
      const textEl = r?.querySelector('textarea,input[type="text"]');
      const text = (textEl && (textEl.value || '').trim()) || '';
      return {
        index: i,
        filename,
        src: a.currentSrc || a.src || '',
        selectedIndexes: groups,
        text,
      };
    });

    return {
      url: location.href,
      title: document.title,
      extractedAt: new Date().toISOString(),
      count: items.length,
      items,
    };
  });
}

async function applyEdits(page, edits) {
  // Apply in page context to avoid fragile selectors; throttled to reduce server-side rate limiting.
  return await page.evaluate(async (payload) => {
    const { edits, delayMs } = payload;
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

    const audios = [...document.querySelectorAll('audio')];
    const findRoot = (a) => {
      let r = a;
      for (let d = 0; d < 12 && r; d += 1, r = r.parentElement) {
        const t = r.innerText || '';
        if (t.includes('是否同一个人') && t.includes('音频内容')) return r;
      }
      return a.parentElement;
    };

    const mapByFilename = new Map();
    for (const a of audios) {
      const r = findRoot(a);
      const filename = (((r?.innerText || '').match(/目录[:：]\s*([^\n]+)/) || [])[1] || '').trim();
      if (filename) mapByFilename.set(filename, { audio: a, root: r });
    }

    const clickRadio = (groupEl, wantIdx) => {
      if (!groupEl) return false;
      const labels = [...groupEl.querySelectorAll('label[role="radio"]')];
      if (wantIdx < 0 || wantIdx >= labels.length) return false;
      const curIdx = labels.findIndex(
        (x) => x.classList.contains('is-checked') || x.getAttribute('aria-checked') === 'true',
      );
      if (curIdx === wantIdx) return false;
      labels[wantIdx].click();
      return true;
    };

    const setText = (rootEl, wantText) => {
      if (typeof wantText !== 'string') return false;
      const textEl = rootEl?.querySelector('textarea,input[type="text"]');
      if (!textEl) return false;
      const cur = (textEl.value || '').trim();
      if (cur === wantText.trim()) return false;
      textEl.value = wantText;
      textEl.dispatchEvent(new Event('input', { bubbles: true }));
      textEl.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    };

    const applied = [];
    for (const e of edits || []) {
      const hit = mapByFilename.get(e.filename);
      if (!hit) {
        applied.push({ filename: e.filename, ok: false, reason: 'not_found' });
        continue;
      }
      const r = hit.root;
      const groups = [...(r?.querySelectorAll('[role="radiogroup"]') || [])];
      const changed = { filename: e.filename, ok: true, radio: [], text: false };

      if (Array.isArray(e.selectedIndexes)) {
        for (let gi = 0; gi < e.selectedIndexes.length && gi < groups.length; gi += 1) {
          const want = e.selectedIndexes[gi];
          if (typeof want === 'number' && want >= 0) {
            const did = clickRadio(groups[gi], want);
            changed.radio.push(did);
          } else {
            changed.radio.push(false);
          }
        }
      }

      if (typeof e.text === 'string') {
        changed.text = setText(r, e.text);
      }

      applied.push(changed);
      await sleep(delayMs);
    }
    return { appliedCount: applied.length, applied };
  }, { edits, delayMs: 250 });
}

async function clickVisibleText(page, targets) {
  const wanted = Array.isArray(targets) ? targets : [targets];
  return await page.evaluate((texts) => {
    const isVisible = (el) => {
      if (!el) return false;
      const style = window.getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return (
        style &&
        style.visibility !== 'hidden' &&
        style.display !== 'none' &&
        rect.width > 0 &&
        rect.height > 0
      );
    };

    const candidates = [
      ...document.querySelectorAll('button, [role="button"], .el-button, a, span, div'),
    ];
    for (const text of texts) {
      const exact = candidates.find((el) => isVisible(el) && (el.innerText || '').trim() === text);
      if (exact) {
        exact.click();
        return { ok: true, text, mode: 'exact' };
      }
    }
    for (const text of texts) {
      const partial = candidates.find((el) => isVisible(el) && (el.innerText || '').includes(text));
      if (partial) {
        partial.click();
        return { ok: true, text, mode: 'partial' };
      }
    }
    return { ok: false, texts };
  }, wanted);
}

async function submitCurrentPage(page) {
  const before = await extractItems(page);
  const beforeKey = JSON.stringify(before.items.map((x) => x.filename));

  const firstClick = await clickVisibleText(page, ['提交']);
  if (!firstClick.ok) {
    return { ok: false, stage: 'submit_click', details: firstClick };
  }

  await page.waitForTimeout(1200);

  // Some flows show a confirm dialog. Click it if present.
  const confirmClick = await clickVisibleText(page, ['确定', '确认', '继续提交']);
  await page.waitForTimeout(confirmClick.ok ? 1200 : 800);

  try {
    await page.waitForFunction(
      (prevKey) => {
        const audios = [...document.querySelectorAll('audio')];
        const findRoot = (a) => {
          let r = a;
          for (let d = 0; d < 12 && r; d += 1, r = r.parentElement) {
            const t = r.innerText || '';
            if (t.includes('是否同一个人') && t.includes('音频内容')) return r;
          }
          return a.parentElement;
        };
        const current = audios.map((a) => {
          const r = findRoot(a);
          return ((((r?.innerText || '').match(/目录[:：]\s*([^\n]+)/) || [])[1]) || '').trim();
        });
        return JSON.stringify(current) !== prevKey && current.length > 0;
      },
      beforeKey,
      { timeout: 120000 },
    );
  } catch (error) {
    // Fall through and return the current page state for inspection.
  }

  await page.waitForTimeout(1500);
  const after = await extractItems(page);
  return {
    ok: true,
    submitClick: firstClick,
    confirmClick,
    beforeCount: before.count,
    afterCount: after.count,
    beforeFirst: before.items[0]?.filename || '',
    afterFirst: after.items[0]?.filename || '',
    changed: (before.items[0]?.filename || '') !== (after.items[0]?.filename || ''),
    data: after,
  };
}

async function main() {
  // Ensure output file doesn't contain stale success from previous runs.
  try {
    if (fs.existsSync(RPC_OUT_PATH)) fs.unlinkSync(RPC_OUT_PATH);
  } catch {}

  const context = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless: false,
    executablePath: EDGE_PATH,
    viewport: null,
    args: ['--new-window', '--start-maximized'],
  });

  const page = context.pages()[0] || (await context.newPage());
  await page.bringToFront();
  await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: 120000 });
  await page.waitForTimeout(2000);

  writeJson(STATUS_PATH, {
    ok: true,
    url: page.url(),
    title: await page.title(),
    openedAt: new Date().toISOString(),
  });

  let busy = false;
  // Poll for RPC commands written by PowerShell.
  // Command format: { id: string, action: 'extract'|'apply', outPath?: string, edits?: [...] }
  // Response is written to RPC_OUT_PATH with the same id.
  setInterval(async () => {
    if (busy) return;
    if (!fs.existsSync(RPC_IN_PATH)) return;
    busy = true;
    try {
      const raw = fs.readFileSync(RPC_IN_PATH, 'utf8');
      fs.unlinkSync(RPC_IN_PATH);
      const cmd = JSON.parse(raw);

      if (cmd.action === 'extract') {
        const data = await extractItems(page);
        if (cmd.outPath) {
          const out = path.resolve(cmd.outPath);
          fs.mkdirSync(path.dirname(out), { recursive: true });
          writeJson(out, data);
        }
        writeJson(RPC_OUT_PATH, { ok: true, id: cmd.id, action: cmd.action, data });
      } else if (cmd.action === 'apply') {
        const res = await applyEdits(page, cmd.edits || []);
        writeJson(RPC_OUT_PATH, { ok: true, id: cmd.id, action: cmd.action, result: res });
      } else if (cmd.action === 'submit') {
        const res = await submitCurrentPage(page);
        if (cmd.outPath && res?.data) {
          const out = path.resolve(cmd.outPath);
          fs.mkdirSync(path.dirname(out), { recursive: true });
          writeJson(out, res.data);
        }
        writeJson(RPC_OUT_PATH, { ok: true, id: cmd.id, action: cmd.action, result: res });
      } else {
        writeJson(RPC_OUT_PATH, { ok: false, id: cmd.id, error: `unknown action: ${cmd.action}` });
      }
    } catch (error) {
      writeJson(RPC_OUT_PATH, {
        ok: false,
        error: String(error && error.stack ? error.stack : error),
      });
    } finally {
      busy = false;
    }
  }, 350);

  await new Promise(() => {});
}

main().catch((error) => {
  writeJson(STATUS_PATH, {
    ok: false,
    error: String(error && error.stack ? error.stack : error),
    failedAt: new Date().toISOString(),
  });
  process.exit(1);
});
