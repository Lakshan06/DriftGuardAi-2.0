import { ReactNode, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const token = localStorage.getItem('authToken');
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) {
      console.warn('No token found - redirecting to login');
      navigate('/login', { replace: true });
    }
  }, [token, navigate]);

  if (!token) {
    return (
      <div className="app-loading">
        <div className="spinner" />
        <h2>Redirecting to login...</h2>
      </div>
    );
  }

  return <>{children}</>;
}