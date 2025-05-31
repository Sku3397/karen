const { spawn } = require('child_process');

const tests = [
  'tests/frontend_smoke_test.js',
  'tests/backend_notification_test.js',
  'tests/backend_billing_test.js',
  'tests/backend_scheduler_test.js',
  'tests/backend_gmail_test.js',
];

let failed = false;

function runTest(test, cb) {
  console.log(`\n=== Running: ${test} ===`);
  const proc = spawn('node', [test], { stdio: 'inherit' });
  proc.on('close', code => {
    if (code !== 0) {
      console.error(`FAIL: ${test} exited with code ${code}`);
      failed = true;
    } else {
      console.log(`PASS: ${test}`);
    }
    cb();
  });
}

(function runAll(i) {
  if (i >= tests.length) {
    if (failed) {
      console.error('\nSome tests failed.');
      process.exit(1);
    } else {
      console.log('\nAll tests passed.');
      process.exit(0);
    }
  } else {
    runTest(tests[i], () => runAll(i + 1));
  }
})(0); 