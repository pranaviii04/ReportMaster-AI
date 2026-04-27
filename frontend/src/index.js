/**
 * ReportMaster AI — React 18 Entry Point
 * Mounts the root <App /> component using the new createRoot API.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error(
    '[ReportMaster AI] Could not find #root element. Check public/index.html.'
  );
}

const root = ReactDOM.createRoot(rootElement);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
