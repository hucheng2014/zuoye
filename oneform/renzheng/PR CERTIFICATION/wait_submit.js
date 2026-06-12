/** Wait until submit.log gains N new SUCCESS lines since start */
const fs = require('fs');
const path = require('path');
const LOG = path.join(__dirname, 'runs', 'submit.log');

function count() {
  if (!fs.existsSync(LOG)) return 0;
  return fs.readFileSync(LOG, 'utf8').split('\n').filter((l) => l.includes('SUCCESS total')).length;
}

const target = count() + parseInt(process.argv[2] || '1', 10);
const maxMs = parseInt(process.argv[3] || '900000', 10);
const t0 = Date.now();

(async () => {
  while (Date.now() - t0 < maxMs) {
    if (count() >= target) {
      console.log('OK', fs.readFileSync(LOG, 'utf8').split('\n').filter((l) => l.includes('SUCCESS total')).pop());
      process.exit(0);
    }
    await new Promise((r) => setTimeout(r, 20000));
    process.stdout.write(`wait ${Math.round((Date.now() - t0) / 1000)}s count=${count()}/${target}\n`);
  }
  console.error('TIMEOUT');
  process.exit(1);
})();
