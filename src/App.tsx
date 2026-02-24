import { Routes, Route, Navigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ModelDetailPage } from './pages/ModelDetailPage';
import { GovernancePage } from './pages/GovernancePage';
import { AuditPage } from './pages/AuditPage';
import { CommandCenterPage } from './pages/CommandCenterPage';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { ErrorBoundary } from './components/ErrorBoundary';

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState('');

  useEffect(() => {
    // Validate token on app load
    const validateAuth = () => {
      try {
        const token = localStorage.getItem('authToken');
        const userEmail = localStorage.getItem('userEmail');
        
        // Token must be a non-empty string
        const isValidToken = typeof token === 'string' && token.length > 0;
        const isValidEmail = typeof userEmail === 'string' && userEmail.length > 0;
        
        if (isValidToken && isValidEmail) {
          setIsAuthenticated(true);
          setAuthError('');
        } else {
          setIsAuthenticated(false);
          if (token) {
            // Clear invalid token
            localStorage.removeItem('authToken');
            localStorage.removeItem('userEmail');
            localStorage.removeItem('userName');
          }
        }
      } catch (error) {
        console.error('Auth validation error:', error);
        setIsAuthenticated(false);
        setAuthError('Authentication validation failed');
      } finally {
        setLoading(false);
      }
    };
    
    validateAuth();
  }, []);

  if (loading) {
    return (
      <div className="app-loading">
        <div className="spinner" />
        <h2>Loading DriftGuardAI...</h2>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage onLogin={() => setIsAuthenticated(true)} />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <ErrorBoundary>
      <div className="app-layout">
        <Navbar onLogout={() => {
          setIsAuthenticated(false);
          localStorage.removeItem('authToken');
          localStorage.removeItem('userEmail');
          localStorage.removeItem('userName');
        }} />
        <div className="app-content">
          <Sidebar />
          <main className="main-content">
            <Routes>
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <DashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/command-center"
                element={
                  <ProtectedRoute>
                    <CommandCenterPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/model/:modelId"
                element={
                  <ProtectedRoute>
                    <ModelDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/governance"
                element={
                  <ProtectedRoute>
                    <GovernancePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/audit"
                element={
                  <ProtectedRoute>
                    <AuditPage />
                  </ProtectedRoute>
                }
              />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </ErrorBoundary>
  );
}