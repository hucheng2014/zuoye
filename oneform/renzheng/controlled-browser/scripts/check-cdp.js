const http = require('http');

const endpoint = process.argv[2] || process.env.CDP_ENDPOINT || 'http://127.0.0.1:9235';
const url = new URL('/json/version', endpoint);

http.get(url, (res) => {
  let body = '';
  res.setEncoding('utf8');
  res.on('data', (chunk) => body += chunk);
  res.on('end', () => {
    console.log(body);
    process.exit(res.statusCode >= 200 && res.statusCode < 300 ? 0 : 1);
  });
}).on('error', (error) => {
  console.error(error.message);
  process.exit(1);
});
