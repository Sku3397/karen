import React, { useEffect, useState } from 'react';
import { WebSocketAPI } from '../api/WebSocketAPI';

function RealTimeUpdates() {
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    const ws = WebSocketAPI.subscribe('updates');
    ws.onmessage = (message) => {
      setMessages((prevMessages) => [...prevMessages, message.data]);
    };
    return () => ws.close();
  }, []);

  return (
    <div>
      {messages.map((msg, index) => (
        <div key={index}>{msg}</div>
      ))}
    </div>
  );
}

export default RealTimeUpdates;