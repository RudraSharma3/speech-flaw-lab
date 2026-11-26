import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import { IS_STATIC_DEMO, installStaticApi } from './lib/staticApi';
import './index.css';

if (IS_STATIC_DEMO) {
  installStaticApi();
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
