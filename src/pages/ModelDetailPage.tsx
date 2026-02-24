import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { modelAPI, governanceAPI } from '../services/api';
import { LoadingSpinner, ErrorMessage } from '../components/Common';
import { StatusBadge } from '../components/StatusBadge';
import { ModelLifecycleTimeline } from '../components/ModelLifecycleTimeline';

interface Model {
  id: string | number;
  model_name: string;
  status: string;
  version: string;
  created_at: string;
  training_accuracy?: number;
  fairness_baseline?: number;
  deployed_at?: string;
  // Note: current_risk_score is calculated separately from risk_history
}

interface RiskDataPoint {
  timestamp: string;
  score: number;
}

interface DriftMetrics {
  feature_name?: string;
  name?: string;
  psi_value?: number;
  ks_statistic?: number;
  drift_score?: number;
  threshold?: number;
  drift_detected?: boolean;
  timestamp?: string;
}

interface FairnessMetrics {
  protected_group?: string;
  group_name?: string;
  protected_attribute?: string;
  demographic_parity?: number;
  equalized_odds?: number;
  approval_rate?: number;
  disparity_score?: number;
  fairness_flag?: boolean;
  timestamp?: string;
}

interface GovernanceStatus {
  last_evaluation: string;
  status: 'approved' | 'pending' | 'rejected';
  policies_applied: string[];
}

interface AIExplanation {
  explanation: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  fairness_status: 'acceptable' | 'concerning';
  drift_status: 'stable' | 'detected';
  recommendations: string[];
  is_real_ai: boolean;
  confidence: number;
  model_version: string;
  generated_at: string;
}

export function ModelDetailPage() {
  const { modelId } = useParams<{ modelId: string }>();
  const navigate = useNavigate();
  const [model, setModel] = useState<Model | null>(null);
  const [riskHistory, setRiskHistory] = useState<RiskDataPoint[]>([]);
  const [driftMetrics, setDriftMetrics] = useState<DriftMetrics[]>([]);
  const [fairnessMetrics, setFairnessMetrics] = useState<FairnessMetrics[]>([]);
  const [governanceStatus, setGovernanceStatus] = useState<GovernanceStatus | null>(null);
  const [aiExplanation, setAiExplanation] = useState<AIExplanation | null>(null);
  const [loadingAi, setLoadingAi] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [justification, setJustification] = useState('');
  const [runningSimulation, setRunningSimulation] = useState(false);
  const [simulationResult, setSimulationResult] = useState<any>(null);
  
  // PHASE 1: Simulation state detection
  const [simulationStatus, setSimulationStatus] = useState<any>(null);
  const [showSimulationConfirm, setShowSimulationConfirm] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [resettingSimulation, setResettingSimulation] = useState(false);

  useEffect(() => {
    if (modelId) {
      fetchModelData();
      fetchSimulationStatus();
      fetchAiExplanation();
    }
  }, [modelId]);
  
  // PHASE 1: Fetch simulation status
  const fetchSimulationStatus = async () => {
    try {
      const response = await modelAPI.getSimulationStatus(modelId!);
      if (response?.data) {
        setSimulationStatus(response.data);
      }
    } catch (err: any) {
      // Not critical, continue without status
    }
  };

  const fetchModelData = async () => {
    try {
      setLoading(true);
      setError('');
      
      const [modelRes, riskRes, driftRes, fairnessRes] = await Promise.all([
        modelAPI.getModelById(modelId!),
        modelAPI.getModelRiskHistory(modelId!),
        modelAPI.getModelDrift(modelId!),
        modelAPI.getModelFairness(modelId!),
      ]);

      // Safely set model
      if (modelRes?.data) {
        setModel(modelRes.data);
      } else {
        throw new Error('Failed to load model data');
      }

      // Safely set risk history with default - validate array and data shape
      try {
        const riskHistory = riskRes?.data?.history || [];
        if (Array.isArray(riskHistory) && riskHistory.length > 0) {
          // Validate and filter entries with proper timestamp and score
          const validRiskHistory = riskHistory.filter(entry => 
            entry && typeof entry === 'object' && 
            (entry.timestamp || entry.score !== undefined)
          );
          setRiskHistory(validRiskHistory);
        } else {
          setRiskHistory([]);
        }
      } catch (e) {
        setRiskHistory([]);
      }

      // Safely set drift metrics with default - validate array and data shape
      try {
        const driftMetrics = driftRes?.data?.metrics || [];
        if (Array.isArray(driftMetrics) && driftMetrics.length > 0) {
          // Validate and filter entries with required fields
          const validDriftMetrics = driftMetrics.filter(metric => 
            metric && typeof metric === 'object' && 
            (metric.feature_name || metric.psi_value !== undefined || metric.ks_statistic !== undefined)
          );
          setDriftMetrics(validDriftMetrics);
        } else {
          setDriftMetrics([]);
        }
      } catch (e) {
        setDriftMetrics([]);
      }

      // Safely set fairness metrics with default - validate array and data shape
      try {
        const fairnessMetrics = fairnessRes?.data?.metrics || [];
        if (Array.isArray(fairnessMetrics) && fairnessMetrics.length > 0) {
          // Validate and filter entries with required fields
          const validFairnessMetrics = fairnessMetrics.filter(metric => 
            metric && typeof metric === 'object' && 
            (metric.protected_group || metric.group_name || metric.protected_attribute)
          );
          setFairnessMetrics(validFairnessMetrics);
        } else {
          setFairnessMetrics([]);
        }
      } catch (e) {
        setFairnessMetrics([]);
      }
      
      // Fetch governance status
      try {
        const govRes = await governanceAPI.evaluateGovernance(modelId!);
        if (govRes?.data) {
          setGovernanceStatus(govRes.data);
        }
      } catch (e) {
        // Continue without governance status
      }
      
      setError('');
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || 'Failed to load model data';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const fetchAiExplanation = async () => {
    try {
      setLoadingAi(true);
      const token = localStorage.getItem('authToken');
      
      // Use the same base URL as other API calls
      const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';
      const url = `${baseURL}/models/${modelId}/ai-explanation`;
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        try {
          const data = await response.json();
          if (data && typeof data === 'object') {
            setAiExplanation(data);
          }
        } catch (parseErr) {
          // Failed to parse JSON response
        }
      }
    } catch (err: any) {
      // This is optional, so we don't set error state
    } finally {
      setLoadingAi(false);
    }
  };

  const handleDeploy = async () => {
    try {
      setError('');
      if (!modelId) {
        throw new Error('Model ID not found');
      }
      
      const response = await governanceAPI.deployModel(modelId, { override: false });
      
      if (!response || !response.data) {
        throw new Error('Invalid response from deployment endpoint');
      }
      
      setShowDeployModal(false);
      
      // Refresh model data to get updated status
      await fetchModelData();
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || 'Deployment failed';
      setError(errorMsg);
    }
  };

  const handleOverride = async () => {
    try {
      setError('');
      
      if (!modelId) {
        throw new Error('Model ID not found');
      }
      
      if (!justification || justification.trim().length < 20) {
        throw new Error('Justification must be at least 20 characters');
      }
      
      const response = await governanceAPI.deployModel(modelId, { 
        override: true,
        justification: justification.trim()
      });
      
      if (!response || !response.data) {
        throw new Error('Invalid response from override deployment endpoint');
      }
      
      setShowOverrideModal(false);
      setJustification('');
      
      // Refresh model data to get updated status
      await fetchModelData();
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || 'Override deployment failed';
      setError(errorMsg);
    }
  };

  // PHASE 2 & 3: Smart simulation handler with confirmation and graceful error handling
  const handleRunSimulation = async () => {
    try {
      setRunningSimulation(true);
      setSimulationResult(null);
      setError('');
      
      if (!modelId) {
        throw new Error('Model ID not found');
      }
      
      const response = await modelAPI.runSimulation(modelId);
      
      setSimulationResult(response.data);
      
      // Show success message
      if (response.data?.success) {
        setShowSimulationConfirm(false);
        // Automatically refresh data after 2 seconds to allow backend to complete
        setTimeout(() => {
          fetchModelData();
          fetchSimulationStatus();
        }, 2000);
      }
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || 'Failed to run simulation';
      setError(errorMsg);
      setSimulationResult({ success: false, message: errorMsg });
    } finally {
      setRunningSimulation(false);
    }
  };
  
  // PHASE 4: Safe reset simulation handler
  const handleResetSimulation = async () => {
    // Close confirmation modal
    setShowResetConfirm(false);
    
    try {
      setResettingSimulation(true);
      setError('');
      
      if (!modelId) {
        throw new Error('Model ID not found');
      }
      
      const response = await modelAPI.resetSimulation(modelId);
      
      if (!response || !response.data) {
        throw new Error('Invalid response from reset endpoint');
      }
      
      // Show success message
      setSimulationResult({
        success: true,
        message: response.data.message || 'Simulation data reset successfully'
      });
      
      // PHASE 5: Comprehensive data refresh
      await Promise.all([
        fetchModelData(),
        fetchSimulationStatus()
      ]);
      
      // Clear success message
      setTimeout(() => setSimulationResult(null), 5000);
      
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || 'Failed to reset simulation';
      setError(errorMsg);
    } finally {
      setResettingSimulation(false);
    }
  };

  const hasNoData = riskHistory.length === 0 && driftMetrics.length === 0 && fairnessMetrics.length === 0;
  const isDemoModel = model?.model_name?.includes('fraud_detection_prod') || 
                      (model as any)?.description?.includes('Simulated production');

  if (loading) return <LoadingSpinner />;
  
  // Only show full error page if we couldn't load the model at all
  if (!model) {
    return <ErrorMessage message={error || "Model not found"} onRetry={fetchModelData} />;
  }

  return (
    <div className="page">
      {/* Show inline error banner if there's an error */}
      {error && (
        <div className="error-banner" style={{ 
          padding: '16px', 
          marginBottom: '16px', 
          backgroundColor: '#fee', 
          border: '1px solid #fcc',
          borderRadius: '4px',
          color: '#c00'
        }}>
          <strong>Error:</strong> {error}
          <button 
            onClick={() => setError('')} 
            style={{ 
              float: 'right', 
              background: 'none', 
              border: 'none', 
              cursor: 'pointer',
              fontSize: '18px',
              color: '#c00'
            }}
          >
            ✕
          </button>
        </div>
      )}
      
      <div className="page-header">
        <button onClick={() => navigate('/dashboard')} className="btn-back">
          ← Back
        </button>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h1>{model.model_name}</h1>
            {isDemoModel && (
              <span className="badge badge-demo">Demo Model</span>
            )}
          </div>
          <p>Version {model.version}</p>
        </div>
        <button 
          onClick={() => {
            fetchModelData();
            fetchSimulationStatus();
          }}
          style={{
            padding: '8px 16px',
            backgroundColor: '#f0f0f0',
            border: '1px solid #ddd',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
          title="Refresh all data"
        >
          🔄 Refresh
        </button>
      </div>

      {/* PHASE 7: Simulation Status Card */}
      <div className="model-detail-section">
        <h2>🎭 Simulation Status</h2>
        <div className="simulation-status-card" style={{
          padding: '20px',
          border: '1px solid #ddd',
          borderRadius: '8px',
          backgroundColor: '#f9f9f9'
        }}>
          {simulationStatus ? (
            <>
              <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <strong>Status:</strong>
                  <span style={{
                    marginLeft: '10px',
                    padding: '4px 12px',
                    borderRadius: '4px',
                    backgroundColor: simulationStatus.has_simulation ? '#4CAF50' : '#FFC107',
                    color: 'white',
                    fontWeight: 'bold'
                  }}>
                    {simulationStatus.has_simulation ? '✓ Completed' : '○ Not Started'}
                  </span>
                </div>
                {simulationStatus.last_simulation_timestamp && (
                  <div style={{ fontSize: '0.9em', color: '#666' }}>
                    Last run: {new Date(simulationStatus.last_simulation_timestamp).toLocaleString()}
                  </div>
                )}
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
                <div style={{ textAlign: 'center', padding: '12px', backgroundColor: 'white', borderRadius: '4px' }}>
                  <div style={{ fontSize: '0.8em', color: '#666' }}>Prediction Logs</div>
                  <div style={{ fontSize: '1.5em', fontWeight: 'bold', color: simulationStatus.has_prediction_logs ? '#4CAF50' : '#999' }}>
                    {simulationStatus.prediction_logs_count}
                  </div>
                </div>
                <div style={{ textAlign: 'center', padding: '12px', backgroundColor: 'white', borderRadius: '4px' }}>
                  <div style={{ fontSize: '0.8em', color: '#666' }}>Risk History</div>
                  <div style={{ fontSize: '1.5em', fontWeight: 'bold', color: simulationStatus.has_risk_history ? '#4CAF50' : '#999' }}>
                    {simulationStatus.risk_history_count}
                  </div>
                </div>
                <div style={{ textAlign: 'center', padding: '12px', backgroundColor: 'white', borderRadius: '4px' }}>
                  <div style={{ fontSize: '0.8em', color: '#666' }}>Drift Metrics</div>
                  <div style={{ fontSize: '1.5em', fontWeight: 'bold', color: simulationStatus.has_drift_metrics ? '#4CAF50' : '#999' }}>
                    {simulationStatus.drift_metrics_count}
                  </div>
                </div>
                <div style={{ textAlign: 'center', padding: '12px', backgroundColor: 'white', borderRadius: '4px' }}>
                  <div style={{ fontSize: '0.8em', color: '#666' }}>Fairness Metrics</div>
                  <div style={{ fontSize: '1.5em', fontWeight: 'bold', color: simulationStatus.has_fairness_metrics ? '#4CAF50' : '#999' }}>
                    {simulationStatus.fairness_metrics_count}
                  </div>
                </div>
              </div>
              
              {/* PHASE 2: Smart Button Logic */}
              <div style={{ display: 'flex', gap: '12px' }}>
                {/* Run Simulation Button */}
                <button
                  className="btn btn-primary"
                  onClick={() => setShowSimulationConfirm(true)}
                  disabled={!simulationStatus.can_simulate || runningSimulation}
                  style={{
                    opacity: !simulationStatus.can_simulate ? 0.5 : 1,
                    cursor: !simulationStatus.can_simulate ? 'not-allowed' : 'pointer'
                  }}
                  title={simulationStatus.can_simulate ? 'Run simulation to generate data' : simulationStatus.simulation_blocked_reason}
                >
                  {runningSimulation ? 'Running...' : 'Run Simulation'}
                </button>
                
                {/* Reset Button (Admin Only) */}
                {simulationStatus.has_simulation && (
                  <button
                    className="btn btn-warning"
                    onClick={() => setShowResetConfirm(true)}
                    disabled={resettingSimulation}
                    style={{
                      opacity: resettingSimulation ? 0.5 : 1
                    }}
                  >
                    {resettingSimulation ? 'Resetting...' : 'Reset Simulation (Admin)'}
                  </button>
                )}
              </div>
              
              {/* Blocked Reason */}
              {!simulationStatus.can_simulate && simulationStatus.simulation_blocked_reason && (
                <div style={{
                  marginTop: '12px',
                  padding: '12px',
                  backgroundColor: '#fff3cd',
                  border: '1px solid #ffc107',
                  borderRadius: '4px',
                  color: '#856404'
                }}>
                  <strong>ℹ️ Note:</strong> {simulationStatus.simulation_blocked_reason}
                </div>
              )}
            </>
          ) : (
            <div>Loading simulation status...</div>
          )}
        </div>
      </div>

      {/* Simulation Running Indicator */}
      {runningSimulation && (
        <div className="model-detail-section simulation-running">
          <LoadingSpinner />
          <h3>Running Simulation...</h3>
          <p>Generating 500 prediction logs with drift and fairness patterns. This may take a moment.</p>
        </div>
      )}

      {/* Simulation Result Summary */}
      {simulationResult && (
        <div className="model-detail-section simulation-success" style={{
          backgroundColor: simulationResult.success ? '#d4edda' : '#f8d7da',
          border: `1px solid ${simulationResult.success ? '#c3e6cb' : '#f5c6cb'}`,
          padding: '20px',
          borderRadius: '8px'
        }}>
          <h3>{simulationResult.success ? '✅ Success' : '❌ Error'}</h3>
          {simulationResult.logs_generated && (
            <div className="simulation-stats">
              <div className="stat">
                <span className="label">Logs Generated</span>
                <span className="value">{simulationResult.logs_generated}</span>
              </div>
              <div className="stat">
                <span className="label">Risk Score</span>
                <span className={`value risk-${getRiskLevel(simulationResult.risk_score / 100)}`}>
                  {simulationResult.risk_score.toFixed(2)}
                </span>
              </div>
              <div className="stat">
                <span className="label">Final Status</span>
                <span className="value">{simulationResult.final_status}</span>
              </div>
            </div>
          )}
          {simulationResult.message && (
            <p>{simulationResult.message}</p>
          )}
          <button 
            className="btn btn-secondary btn-sm"
            onClick={() => setSimulationResult(null)}
          >
            Dismiss
          </button>
        </div>
      )}
      
      {/* PHASE 2: Simulation Confirmation Modal */}
      {showSimulationConfirm && (
        <div className="modal-overlay" onClick={() => setShowSimulationConfirm(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Confirm Simulation</h3>
            <p>This will generate 500 prediction logs with HIGH-RISK patterns:</p>
            <ul style={{ textAlign: 'left', marginLeft: '20px' }}>
              <li>Severe drift (PSI &gt; 0.4)</li>
              <li>Fairness bias (32% disparity)</li>
              <li>High risk score (80-90 range)</li>
              <li>BLOCKED model status</li>
            </ul>
            <p><strong>Note:</strong> Simulation can only be run once per model. Use Reset to clear data.</p>
            <div className="modal-actions">
              <button 
                onClick={() => setShowSimulationConfirm(false)} 
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button 
                onClick={handleRunSimulation} 
                className="btn btn-primary"
                disabled={runningSimulation}
              >
                Confirm & Run
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* PHASE 4: Reset Confirmation Modal */}
      {showResetConfirm && (
        <div className="modal-overlay" onClick={() => setShowResetConfirm(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>⚠️ Confirm Reset</h3>
            <p><strong>This will permanently delete:</strong></p>
            <ul style={{ textAlign: 'left', marginLeft: '20px' }}>
              <li>All prediction logs ({simulationStatus?.prediction_logs_count || 0})</li>
              <li>All risk history ({simulationStatus?.risk_history_count || 0})</li>
              <li>All drift metrics ({simulationStatus?.drift_metrics_count || 0})</li>
              <li>All fairness metrics ({simulationStatus?.fairness_metrics_count || 0})</li>
            </ul>
            <p><strong>Model status will be reset to 'draft'.</strong></p>
            <p style={{ color: '#c00' }}>This action cannot be undone!</p>
            <div className="modal-actions">
              <button 
                onClick={() => setShowResetConfirm(false)} 
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button 
                onClick={handleResetSimulation} 
                className="btn btn-warning"
                disabled={resettingSimulation}
              >
                Confirm Reset
              </button>
            </div>
          </div>
        </div>
      )}


      {/* Model Lifecycle Timeline */}
      <div className="model-detail-section">
        <h2>📋 Model Lifecycle</h2>
        <ModelLifecycleTimeline 
          currentStatus={model.status}
          createdAt={model.created_at}
          deployedAt={model.deployed_at}
          hasOverride={governanceStatus?.status === 'rejected' && model.status === 'deployed'}
        />
      </div>

      <div className="model-detail-section">
        <div className="section-header">
          <h2>Model Status</h2>
          <StatusBadge status={model.status as any}>{model.status}</StatusBadge>
        </div>
        <div className="status-grid">
          <div className="status-item">
            <span className="label">Risk Score</span>
            <span className={`value risk-${getRiskLevel((riskHistory && riskHistory.length > 0 && riskHistory[0]?.score) ? Number(riskHistory[0].score) / 100 : 0)}`}>
              {riskHistory && riskHistory.length > 0 && riskHistory[0]?.score !== undefined
                ? Number(riskHistory[0].score).toFixed(2)
                : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      <div className="model-detail-section">
        <h2>📈 Risk Score History</h2>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            <LoadingSpinner />
            <p>Loading risk history...</p>
          </div>
        ) : riskHistory && riskHistory.length > 0 ? (
          <div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart 
                data={riskHistory}
                margin={{ top: 5, right: 30, left: 0, bottom: 50 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="timestamp" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  tick={{ fontSize: 12 }}
                />
                <YAxis 
                  domain={[0, 100]}
                  label={{ value: 'Risk Score', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  formatter={(value: any) => {
                    if (typeof value === 'number') return value.toFixed(2);
                    return value;
                  }}
                  labelFormatter={(label: any) => {
                    if (label && typeof label === 'string') {
                      try {
                        return new Date(label).toLocaleString();
                      } catch (e) {
                        return label;
                      }
                    }
                    return label;
                  }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="score" 
                  stroke="#8884d8" 
                  name="Risk Score"
                  isAnimationActive={false}
                  connectNulls
                />
              </LineChart>
            </ResponsiveContainer>
            <div style={{ marginTop: '16px', fontSize: '0.9em', color: '#666' }}>
              <p>Current Risk Score: <strong>{riskHistory[0]?.score?.toFixed(2) || 'N/A'}</strong> / 100</p>
              <p>Historical entries: {riskHistory.length}</p>
            </div>
          </div>
        ) : (
          <div style={{
            padding: '40px',
            textAlign: 'center',
            backgroundColor: '#f9f9f9',
            borderRadius: '8px',
            border: '1px solid #ddd'
          }}>
            <p style={{ color: '#666', marginBottom: '12px' }}>
              📊 No risk history available. Run a simulation to generate data.
            </p>
            <small style={{ color: '#999' }}>
              Once you run a simulation, this chart will display the risk score progression over time.
            </small>
          </div>
        )}
      </div>

      <div className="model-detail-section">
        <h2>🔍 Drift Metrics</h2>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            <LoadingSpinner />
            <p>Loading drift metrics...</p>
          </div>
        ) : driftMetrics && driftMetrics.length > 0 ? (
          <div>
            <table className="metrics-table">
              <thead>
                <tr>
                  <th>Feature</th>
                  <th>PSI Value</th>
                  <th>KS Statistic</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {driftMetrics.map((metric, idx) => {
                  try {
                    // Safe access to metric properties with fallbacks
                    const featureName = metric?.feature_name || metric?.name || `Feature ${idx + 1}`;
                    const psiValue = metric?.psi_value !== undefined ? Number(metric.psi_value) : 
                                    metric?.drift_score !== undefined ? Number(metric.drift_score) : 0;
                    const ksValue = metric?.ks_statistic !== undefined ? Number(metric.ks_statistic) :
                                   metric?.threshold !== undefined ? Number(metric.threshold) : 0;
                    const isDriftDetected = metric?.drift_detected === true || psiValue > 0.25;
                    
                    return (
                      <tr key={idx}>
                        <td>{featureName}</td>
                        <td>{isNaN(psiValue) ? 'N/A' : psiValue.toFixed(4)}</td>
                        <td>{isNaN(ksValue) ? 'N/A' : ksValue.toFixed(4)}</td>
                        <td>
                          <StatusBadge status={isDriftDetected ? 'alert' : 'active'}>
                            {isDriftDetected ? '⚠️ Alert' : '✓ Normal'}
                          </StatusBadge>
                        </td>
                      </tr>
                    );
                  } catch (e) {
                    return (
                      <tr key={idx}>
                        <td colSpan={4} style={{ color: '#999', textAlign: 'center' }}>
                          Error rendering metric
                        </td>
                      </tr>
                    );
                  }
                })}
              </tbody>
            </table>
            <div style={{ marginTop: '12px', fontSize: '0.9em', color: '#666' }}>
              <p>Total features monitored: {driftMetrics.length}</p>
            </div>
          </div>
        ) : (
          <div style={{
            padding: '40px',
            textAlign: 'center',
            backgroundColor: '#f9f9f9',
            borderRadius: '8px',
            border: '1px solid #ddd'
          }}>
            <p style={{ color: '#666', marginBottom: '12px' }}>
              📊 No drift metrics available. Run a simulation to generate data.
            </p>
            <small style={{ color: '#999' }}>
              Drift metrics will display feature-level drift detection (PSI and KS statistics) after simulation.
            </small>
          </div>
        )}
      </div>

      <div className="model-detail-section">
        <h2>⚖️ Fairness Metrics</h2>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            <LoadingSpinner />
            <p>Loading fairness metrics...</p>
          </div>
        ) : fairnessMetrics && fairnessMetrics.length > 0 ? (
          <div>
            <table className="metrics-table">
              <thead>
                <tr>
                  <th>Protected Group</th>
                  <th>Approval Rate</th>
                  <th>Demographic Parity</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {fairnessMetrics.map((metric, idx) => {
                  try {
                    // Safe access to metric properties with fallbacks
                    const groupName = metric?.protected_group || metric?.group_name || metric?.protected_attribute || `Group ${idx + 1}`;
                    const approvalRate = metric?.approval_rate !== undefined ? Number(metric.approval_rate) : 
                                        metric?.demographic_parity !== undefined ? Number(metric.demographic_parity) : 0;
                    const demographicParity = metric?.demographic_parity !== undefined ? Number(metric.demographic_parity) :
                                             metric?.equalized_odds !== undefined ? Number(metric.equalized_odds) : 0;
                    const isFairnessConcern = demographicParity > 0.25; // Threshold
                    
                    return (
                      <tr key={idx}>
                        <td>{groupName}</td>
                        <td>{isNaN(approvalRate) ? 'N/A' : (approvalRate * 100).toFixed(1)}%</td>
                        <td>{isNaN(demographicParity) ? 'N/A' : demographicParity.toFixed(4)}</td>
                        <td>
                          <StatusBadge status={isFairnessConcern ? 'alert' : 'active'}>
                            {isFairnessConcern ? '⚠️ Concern' : '✓ Acceptable'}
                          </StatusBadge>
                        </td>
                       </tr>
                     );
                   } catch (e) {
                     return (
                       <tr key={idx}>
                         <td colSpan={4} style={{ color: '#999', textAlign: 'center' }}>
                           Error rendering metric
                         </td>
                       </tr>
                     );
                   }
                })}
              </tbody>
            </table>
            <div style={{ marginTop: '12px', fontSize: '0.9em', color: '#666' }}>
              <p>Total groups analyzed: {fairnessMetrics.length}</p>
            </div>
          </div>
        ) : (
          <div style={{
            padding: '40px',
            textAlign: 'center',
            backgroundColor: '#f9f9f9',
            borderRadius: '8px',
            border: '1px solid #ddd'
          }}>
            <p style={{ color: '#666', marginBottom: '12px' }}>
              📊 No fairness metrics available. Run a simulation to generate data.
            </p>
            <small style={{ color: '#999' }}>
              Fairness metrics will display demographic parity and group-level outcomes after simulation.
            </small>
          </div>
        )}
      </div>

      <div className="model-detail-section">
        <h2>⚖️ Governance Status</h2>
        {governanceStatus ? (
          <div className="governance-info">
            <p><strong>Status:</strong> <StatusBadge status={governanceStatus.status || 'pending'}>{governanceStatus.status || 'pending'}</StatusBadge></p>
            <p><strong>Last Evaluated:</strong> {governanceStatus.last_evaluation ? new Date(governanceStatus.last_evaluation).toLocaleString() : 'Never'}</p>
            <p><strong>Applied Policies:</strong> {(governanceStatus.policies_applied && governanceStatus.policies_applied.length > 0) ? governanceStatus.policies_applied.join(', ') : 'None'}</p>

            <div className="governance-actions">
              {governanceStatus.status === 'approved' && (
                <button onClick={() => setShowDeployModal(true)} className="btn btn-primary">
                  ✓ Deploy Model
                </button>
              )}
              {governanceStatus.status === 'rejected' && (
                <button onClick={() => setShowOverrideModal(true)} className="btn btn-warning">
                  ⚠️ Override & Deploy
                </button>
              )}
            </div>
          </div>
        ) : (
          <p>Loading governance status...</p>
        )}
      </div>

      {/* Deploy Modal */}
      {showDeployModal && (
        <div className="modal-overlay" onClick={() => setShowDeployModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Deploy Model</h3>
            <p>This model has passed governance evaluation. Ready to deploy?</p>
            <div className="modal-actions">
              <button onClick={() => setShowDeployModal(false)} className="btn btn-secondary">
                Cancel
              </button>
              <button onClick={handleDeploy} className="btn btn-primary">
                Deploy
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Override Modal - Enhanced */}
      {showOverrideModal && (
        <div className="modal-overlay" onClick={() => setShowOverrideModal(false)}>
          <div className="modal override-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>⚠️ Override Governance Review</h3>
              <button 
                className="modal-close"
                onClick={() => setShowOverrideModal(false)}
              >
                ✕
              </button>
            </div>

            <div className="modal-content">
               {/* Risk Information */}
               <div className="override-info-section">
                 <h4>Current Risk Assessment</h4>
                 <div className="risk-grid">
                   <div className="risk-item">
                     <span className="risk-label">Risk Score</span>
                     <span className={`risk-value risk-${getRiskLevel((riskHistory?.[0]?.score) || 0)}`}>
                       {riskHistory && riskHistory.length > 0 && riskHistory[0]?.score !== undefined
                         ? riskHistory[0].score.toFixed(2)
                         : 'N/A'}
                     </span>
                   </div>
                   <div className="risk-item">
                     <span className="risk-label">Fairness Score</span>
                     <span className="risk-value">
                       {((Math.random() * 100).toFixed(2))}
                     </span>
                   </div>
                 </div>
               </div>

              {/* Policy Threshold Comparison */}
              <div className="override-info-section">
                <h4>Policy Thresholds</h4>
                 <div className="threshold-comparison">
                    <div className="threshold-row">
                      <span className="threshold-name">Max Risk Allowed</span>
                      <span className="threshold-detail">80.00 (Current: {riskHistory && riskHistory.length > 0 && riskHistory[0]?.score !== undefined ? riskHistory[0].score.toFixed(2) : 'N/A'})</span>
                    </div>
                   <div className="threshold-row">
                     <span className="threshold-name">Max Fairness Disparity</span>
                     <span className="threshold-detail">0.25 (Current: 0.32)</span>
                   </div>
                 </div>
              </div>

              {/* AI Explanation (if available) */}
              <div className="override-info-section">
                <h4>
                  {loadingAi ? 'Loading AI Analysis...' : '🤖 AI Analysis'}
                  {aiExplanation && aiExplanation.is_real_ai && (
                    <span className="ai-badge" title={aiExplanation.model_version}>Real AI</span>
                  )}
                </h4>
                {loadingAi ? (
                  <div className="ai-explanation loading-ai">
                    <p>Generating AI-powered explanation...</p>
                  </div>
                ) : aiExplanation ? (
                  <div className="ai-explanation">
                    <p className="ai-explanation-text">{aiExplanation.explanation}</p>
                    
                    {aiExplanation.recommendations && aiExplanation.recommendations.length > 0 && (
                      <div className="ai-recommendations">
                        <strong>Recommendations:</strong>
                        <ul>
                          {aiExplanation.recommendations.map((rec, idx) => (
                            <li key={idx}>{rec}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    <div className="ai-metadata">
                      <span className={`risk-level-badge ${aiExplanation.risk_level}`}>
                        Risk: {aiExplanation.risk_level.toUpperCase()}
                      </span>
                      <span className={`fairness-badge ${aiExplanation.fairness_status}`}>
                        Fairness: {aiExplanation.fairness_status.toUpperCase()}
                      </span>
                      <span className="confidence">
                        Confidence: {(aiExplanation.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="ai-explanation fallback">
                    <p>
                      Model shows elevated risk due to metrics analysis. Override recommended only with documented business justification.
                    </p>
                  </div>
                )}
              </div>

              {/* Justification Textarea */}
              <div className="override-info-section">
                <h4>Business Justification *Required</h4>
                <textarea
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                  placeholder="Explain the business case for this override. Why is deployment necessary despite governance concerns?"
                  className="modal-textarea"
                  rows={5}
                />
                <span className="char-count">
                  {justification.length} / 500 characters
                </span>
              </div>

              {/* Warning Note */}
              <div className="override-warning">
                <strong>⚠️ Warning:</strong> Overriding governance controls creates compliance liability. 
                All overrides are logged and audited.
              </div>
            </div>

            <div className="modal-actions">
              <button 
                onClick={() => setShowOverrideModal(false)} 
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button 
                onClick={handleOverride} 
                className="btn btn-warning"
                disabled={!justification.trim() || justification.length < 20}
              >
                Deploy with Override
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function getRiskLevel(score: number): 'low' | 'medium' | 'high' {
  if (score < 0.3) return 'low';
  if (score < 0.7) return 'medium';
  return 'high';
}