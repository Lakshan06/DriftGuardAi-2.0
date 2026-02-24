import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';
import { ErrorMessage } from '../components/Common';

interface LoginPageProps {
  onLogin: () => void;
}

interface LoginResponse {
  access_token?: string;
  token?: string;
  user?: {
    email: string;
    id?: string;
    name?: string;
  };
  email?: string;
  message?: string;
  success?: boolean;
}

export function LoginPage({ onLogin }: LoginPageProps) {
  const [email, setEmail] = useState('testuser@example.com');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setDebugInfo('');
    setLoading(true);

    try {
      if (!email || !password) {
        throw new Error('Email and password are required');
      }

      const response = await authAPI.login(email, password);
      const data: LoginResponse = response.data;

      setDebugInfo(`Response received: ${JSON.stringify(data)}`);

      // Handle different response formats
      let token = data.access_token || data.token;
      let userEmail = data.user?.email || data.email || email;
      let userName = data.user?.name || 'User';

      // Validate we got a token
      if (!token) {
        throw new Error('No authentication token received from server');
      }

      // Validate token is a string
      if (typeof token !== 'string') {
        throw new Error('Invalid token format from server');
      }

      // Store token and user info
      localStorage.setItem('authToken', token);
      localStorage.setItem('userEmail', userEmail);
      localStorage.setItem('userName', userName);

      // Call parent callback
      onLogin();

      // Navigate to dashboard
      navigate('/dashboard');

    } catch (err: any) {
      let errorMessage = 'Login failed. Please try again.';

      // Handle different error types
      if (err.response) {
        // Server responded with error status
        errorMessage = 
          err.response.data?.message ||
          err.response.data?.error ||
          err.response.statusText ||
          `Server error: ${err.response.status}`;
      } else if (err.request) {
        // Request was made but no response
        errorMessage = 'No response from server. Is the backend running at ' + 
          (import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api') + '?';
      } else {
        // Error in request setup
        errorMessage = err.message || 'Login failed';
      }

      setError(errorMessage);
      setDebugInfo(`Error details: ${JSON.stringify({
        status: err.response?.status,
        data: err.response?.data,
        message: err.message,
      })}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-card">
          <h1 className="login-title">🛡️ DriftGuardAI</h1>
          <p className="login-subtitle">AI Model Governance Platform</p>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                disabled={loading}
              />
            </div>

            {error && (
              <div style={{ marginBottom: '16px' }}>
                <ErrorMessage message={error} />
              </div>
            )}

            {debugInfo && (
              <div 
                style={{
                  marginBottom: '16px',
                  padding: '10px',
                  background: '#f0f0f0',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontFamily: 'monospace',
                  color: '#666',
                  maxHeight: '100px',
                  overflow: 'auto',
                }}
              >
                <strong>Debug:</strong> {debugInfo}
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary btn-block"
              disabled={loading}
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>

          <div className="login-footer">
            <p>Demo credentials: demo@driftguardai.com / password123</p>
            <p style={{ fontSize: '12px', marginTop: '8px', color: '#666' }}>
              Backend URL: {import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}