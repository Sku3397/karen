const http = require('http');
const fs = require('fs');
const path = require('path');

const endpoints = [
  {
    name: 'generateInvoice',
    method: 'POST',
    path: '/karen-437100/us-central1/generateInvoice',
    data: JSON.stringify({ userId: 'testuser', items: ['item1', 'item2'] })
  },
  {
    name: 'scheduleAppointment',
    method: 'POST',
    path: '/karen-437100/us-central1/scheduleAppointment',
    data: JSON.stringify({ appointmentDetails: { date: '2025-06-01', time: '10:00', client: 'testuser' } })
  }
];

const results = [];

function testEndpoint(endpoint, cb) {
  const options = {
    hostname: '127.0.0.1',
    port: 5001,
    path: endpoint.path,
    method: endpoint.method,
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': endpoint.data ? Buffer.byteLength(endpoint.data) : 0
    }
  };

  const req = http.request(options, (res) => {
    let body = '';
    res.on('data', chunk => body += chunk);
    res.on('end', () => {
      results.push({
        endpoint: endpoint.name,
        status: res.statusCode,
        body: body,
        error: null
      });
      cb();
    });
  });

  req.on('error', (e) => {
    results.push({
      endpoint: endpoint.name,
      status: null,
      body: null,
      error: e.message
    });
    cb();
  });

  if (endpoint.data) req.write(endpoint.data);
  req.end();
}

function runTests(i = 0) {
  if (i >= endpoints.length) {
    const resultsDir = path.resolve(__dirname, '../tests/results');
    if (!fs.existsSync(resultsDir)) {
      fs.mkdirSync(resultsDir, { recursive: true });
    }
    const resultsPath = path.join(resultsDir, 'backend_api_results.json');
    fs.writeFileSync(resultsPath, JSON.stringify(results, null, 2));
    console.log('Backend API smoke test complete. Results written to ' + resultsPath);
    process.exit(0);
  } else {
    testEndpoint(endpoints[i], () => runTests(i + 1));
  }
}

runTests(); 