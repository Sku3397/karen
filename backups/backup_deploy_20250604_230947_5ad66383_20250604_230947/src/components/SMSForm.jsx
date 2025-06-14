import React, { useState } from "react";

const SMSForm = () => {
  const [to, setTo] = useState("");
  const [message, setMessage] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [loading, setLoading] = useState(false);

  console.log('Rendering SMSForm');

  // Simulated send handler
  const handleSend = (e) => {
    e.preventDefault();
    setLoading(true);
    console.log('Sending SMS to', to);
    setTimeout(() => {
      setConfirmation(`SMS sent to ${to}`);
      setLoading(false);
    }, 1000);
  };

  return (
    <form className="sms-form" onSubmit={handleSend}>
      <label>
        To (phone):
        <input
          type="tel"
          value={to}
          onChange={e => setTo(e.target.value)}
          pattern="[0-9+\-() ]+"
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
        {loading ? "Sending..." : "Send SMS"}
      </button>
      {confirmation && <div className="confirmation">{confirmation}</div>}
    </form>
  );
};

export default SMSForm;
