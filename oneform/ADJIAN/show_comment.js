const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const pages = browser.contexts()[0]?.pages() || [];
  const page = pages.find(p => p.url().includes('tryrating.com')) || pages[0];
  if (!page) { console.log('No page'); return; }

  const info = await page.evaluate(() => {
    const ta = document.querySelector('textarea');
    const text = document.body.innerText;
    const tid = text.match(/Task ID\s*\n?\s*(\S+)/);
    const kw = text.match(/KEYWORD\s*\n+([\s\S]+?)\n\n/);
    const ex = text.match(/EXPANSION\s*\n+([\s\S]+?)\n\n/);
    return {
      taskId: tid ? tid[1] : null,
      keyword: kw ? kw[1].replace(/\s+/g,' ').trim() : null,
      expansion: ex ? ex[1].replace(/\s+/g,' ').trim() : null,
      commentValue: ta ? ta.value : 'NO_TEXTAREA',
    };
  });

  console.log('Task ID:', info.taskId);
  console.log('Keyword:', info.keyword);
  console.log('Expansion:', info.expansion);
  console.log('=== COMMENT VALUE ===');
  console.log(info.commentValue);
  console.log('=== END ===');
})();
