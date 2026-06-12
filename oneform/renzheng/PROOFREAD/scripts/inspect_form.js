require('./_timeout');
const { chromium } = require('playwright');
const CDP = process.env.CDP_ENDPOINT || 'http://127.0.0.1:9233';

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('starshot')) || ctx.pages()[0];
  const taskFrame = page.frames().find(f => f.url().includes('task-editor'));
  if (!taskFrame) throw new Error('task-editor frame not found');

  // Click Response A tab to see its current state
  const tabA = taskFrame.getByRole('tab', { name: 'Response A' });
  if (await tabA.count()) await tabA.first().click();
  await page.waitForTimeout(500);

  // Get ALL controls with full context
  const controls = await taskFrame.locator('input, textarea, select').evaluateAll(els =>
    els.map((el, i) => {
      const container = el.closest('.question-block, .question-container, [class*="question"], div') || el.parentElement;
      const labelEl = el.closest('label') || container;
      return {
        i, tag: el.tagName, type: el.getAttribute('type'),
        name: el.getAttribute('name'), value: el.value || '',
        checked: el.checked || false,
        visible: el.offsetParent !== null,
        label: (labelEl?.innerText || '').trim().slice(0, 120),
      };
    })
  );

  // Only show visible controls
  const visible = controls.filter(c => c.visible);
  const checked = controls.filter(c => c.checked);

  console.log('=== VISIBLE CONTROLS ===');
  console.log(JSON.stringify(visible, null, 2));
  console.log('\n=== CHECKED CONTROLS ===');
  console.log(JSON.stringify(checked, null, 2));

  // Also get the form text for Response A section
  const formText = await taskFrame.locator('body').innerText({ timeout: 2000 }).catch(() => '');
  // Find the part after "Response A"
  const respAIdx = formText.indexOf('Response A (proofread copy)');
  const respBIdx = formText.indexOf('Response B');
  if (respAIdx !== -1) {
    const section = formText.slice(respAIdx, respBIdx !== -1 ? respBIdx : respAIdx + 2000);
    console.log('\n=== RESPONSE A SECTION TEXT ===');
    console.log(section.slice(0, 1500));
  }

  await browser.close();
}

main().catch(e => { console.error(e.message); process.exit(1); });
