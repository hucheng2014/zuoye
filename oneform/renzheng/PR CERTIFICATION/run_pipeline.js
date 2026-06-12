const { checkAndAccept, extractTask, sleep } = require('./pr_automation_helper');
const fs = require('fs');
const path = require('path');
const { saveTask, ROOT } = require('./task_utils');

async function main() {
  console.log('=== PR Task Extraction Pipeline ===');

  console.log('Checking for ACCEPT button...');
  const accepted = await checkAndAccept();
  if (accepted) {
    console.log('✓ Found and clicked ACCEPT button. Waiting for page to load...');
    await sleep(4000);
  } else {
    console.log('No active ACCEPT button found or already accepted.');
  }

  console.log('Extracting current task details...');
  const task = await extractTask();
  const enriched = saveTask(task);
  console.log(`✓ Task extracted fingerprint=${enriched.fingerprint}`);

  let markdown = `# Current Task Analysis

**Locale:** \`${enriched.locale}\`
**Fingerprint:** \`${enriched.fingerprint}\`

## User Request
\`\`\`text
${enriched.userRequest}
\`\`\`

## Responses

`;

  for (const [key, value] of Object.entries(enriched.responses)) {
    markdown += `### ${key}\n\`\`\`text\n${value}\n\`\`\`\n\n`;
  }

  markdown += `---
*End of current task extraction.*
`;

  fs.writeFileSync(path.join(ROOT, 'current_task_analysis.md'), markdown);
  console.log('✓ Saved current_task.json + current_task_analysis.md');
  console.log('================================================');
}

main().catch((error) => {
  console.error('Extraction pipeline failed:', error);
  process.exit(1);
});
