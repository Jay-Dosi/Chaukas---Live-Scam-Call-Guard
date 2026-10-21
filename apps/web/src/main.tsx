import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { TranslationProvider } from '@i18n/useTranslation';
import App from './App';
import './styles/tokens.css';
import './styles/base.css';
import './styles/components.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <TranslationProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </TranslationProvider>
  </React.StrictMode>
);