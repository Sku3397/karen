const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  const url = 'http://localhost:8080';
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  let errors = [];
  let failedRequests = [];

  // Capture console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  // Capture failed network requests
  page.on('requestfailed', request => {
    failedRequests.push({
      url: request.url(),
      error: request.failure() && request.failure().errorText
    });
  });

  try {
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
    // Check for visible content in the root/app div
    const content = await page.evaluate(() => {
      const root = document.getElementById('root') || document.getElementById('app');
      return root ? root.innerText : null;
    });
    await page.screenshot({ path: 'tests/results/screenshot.png' });
    fs.writeFileSync('tests/results/content.txt', content || 'No content found');
    fs.writeFileSync('tests/results/console_errors.json', JSON.stringify(errors, null, 2));
    fs.writeFileSync('tests/results/failed_requests.json', JSON.stringify(failedRequests, null, 2));
    if (!content || content.trim() === '') {
      console.error('No visible content found in root/app div.');
      process.exit(1);
    }
    if (errors.length > 0) {
      console.error('Console errors detected:', errors);
      process.exit(2);
    }
    if (failedRequests.length > 0) {
      console.error('Failed network requests detected:', failedRequests);
      process.exit(3);
    }
    console.log('Frontend smoke test passed.');
    process.exit(0);
  } catch (err) {
    fs.writeFileSync('tests/results/puppeteer_error.log', err.stack || err.toString());
    console.error('Puppeteer test failed:', err);
    process.exit(4);
  } finally {
    await browser.close();
  }
})(); 