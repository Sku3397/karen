import React, { useState } from "react";
import EmailForm from "./EmailForm";
import SMSForm from "./SMSForm";
import "../styles/interaction.css";

const ClientInteractionInterface = () => {
  const [mode, setMode] = useState("email");
  console.log('Rendering ClientInteractionInterface, mode:', mode);

  return (
    <div className="interaction-container">
      <h2>Client Communication</h2>
      <div className="interaction-tabs">
        <button
          className={mode === "email" ? "active" : ""}
          onClick={() => { console.log('Switching to email mode'); setMode("email"); }}
        >
          Email
        </button>
        <button
          className={mode === "sms" ? "active" : ""}
          onClick={() => { console.log('Switching to sms mode'); setMode("sms"); }}
        >
          SMS
        </button>
      </div>
      <div className="interaction-form">
        {mode === "email" ? <EmailForm /> : <SMSForm />}
      </div>
    </div>
  );
};

export default ClientInteractionInterface;
