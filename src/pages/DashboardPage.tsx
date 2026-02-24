import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { modelAPI } from '../services/api';
import { LoadingSpinner, ErrorMessage } from '../components/Common';
import { StatusBadge } from '../components/StatusBadge';
import { ModelRegistrationModal } from '../components/ModelRegistrationModal';

interface Model {
  id: string | number;
  model_name: string;
  name?: string;
  status: string;
  deployment_status?: string;
  risk_score?: number;
  version: string;
  created_at: string;
  last_updated?: string;
}

export function DashboardPage() {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Verify token exists before making request
      const token = localStorage.getItem('authToken');
      if (!token) {
        console.warn('No token found - redirecting to login');
        navigate('/login', { replace: true });
        return;
      }
      
      const response = await modelAPI.getModels();
      // Handle both response formats: { items: [...] } or { models: [...] }
      const modelsList = response.data.items || response.data.models || response.data || [];
      setModels(Array.isArray(modelsList) ? modelsList : []);
      setRetryCount(0);
    } catch (err: any) {
      console.error('Error fetching models:', err);
      
      const errorMsg = err.message || 'Failed to load models';
      
      // Check if it's an auth error
      if (errorMsg.includes('Could not validate credentials') || 
          errorMsg.includes('Unauthorized') ||
          errorMsg.includes('401')) {
        console.warn('Authentication error - clearing token and redirecting');
        localStorage.removeItem('authToken');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('userName');
        navigate('/login', { replace: true });
        return;
      }
      
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterModel = async (formData: any) => {
    try {
      // Parse schema_definition if it's a string
      const modelData = {
        ...formData,
        schema_definition: formData.schema_definition 
          ? JSON.parse(formData.schema_definition) 
          : null,
        training_accuracy: formData.training_accuracy 
          ? parseFloat(formData.training_accuracy) 
          : null,
        fairness_baseline: formData.fairness_baseline 
          ? parseFloat(formData.fairness_baseline) 
          : null,
      };

      await modelAPI.createModel(modelData);
      
      // Refresh the models list
      await fetchModels();
    } catch (err: any) {
      console.error('Error registering model:', err);
      setError(err.message || 'Failed to register model');
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} onRetry={fetchModels} />;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>📊 Dashboard</h1>
          <p>Monitor all AI models and their governance status</p>
        </div>
        <button 
          className="btn btn-primary"
          onClick={() => setIsModalOpen(true)}
        >
          + Register Model
        </button>
      </div>

      <div className="models-grid">
        {models.length === 0 ? (
          <div className="empty-state">
            <p>No models found. Start by registering a model.</p>
            <button 
              className="btn btn-primary"
              onClick={() => setIsModalOpen(true)}
            >
              Register Your First Model
            </button>
          </div>
        ) : (
          models.map((model) => (
            <div
              key={model.id || Math.random()}
              className="model-card"
              onClick={() => navigate(`/model/${model.id}`)}
            >
              <div className="card-header">
                <h3>{model.name || model.model_name || 'Unnamed Model'}</h3>
                <StatusBadge status={model.status || 'draft'}>{model.status || 'draft'}</StatusBadge>
              </div>

              <div className="card-body">
                <div className="metric">
                  <span className="label">Version</span>
                  <span className="value">{model.version || 'N/A'}</span>
                </div>
                <div className="metric">
                  <span className="label">Risk Score</span>
                  <span className={`value risk-${getRiskLevel(model.risk_score)}`}>
                    {typeof model.risk_score === 'number' ? model.risk_score.toFixed(2) : 'N/A'}
                  </span>
                </div>
                <div className="metric">
                  <span className="label">Last Updated</span>
                  <span className="value">
                    {model.last_updated || model.created_at ? new Date(model.last_updated || model.created_at).toLocaleDateString() : 'N/A'}
                  </span>
                </div>
              </div>

              <div className="card-footer">
                <button className="btn btn-secondary btn-sm">
                  View Details →
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <ModelRegistrationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleRegisterModel}
      />
    </div>
  );
}

function getRiskLevel(score: number | undefined): 'low' | 'medium' | 'high' {
  const numScore = typeof score === 'number' ? score : 0;
  if (numScore < 0.3) return 'low';
  if (numScore < 0.7) return 'medium';
  return 'high';
}