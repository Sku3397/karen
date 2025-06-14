import React, { useEffect, useState } from 'react';
import { db } from '../api/firebase';
import { collection, getDocs } from 'firebase/firestore';

export const FeedbackDisplay = () => {
  const [feedbacks, setFeedbacks] = useState([]);

  useEffect(() => {
    const fetchFeedback = async () => {
      const feedbackCollection = collection(db, 'feedback');
      const feedbackSnapshot = await getDocs(feedbackCollection);
      const feedbackList = feedbackSnapshot.docs.map(doc => doc.data());
      setFeedbacks(feedbackList);
    };
    fetchFeedback();
  }, []);

  return (
    <div>
      {feedbacks.map((feedback, index) => (
        <div key={index}>{feedback.feedback}</div>
      ))}
    </div>
  );
};