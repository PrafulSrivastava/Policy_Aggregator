// CRITICAL: This should execute immediately when module loads
console.log('🔴 [INDEX] ========================================');
console.log('🔴 [INDEX] MODULE LOADING - index.tsx is executing');
console.log('🔴 [INDEX] ========================================');

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import ErrorBoundary from './components/ErrorBoundary';

console.log('🔴 [INDEX] ✅ All imports completed successfully');
console.log('[INDEX] Initializing React app...');
console.log('[INDEX] React version:', React.version);
console.log('[INDEX] Environment:', import.meta.env.MODE);
console.log('[INDEX] API Base URL:', import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000 (default)');

const rootElement = document.getElementById('root');
if (!rootElement) {
  console.error('[INDEX] ❌ Root element not found!');
  throw new Error("Could not find root element to mount to");
}

console.log('[INDEX] ✅ Root element found:', rootElement);
console.log('[INDEX] Creating React root...');

try {
  const root = ReactDOM.createRoot(rootElement);
  console.log('[INDEX] ✅ React root created');
  console.log('[INDEX] Rendering app with ErrorBoundary...');
  
  root.render(
    <React.StrictMode>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </React.StrictMode>
  );
  
  console.log('[INDEX] ✅ App render call completed');
  console.log('[INDEX] Waiting for components to mount...');
} catch (error) {
  console.error('[INDEX] ❌ Fatal error rendering app:', error);
  console.error('[INDEX] Error stack:', error instanceof Error ? error.stack : 'No stack trace');
  rootElement.innerHTML = `
    <div style="padding: 20px; font-family: monospace; background: #ff3000; color: white;">
      <h1>Fatal Error Initializing App</h1>
      <pre>${error instanceof Error ? error.stack : String(error)}</pre>
      <p>Check browser console for more details.</p>
    </div>
  `;
}