const { chromium } = require('../node_modules/playwright');
(async()=>{
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9235');
  const contexts = browser.contexts();
  console.log('contexts', contexts.length);
  for (const [ci, ctx] of contexts.entries()) {
    console.log('context', ci, 'pages', ctx.pages().length);
    for (const [pi, page] of ctx.pages().entries()) {
      console.log('PAGE', ci, pi, await page.title(), page.url());
      try { await page.waitForLoadState('domcontentloaded', {timeout: 3000}); } catch(e) {}
      const text = await page.locator('body').innerText({timeout: 5000}).catch(e => 'ERR '+e.message);
      console.log('TEXT_START\n'+text.slice(0,5000)+'\nTEXT_END');
      const inputs = await page.locator('input,textarea,select,button,[role=button],[role=radio],[role=checkbox]').evaluateAll(els => els.slice(0,200).map((el,i)=>({i, tag:el.tagName, type:el.getAttribute('type'), role:el.getAttribute('role'), name:el.getAttribute('name'), id:el.id, text:el.innerText||el.value||el.getAttribute('aria-label')||el.getAttribute('placeholder')||'', checked:el.checked, disabled:el.disabled, classes:el.className}))).catch(e=>({err:e.message}));
      console.log('CONTROLS', JSON.stringify(inputs,null,2).slice(0,10000));
    }
  }
  await browser.close();
})();
