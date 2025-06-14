const {Firestore} = require('@google-cloud/firestore');

const firestore = new Firestore({ projectId: 'demo-project' });

(async () => {
  try {
    const docRef = firestore.collection('test').doc();
    await docRef.set({ hello: 'world', ts: new Date() });
    const doc = await docRef.get();
    console.log('Firestore emulator test success:', doc.data());
    process.exit(0);
  } catch (err) {
    console.error('Firestore emulator test failed:', err.message);
    process.exit(1);
  }
})(); 