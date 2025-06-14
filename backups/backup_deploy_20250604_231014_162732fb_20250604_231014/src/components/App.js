import React from 'react';
import './styles/main.css';
import RealTimeUpdates from './RealTimeUpdates';

function App() {
  return (
    <div className='app'>
      <h1>AI Handyman Secretary Assistant</h1>
      <RealTimeUpdates />
    </div>
  );
}

export default App;