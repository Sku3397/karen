const functions = require('firebase-functions');
const billing = require('./billingFunction');
const notification = require('./notificationFunction');
const scheduler = require('./schedulerFunction');

exports.generateInvoice = functions.https.onRequest(billing.generateInvoice);
exports.sendNotification = functions.https.onRequest(notification.sendNotification);
exports.scheduleAppointment = functions.https.onRequest(scheduler.scheduleAppointment); 