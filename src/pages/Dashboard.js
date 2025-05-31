import React, { useEffect, useState } from 'react';
import { fetchTasks } from '../api/client';
import useWebSocket from '../hooks/useWebSocket';

export default function Dashboard() {
  const [tasks, setTasks] = useState([]);
  const updates = useWebSocket('wss://your-websocket-domain.com/updates');

  useEffect(() => {
    fetchTasks().then(response => setTasks(response.data)).catch(error => console.error(error));
  }, []);

  useEffect(() => {
    if (updates) {
      // Handle the incoming WebSocket data
      console.log('Received updates:', updates);
    }
  }, [updates]);

  return (
    <div>
      <h1>Dashboard</h1>
      {/* Render tasks and handle updates */}
    </div>
  );
}