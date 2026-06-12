const { chromium } = require('playwright');
const path = require('path');

async function run() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9237');
  const page = browser.contexts()[0].pages()[0];
  await page.setViewportSize({ width: 1200, height: 1000 });

  const captionText = `总体概述: 这是一段户外环境的录音，其中包含持续的鸟鸣声和一次高尔夫球杆击球声。
详细描述:
1. 人声: 无
<总结精炼结果>：
无
2. 环境与音效:
    2.1 环境背景声:
        持续的鸟鸣声和微弱的户外环境声，几乎不被察觉。
    2.2 音效:
        [00:01.800-00:02.100] 高尔夫球杆击球声。
3. 背景音乐:
     音量: 无
     乐器: 无
     节奏与速度: 无
     录音质量与制作手法: 无
     旋律与和声: 无
     风格流派: 无
     氛围情绪: 无
     作用: 无
4. 特殊合成音效:
   无`;

  // 1. Select Radio "中文"
  console.log('Selecting "中文" radio button...');
  const radio = page.locator('input[type="radio"][value="中文"]').first();
  await radio.click({ force: true });
  await page.waitForTimeout(500);

  // 2. Fill Textarea
  console.log('Filling standardized caption text...');
  const ta = page.locator('textarea').first();
  await ta.fill(captionText);
  await page.waitForTimeout(500);

  // 3. Take screenshot before submit
  let imgPath = '/Users/xaa/.gemini/antigravity-cli/brain/6ffe4535-d43d-47de-bd8b-27434df1d17f/scratch/port_9237_golf_filled.png';
  await page.screenshot({ path: imgPath });
  console.log('Saved preview screenshot to:', imgPath);

  // 4. Click Submit
  console.log('Clicking "提交任务" (Submit Task) button...');
  await page.locator('button:has-text("提交任务")').first().click();
  await page.waitForTimeout(4000);

  // 5. Take screenshot after submit
  imgPath = '/Users/xaa/.gemini/antigravity-cli/brain/6ffe4535-d43d-47de-bd8b-27434df1d17f/scratch/port_9237_golf_submitted.png';
  await page.screenshot({ path: imgPath });
  console.log('Saved final screenshot to:', imgPath);
  console.log('Current URL:', page.url());

  await browser.close();
}

run().catch(console.error);
