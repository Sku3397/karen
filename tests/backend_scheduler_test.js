require('dotenv').config();
const { scheduleAppointment } = require('../functions/schedulerFunction');

const req = {
  body: {
    appointmentDetails: {
      date: '2025-01-01',
      time: '10:00',
      client: 'test-client'
    }
  }
};

const res = {
  send: (data) => {
    console.log('PASS: Scheduler function executed:', data);
    process.exit(0);
  }
};

scheduleAppointment(req, res).catch(e => {
  console.error('FAIL: Scheduler function error:', e);
  process.exit(1);
}); 