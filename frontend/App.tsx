import React from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Common';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import RouteSubscriptions from './pages/RouteSubscriptions';
import SourceConfiguration from './pages/SourceConfiguration';
import ChangeHistory from './pages/ChangeHistory';
import ChangeDetail from './pages/ChangeDetail';
import ManualTrigger from './pages/ManualTrigger';
import Settings from './pages/Settings';

console.log('[APP] App component loading...');

const AppRoutes: React.FC = () => {
  console.log('[APP] AppRoutes component rendering...');
  const { isAuthenticated, isLoading } = useAuth();
  console.log('[APP] Auth state - isAuthenticated:', isAuthenticated, 'isLoading:', isLoading);

  if (isLoading) {
    console.log('[APP] ⏳ Showing loading state...');
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    console.log('[APP] 🔒 Not authenticated, showing login routes');
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  console.log('[APP] ✅ Authenticated, showing protected routes');
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/routes" element={<RouteSubscriptions />} />
        <Route path="/sources" element={<SourceConfiguration />} />
        <Route path="/changes" element={<ChangeHistory />} />
        <Route path="/changes/:id" element={<ChangeDetail />} />
        <Route path="/trigger" element={<ManualTrigger />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
};

const App: React.FC = () => {
  console.log('[APP] App component rendering, setting up providers...');
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
};

export default App;