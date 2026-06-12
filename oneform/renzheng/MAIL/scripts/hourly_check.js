const { spawn } = require('child_process');
const path = require('path');

const intervalMs = Number(process.env.MAIL_CHECK_INTERVAL_MS || 3600_000);
const checker = path.resolve(__dirname, 'check_new_tasks.js');

function stamp() {
  return new Date().toISOString();
}

function runOnce() {
  console.log(`[${stamp()}] starting MAIL task check`);
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [checker], {
      cwd: path.resolve(__dirname, '..', '..'),
      env: process.env,
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    child.stdout.on('data', (chunk) => process.stdout.write(`[checker] ${chunk}`));
    child.stderr.on('data', (chunk) => process.stderr.write(`[checker:error] ${chunk}`));
    child.on('close', (code) => {
      console.log(`[${stamp()}] check exited with code ${code}`);
      resolve();
    });
    child.on('error', (error) => {
      console.error(`[${stamp()}] failed to start checker: ${error.stack || error.message}`);
      resolve();
    });
  });
}

async function main() {
  while (true) {
    await runOnce();
    console.log(`[${stamp()}] next check in ${Math.round(intervalMs / 1000)}s`);
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
