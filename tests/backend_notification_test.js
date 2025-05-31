require('dotenv').config();
const { sendNotification } = require('../functions/notificationFunction');

(async () => {
  try {
    await sendNotification('Test message', 'test-topic');
    console.log('PASS: Notification function executed');
    process.exit(0);
  } catch (e) {
    console.error('FAIL: Notification function error:', e);
    process.exit(1);
  }
})(); 