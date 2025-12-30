import { HashRouter, Routes as RouterRoutes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Navigation from './components/Navigation';
import Footer from './components/Footer';
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
import SystemSettings from './pages/settings/System';
import Trigger from './pages/Trigger';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <HashRouter>
        <RouterRoutes>
          {/* Public route */}
          <Route path="/login" element={<Login />} />
          
          {/* Protected routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Navigation />
                <div className="pb-12">
                  <Dashboard />
                </div>
                <Footer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/routes"
            element={
              <ProtectedRoute>
                <Navigation />
                <div className="pb-12">
                  <RoutesPage />
                </div>
                <Footer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/routes/new"
            element={
              <ProtectedRoute>
                <Navigation />
                <div className="pb-12">
                  <AddRoute />
                </div>
                <Footer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/routes/:routeId"
            element={
              <ProtectedRoute>
                <Navigation />
                <div className="pb-12">
                  <RouteDetail />
                </div>
                <Footer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/routes/:routeId/changes"
            element={
              <ProtectedRoute>
                <Navigation />
                <div className="pb-12">
                  <RouteChanges />
                </div>
                <Footer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sources/new"
            element={
              <ProtectedRoute>
                <Navigation />
                <div className="pb-12">
                  <AddSource />
                </div>
                <Footer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sources"
            element={
              <ProtectedRoute>
                <Navigation />
                <div className="pb-12">
                  <Sources />
                </div>
                <Footer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/changes"
            element={
              <ProtectedRoute>
                <Navigation />
                <div className="pb-12">
                  <Changes />
                </div>
                <Footer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/changes/:changeId"
            element={
              <ProtectedRoute>
                <Navigation />
                <div className="pb-12">
                  <ChangeDetail />
                </div>
                <Footer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings/notifications"
            element={
              <ProtectedRoute>
                <Navigation />
                <div className="pb-12">
                  <NotificationsSettings />
                </div>
                <Footer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings/system"
            element={
              <ProtectedRoute>
                <Navigation />
                <div className="pb-12">
                  <SystemSettings />
                </div>
                <Footer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/trigger"
            element={
              <ProtectedRoute>
                <Navigation />
                <div className="pb-12">
                  <Trigger />
                </div>
                <Footer />
              </ProtectedRoute>
            }
          />
          
          {/* Catch all - redirect to dashboard */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </RouterRoutes>
      </HashRouter>
    </AuthProvider>
  );
}

export default App;
