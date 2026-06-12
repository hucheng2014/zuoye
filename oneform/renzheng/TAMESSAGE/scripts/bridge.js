/**
 * bridge.js — TAMESSAGE task lifecycle: keepalive 540s (9min) → fill → submit
 */
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const RUNS = path.resolve(__dirname, '..', 'runs');
const { KEEPALIVE_MS } = require('./config');
const ANSWERS = process.argv[2] || path.join(RUNS, 'current-answers.json');

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  process.stdout.write(line);
  fs.appendFileSync(path.join(RUNS, 'bridge.log'), line);
}

function killKeepalive() {
  const pidFile = path.join(RUNS, 'keepalive.pid');
  if (!fs.existsSync(pidFile)) return;
  const pid = parseInt(fs.readFileSync(pidFile, 'utf8').trim(), 10);
  if (pid) {
    try { process.kill(pid, 'SIGTERM'); } catch {}
  }
  try { fs.unlinkSync(pidFile); } catch {}
}

function runNode(script, args = []) {
  return new Promise((resolve, reject) => {
    const child = spawn('node', [script, ...args], {
      cwd: path.resolve(__dirname, '..', '..'),
      stdio: 'inherit',
    });
    child.on('close', (code) => (code === 0 ? resolve() : reject(new Error(`${script} exited ${code}`))));
  });
}

async function main() {
  fs.mkdirSync(RUNS, { recursive: true });
  log(`Bridge started. Keepalive ${KEEPALIVE_MS / 1000}s, answers=${ANSWERS}`);

  // Stop any competing CDP scripts
  try { execSync('pkill -f "starshot_keepalive.js" || true', { stdio: 'ignore' }); } catch {}
  killKeepalive();

  // Start keepalive in background
  const keepaliveScript = path.join(__dirname, 'keepalive.js');
  const keepaliveLog = path.join(RUNS, 'keepalive.log');
  const keepaliveChild = spawn('node', [keepaliveScript], {
    detached: true,
    stdio: ['ignore', fs.openSync(keepaliveLog, 'a'), fs.openSync(keepaliveLog, 'a')],
  });
  keepaliveChild.unref();
  log(`Keepalive started pid=${keepaliveChild.pid}`);

  const start = Date.now();
  while (Date.now() - start < KEEPALIVE_MS) {
    const remaining = Math.ceil((KEEPALIVE_MS - (Date.now() - start)) / 1000);
    if (remaining % 60 === 0 || remaining <= 30) log(`Keepalive: ${remaining}s remaining`);
    await new Promise((r) => setTimeout(r, 10000));
  }
  log('Keepalive duration reached. Stopping keepalive for fill+submit.');

  killKeepalive();
  await new Promise((r) => setTimeout(r, 2000));

  await runNode(path.join(__dirname, 'fill_task.js'), ['--answers', ANSWERS, '--submit']);
  log('Task submitted successfully.');
}

main().catch((err) => {
  log(`Bridge failed: ${err.message}`);
  process.exit(1);
});
