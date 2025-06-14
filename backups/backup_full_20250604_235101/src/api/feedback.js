import { db } from './firebase';
import { collection, addDoc } from 'firebase/firestore';

export const submitFeedback = async (feedback) => {
  try {
    await addDoc(collection(db, 'feedback'), {
      feedback,
      timestamp: new Date()
    });
  } catch (error) {
    console.error('Error submitting feedback: ', error);
  }
};