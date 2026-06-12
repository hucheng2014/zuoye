const puppeteer = require('puppeteer-core');

const CDP_URL = 'http://127.0.0.1:9235';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log('Connecting to browser via CDP...');

  const browser = await puppeteer.connect({
    browserURL: CDP_URL,
    defaultViewport: null
  });

  const pages = await browser.pages();
  const page = pages[0] || await browser.newPage();

  console.log('Connected to browser');
  console.log('Current URL:', await page.url());

  // Wait for user to be ready
  console.log('\n=== READY TO START ===');
  console.log('Please ensure you are on the task page.');
  console.log('I will look for the ACCEPT button to start the first task.');
  console.log('Press Ctrl+C if you need to stop.\n');

  await sleep(2000);

  let taskCount = 0;
  const maxTasks = 20;

  while (taskCount < maxTasks) {
    console.log(`\n--- Task ${taskCount + 1}/${maxTasks} ---`);

    // Check if ACCEPT button exists
    const acceptButton = await page.$('button:has-text("ACCEPT"), button:has-text("Accept")').catch(() => null);

    if (acceptButton) {
      console.log('Found ACCEPT button, clicking...');
      await acceptButton.click();
      await sleep(3000);
    }

    // Get page content to analyze the task
    const pageContent = await page.content();
    console.log('Page loaded, analyzing task...');

    // Take a screenshot for reference
    await page.screenshot({ path: `/tmp/task_${taskCount + 1}.png`, fullPage: true });
    console.log(`Screenshot saved: /tmp/task_${taskCount + 1}.png`);

    // Here we would analyze the task and fill in the ratings
    // For now, let's pause and let the user see what's happening
    console.log('\nTask page is ready. Please review the task.');
    console.log('Waiting 5 seconds before proceeding...');
    await sleep(5000);

    // Look for submit button
    const submitButton = await page.$('button:has-text("Submit"), button:has-text("SUBMIT")').catch(() => null);

    if (submitButton) {
      console.log('Found SUBMIT button. Please fill in your ratings first.');
      console.log('Waiting 10 seconds for you to complete the ratings...');
      await sleep(10000);

      console.log('Clicking SUBMIT...');
      await submitButton.click();
      await sleep(2000);

      // Look for confirmation dialog
      const confirmButton = await page.$('button:has-text("Confirm"), button:has-text("Yes"), button:has-text("OK")').catch(() => null);
      if (confirmButton) {
        console.log('Found confirmation button, clicking...');
        await confirmButton.click();
        await sleep(2000);
      }

      // Look for NEXT TASK button
      const nextButton = await page.$('button:has-text("NEXT TASK"), button:has-text("Next Task")').catch(() => null);
      if (nextButton) {
        console.log('Found NEXT TASK button, clicking...');
        await nextButton.click();
        await sleep(5000); // Wait for page refresh
      }

      taskCount++;
    } else {
      console.log('No submit button found. Waiting...');
      await sleep(3000);
    }
  }

  console.log('\n=== COMPLETED ALL 20 TASKS ===');

  await browser.disconnect();
}

main().catch(console.error);
