import React, { useState } from 'react';
import { submitFeedback } from '../api/feedback';

export const FeedbackForm = () => {
  const [feedback, setFeedback] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    await submitFeedback(feedback);
    setFeedback('');
    alert('Feedback submitted successfully!');
  };

  return (
    <form onSubmit={handleSubmit}>
      <textarea
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        placeholder='Enter your feedback here...'
        required
      />
      <button type='submit'>Submit Feedback</button>
    </form>
  );
};