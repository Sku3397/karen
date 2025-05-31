require('dotenv').config();
const { generateInvoice } = require('../functions/billingFunction');

const req = {
  body: {
    userId: 'test-user',
    items: [
      { name: 'item1', price: 10 },
      { name: 'item2', price: 20 }
    ]
  }
};

const res = {
  send: (data) => {
    console.log('PASS: Billing function executed:', data);
    process.exit(0);
  }
};

generateInvoice(req, res).catch(e => {
  console.error('FAIL: Billing function error:', e);
  process.exit(1);
}); 