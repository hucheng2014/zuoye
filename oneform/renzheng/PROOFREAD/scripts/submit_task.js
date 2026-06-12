require('./_timeout');
const { fork } = require('child_process');
const path = require('path');

console.log('Redirecting submission to full_submit.js to enforce strict validation...');
const child = fork(path.join(__dirname, 'full_submit.js'), process.argv.slice(2));
child.on('exit', (code) => {
  process.exit(code || 0);
});
