const {Firestore} = require('@google-cloud/firestore');

let firestore;
if (process.env.FIRESTORE_EMULATOR_HOST) {
  firestore = new Firestore({ projectId: 'demo-project' });
} else {
  firestore = new Firestore();
}

exports.generateInvoice = async (req, res) => {
  // Retrieve billing details from request
  const {userId, items} = req.body;

  // Calculate total cost
  let totalCost = 0;
  items.forEach(item => {
    totalCost += item.price;
  });

  // Store invoice in Firestore
  const docRef = firestore.collection('invoices').doc();
  await docRef.set({
    userId,
    items,
    totalCost,
    createdAt: Firestore.Timestamp.now()
  });

  res.send({message: 'Invoice generated successfully', invoiceId: docRef.id});
};