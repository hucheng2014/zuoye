// Hard timeout for short-lived scripts: force-kill even if Playwright or the
// main event loop gets stuck. Require this at the very top of short-lived scripts.
const { spawn } = require('child_process');

const ms = parseInt(process.env.SCRIPT_TIMEOUT_MS, 10) || 60000;
const parentPid = process.pid;

let cleaned = false;
let watchdog = null;

function cleanup() {
  if (cleaned) return;
  cleaned = true;
  if (watchdog && !watchdog.killed) {
    try { watchdog.kill('SIGKILL'); } catch {}
  }
}

process.on('exit', cleanup);
process.on('SIGINT', () => {
  cleanup();
  process.exit(130);
});
process.on('SIGTERM', () => {
  cleanup();
  process.exit(143);
});
process.on('uncaughtException', (err) => {
  cleanup();
  throw err;
});

watchdog = spawn(process.execPath, [
  '-e',
  `
    const targetPid = ${parentPid};
    const timeoutMs = ${ms};
    setTimeout(() => {
      try {
        process.stderr.write("[timeout] Watchdog killing pid " + targetPid + " after " + (timeoutMs / 1000) + "s\\n");
      } catch {}
      try { process.kill(targetPid, 'SIGKILL'); } catch {}
      process.exit(0);
    }, timeoutMs);
  `,
], {
  stdio: 'ignore',
  detached: true,
});

watchdog.unref();
