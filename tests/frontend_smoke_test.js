const http = require('http');

function fetch(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ status: res.statusCode, body: data }));
    }).on('error', reject);
  });
}

(async () => {
  try {
    const { status, body } = await fetch('http://localhost:8082');
    if (status !== 200) {
      console.error('FAIL: HTTP status', status);
      process.exit(1);
    }
    if (!body.match(/<div id=['"]root['"]>/)) {
      console.error('FAIL: Missing React root div');
      process.exit(2);
    }
    if (!body.match(/Client Communication|AI Handyman|Secretary|Assistant/i)) {
      console.error('FAIL: Expected UI text not found');
      process.exit(3);
    }
    console.log('PASS: Frontend smoke test');
    process.exit(0);
  } catch (e) {
    console.error('FAIL: Error fetching frontend:', e);
    process.exit(4);
  }
})(); 