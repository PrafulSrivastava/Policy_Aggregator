import { BrowserRouter, Routes as RouterRoutes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Navigation from './components/Navigation';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import RoutesPage from './pages/Routes';
import AddRoute from './pages/routes/Add';
import RouteDetail from './pages/routes/Detail';
import RouteChanges from './pages/routes/Changes';
import AddSource from './pages/sources/Add';
import Sources from './pages/Sources';
import Changes from './pages/Changes';
import ChangeDetail from './pages/changes/Detail';
import NotificationsSettings from './pages/settings/Notifications';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <RouterRoutes>
          {/* Public route */}
          <Route path="/login" element={<Login />} />
          
          {/* Protected routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Navigation />
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/routes"
            element={
              <ProtectedRoute>
                <Navigation />
                <RoutesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/routes/new"
            element={
              <ProtectedRoute>
                <Navigation />
                <AddRoute />
              </ProtectedRoute>
            }
          />
          <Route
            path="/routes/:routeId"
            element={
              <ProtectedRoute>
                <Navigation />
                <RouteDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/routes/:routeId/changes"
            element={
              <ProtectedRoute>
                <Navigation />
                <RouteChanges />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sources/new"
            element={
              <ProtectedRoute>
                <Navigation />
                <AddSource />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sources"
            element={
              <ProtectedRoute>
                <Navigation />
                <Sources />
              </ProtectedRoute>
            }
          />
          <Route
            path="/changes"
            element={
              <ProtectedRoute>
                <Navigation />
                <Changes />
              </ProtectedRoute>
            }
          />
          <Route
            path="/changes/:changeId"
            element={
              <ProtectedRoute>
                <Navigation />
                <ChangeDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings/notifications"
            element={
              <ProtectedRoute>
                <Navigation />
                <NotificationsSettings />
              </ProtectedRoute>
            }
          />
          
          {/* Catch all - redirect to dashboard */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </RouterRoutes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
