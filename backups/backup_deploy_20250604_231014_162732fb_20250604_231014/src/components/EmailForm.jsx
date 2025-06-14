import React, { useState } from "react";

const EmailForm = () => {
  const [to, setTo] = useState("");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [loading, setLoading] = useState(false);

  console.log('Rendering EmailForm');

  // Simulated send handler
  const handleSend = (e) => {
    e.preventDefault();
    setLoading(true);
    console.log('Sending email to', to, 'with subject', subject);
    setTimeout(() => {
      setConfirmation(`Email sent to ${to}`);
      setLoading(false);
    }, 1000);
  };

  return (
    <form className="email-form" onSubmit={handleSend}>
      <label>
        To:
        <input
          type="email"
          value={to}
          onChange={e => setTo(e.target.value)}
          required
        />
      </label>
      <label>
        Subject:
        <input
          type="text"
          value={subject}
          onChange={e => setSubject(e.target.value)}
          required
        />
      </label>
      <label>
        Message:
        <textarea
          value={message}
          onChange={e => setMessage(e.target.value)}
          required
        />
      </label>
      <button type="submit" disabled={loading}>
        {loading ? "Sending..." : "Send Email"}
      </button>
      {confirmation && <div className="confirmation">{confirmation}</div>}
    </form>
  );
};

export default EmailForm;
