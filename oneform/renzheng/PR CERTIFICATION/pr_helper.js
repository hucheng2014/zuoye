const puppeteer = require('puppeteer-core');

const CDP_URL = 'http://127.0.0.1:9235';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitForUserInput(prompt) {
  const readline = require('readline').createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise(resolve => {
    readline.question(prompt, answer => {
      readline.close();
      resolve(answer);
    });
  });
}

async function main() {
  console.log('=== PR Certification Helper ===');
  console.log('Connecting to browser via CDP...');

  const browser = await puppeteer.connect({
    browserURL: CDP_URL,
    defaultViewport: null
  });

  const pages = await browser.pages();
  const page = pages[0] || await browser.newPage();

  console.log('✓ Connected to browser');
  console.log('Current URL:', await page.url());

  console.log('\n=== Key Tutorial Reminders ===');
  console.log('1. 维度独立评分 - Each dimension is independent');
  console.log('2. 事实错扣Truthfulness，不扣IF - Factual errors → Truthfulness, not IF');
  console.log('3. V5所有语法/拼写/标点错误都算Localization');
  console.log('4. Much Better只用于满意度差2级以上');
  console.log('5. 两个都Highly Unsatisfying必须选Same');
  console.log('6. 有任何Minor Issue就别轻易打Highly Satisfying\n');

  let taskCount = 0;
  const maxTasks = 20;

  while (taskCount < maxTasks) {
    console.log(`\n━━━ Task ${taskCount + 1}/${maxTasks} ━━━`);

    try {
      // Check for ACCEPT button
      await page.waitForSelector('button', { timeout: 5000 });

      const buttons = await page.$$('button');
      let acceptFound = false;

      for (const button of buttons) {
        const text = await page.evaluate(el => el.textContent, button);
        if (text && (text.includes('ACCEPT') || text.includes('Accept'))) {
          console.log('✓ Found ACCEPT button');
          const answer = await waitForUserInput('Press Enter to click ACCEPT (or type "skip" to skip): ');

          if (answer.toLowerCase() !== 'skip') {
            await button.click();
            console.log('✓ Clicked ACCEPT');
            await sleep(3000);
            acceptFound = true;
          }
          break;
        }
      }

      // Take screenshot
      const screenshotPath = `/tmp/pr_task_${taskCount + 1}.png`;
      await page.screenshot({ path: screenshotPath, fullPage: true });
      console.log(`✓ Screenshot saved: ${screenshotPath}`);

      // Get page title/heading to understand task type
      const heading = await page.$eval('h1, h2, [role="heading"]', el => el.textContent).catch(() => 'Unknown');
      console.log(`Task type: ${heading}`);

      console.log('\n📋 Now evaluate the task following the tutorial:');
      console.log('   - Check User Request validity');
      console.log('   - Rate each dimension independently');
      console.log('   - Following Instructions (IF)');
      console.log('   - Localization (grammar/spelling/punctuation)');
      console.log('   - Concision');
      console.log('   - Truthfulness');
      console.log('   - Overall Satisfaction');
      console.log('   - Then do preference ranking\n');

      await waitForUserInput('Press Enter when you have filled all ratings and are ready to submit: ');

      // Look for submit button
      const submitButtons = await page.$$('button');
      let submitted = false;

      for (const button of submitButtons) {
        const text = await page.evaluate(el => el.textContent, button);
        if (text && (text.includes('Submit') || text.includes('SUBMIT'))) {
          console.log('✓ Found SUBMIT button, clicking...');
          await button.click();
          await sleep(2000);
          submitted = true;
          break;
        }
      }

      if (submitted) {
        // Look for confirmation
        await sleep(1000);
        const confirmButtons = await page.$$('button');

        for (const button of confirmButtons) {
          const text = await page.evaluate(el => el.textContent, button);
          if (text && (text.includes('Confirm') || text.includes('Yes') || text.includes('OK') || text.includes('确认'))) {
            console.log('✓ Found confirmation button, clicking...');
            await button.click();
            await sleep(2000);
            break;
          }
        }

        // Look for NEXT TASK
        await sleep(1000);
        const nextButtons = await page.$$('button');

        for (const button of nextButtons) {
          const text = await page.evaluate(el => el.textContent, button);
          if (text && (text.includes('NEXT') || text.includes('Next'))) {
            console.log('✓ Found NEXT TASK button, clicking...');
            await button.click();
            console.log('⏳ Waiting for page to refresh...');
            await sleep(5000);
            break;
          }
        }

        taskCount++;
        console.log(`✓ Task ${taskCount} completed!`);
      } else {
        console.log('⚠ No submit button found, retrying...');
        await sleep(2000);
      }

    } catch (error) {
      console.error('Error:', error.message);
      const answer = await waitForUserInput('Continue anyway? (y/n): ');
      if (answer.toLowerCase() !== 'y') {
        break;
      }
    }
  }

  console.log('\n🎉 === COMPLETED ALL 20 TASKS ===');

  await browser.disconnect();
}

main().catch(console.error);
