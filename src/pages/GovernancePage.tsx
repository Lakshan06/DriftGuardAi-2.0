import { useState, useEffect } from 'react';
import { governanceAPI, modelAPI } from '../services/api';
import { LoadingSpinner, ErrorMessage } from '../components/Common';
import { StatusBadge } from '../components/StatusBadge';

interface Policy {
  id: string;
  name: string;
  description: string;
  rules: string[];
  enabled: boolean;
}

interface Model {
  id: string;
  name: string;
  status: string;
  current_risk_score: number;
}

interface EvaluationResult {
  model_id: string;
  status: 'approved' | 'pending' | 'rejected';
  violations: string[];
  recommendations: string[];
}

export function GovernancePage() {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedModelId, setSelectedModelId] = useState('');
  const [evaluationResult, setEvaluationResult] = useState<EvaluationResult | null>(null);
  const [evaluating, setEvaluating] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const results = await Promise.allSettled([
        governanceAPI.getPolicies(),
        modelAPI.getModels(),
      ]);
      
      const policiesRes = results[0].status === 'fulfilled' ? results[0].value : null;
      const modelsRes = results[1].status === 'fulfilled' ? results[1].value : null;
      
      setPolicies(policiesRes?.data || []);
      const modelsList = modelsRes?.data?.items || modelsRes?.data?.models || modelsRes?.data || [];
      setModels(Array.isArray(modelsList) ? modelsList : []);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to load governance data');
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluateGovernance = async () => {
    if (!selectedModelId) {
      setError('Please select a model');
      return;
    }

    try {
      setEvaluating(true);
      const response = await governanceAPI.evaluateGovernance(selectedModelId);
      setEvaluationResult(response.data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Evaluation failed');
    } finally {
      setEvaluating(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="page">
      <div className="page-header">
        <h1>⚖️ Governance Management</h1>
        <p>Evaluate models against governance policies</p>
      </div>

      {error && <ErrorMessage message={error} />}

      <div className="governance-section">
        <h2>📋 Active Policies</h2>
        {policies.length > 0 ? (
          <div className="policies-list">
            {policies.map((policy) => (
              <div key={policy.id} className="policy-card">
                <div className="policy-header">
                  <h3>{policy.name}</h3>
                  <StatusBadge status={policy.enabled ? 'active' : 'inactive'}>
                    {policy.enabled ? 'Enabled' : 'Disabled'}
                  </StatusBadge>
                </div>
                <p>{policy.description}</p>
                <div className="policy-rules">
                  <strong>Rules:</strong>
                  <ul>
                    {policy.rules.map((rule, idx) => (
                      <li key={idx}>{rule}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p>No policies configured</p>
        )}
      </div>

      <div className="governance-section">
        <h2>🔍 Evaluate Model</h2>
        <div className="evaluation-form">
          <div className="form-group">
            <label htmlFor="model-select">Select Model</label>
            <select
              id="model-select"
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
            >
              <option value="">-- Choose a model --</option>
              {models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name || 'Unknown'} (v{model.status || 'N/A'})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleEvaluateGovernance}
            disabled={!selectedModelId || evaluating}
            className="btn btn-primary"
          >
            {evaluating ? 'Evaluating...' : 'Evaluate Governance'}
          </button>
        </div>

        {evaluationResult && (
          <div className="evaluation-result">
            <h3>Evaluation Result</h3>
            <div className="result-status">
              <span className="label">Status:</span>
              <StatusBadge status={evaluationResult.status}>
                {evaluationResult.status}
              </StatusBadge>
            </div>

            {evaluationResult.violations && evaluationResult.violations.length > 0 && (
              <div className="violations">
                <h4>Violations</h4>
                <ul>
                  {evaluationResult.violations.map((violation, idx) => (
                    <li key={idx}>❌ {violation || 'Unknown violation'}</li>
                  ))}
                </ul>
              </div>
            )}

            {evaluationResult.recommendations && evaluationResult.recommendations.length > 0 && (
              <div className="recommendations">
                <h4>Recommendations</h4>
                <ul>
                  {evaluationResult.recommendations.map((rec, idx) => (
                    <li key={idx}>💡 {rec || 'No details available'}</li>
                  ))}
                </ul>
              </div>
            )}

            {evaluationResult.status === 'approved' && (
              <div className="success-message">
                ✓ Model is ready for deployment
              </div>
            )}
            {evaluationResult.status === 'rejected' && (
              <div className="error-message">
                ✗ Model does not meet governance requirements
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}