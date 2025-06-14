import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import GlobalErrorBoundary from './GlobalErrorBoundary.js';
import '../public/css/style.css';

console.log('Mounting React app in index.js');

ReactDOM.render(
  <GlobalErrorBoundary>
    <App />
  </GlobalErrorBoundary>,
  document.getElementById('root')
);