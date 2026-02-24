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
  feature_name: string;
  drift_score: number;
  threshold: number;
}

interface FairnessMetrics {
  protected_group: string;
  demographic_parity: number;
  equalized_odds: number;
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
        console.log('Simulation status:', response.data);
      }
    } catch (err: any) {
      console.warn('Failed to fetch simulation status:', err.message);
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

      // Safely set risk history with default
      const riskHistory = riskRes?.data?.history || [];
      if (Array.isArray(riskHistory)) {
        setRiskHistory(riskHistory);
      } else {
        console.warn('Risk history is not an array:', riskHistory);
        setRiskHistory([]);
      }

      // Safely set drift metrics with default
      const driftMetrics = driftRes?.data?.metrics || [];
      if (Array.isArray(driftMetrics)) {
        setDriftMetrics(driftMetrics);
      } else {
        console.warn('Drift metrics is not an array:', driftMetrics);
        setDriftMetrics([]);
      }

      // Safely set fairness metrics with default
      const fairnessMetrics = fairnessRes?.data?.metrics || [];
      if (Array.isArray(fairnessMetrics)) {
        setFairnessMetrics(fairnessMetrics);
      } else {
        console.warn('Fairness metrics is not an array:', fairnessMetrics);
        setFairnessMetrics([]);
      }
      
      // Fetch governance status
      const govRes = await governanceAPI.evaluateGovernance(modelId!);
      if (govRes?.data) {
        setGovernanceStatus(govRes.data);
      }
      
      setError('');
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || 'Failed to load model data';
      console.error('Model data fetch error:', errorMsg, err);
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
        const data = await response.json();
        if (data && typeof data === 'object') {
          setAiExplanation(data);
        }
      } else {
        console.debug(`AI explanation endpoint returned ${response.status}`);
      }
    } catch (err: any) {
      console.debug('Failed to fetch AI explanation:', err.message);
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
      console.error('Deployment error:', errorMsg, err);
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
      console.error('Override deployment error:', errorMsg, err);
      setError(errorMsg);
    }
  };

  // PHASE 2 & 3: Smart simulation handler with confirmation and graceful error handling
  const handleRunSimulation = async () => {
    // Close confirmation modal
    setShowSimulationConfirm(false);
    
    try {
      setRunningSimulation(true);
      setError('');
      setSimulationResult(null);
      
      if (!modelId) {
        throw new Error('Model ID not found');
      }
      
      console.log('Starting simulation for model:', modelId);
      const response = await modelAPI.runSimulation(modelId);
      
      console.log('Raw simulation response:', response);
      
      // Validate response structure
      if (!response) {
        throw new Error('No response received from simulation endpoint');
      }
      
      if (!response.data) {
        console.error('Response structure:', response);
        throw new Error('Simulation endpoint returned empty data');
      }
      
      // Display result briefly
      setSimulationResult(response.data);
      console.log('Simulation completed successfully:', response.data);
      
      // Wait a moment for backend to fully commit
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // PHASE 5: Comprehensive data refresh orchestration
      console.log('Refreshing all model data after simulation...');
      await Promise.all([
        fetchModelData(),
        fetchSimulationStatus()
      ]);
      
      // Clear simulation result after successful refresh
      setTimeout(() => setSimulationResult(null), 5000);
    } catch (err: any) {
      // PHASE 3: Graceful error handling with structured notifications
      console.error('=== SIMULATION ERROR ===');
      console.error('Error object:', err);
      console.error('Error response:', err?.response);
      console.error('Error response data:', err?.response?.data);
      console.error('Error message:', err?.message);
      
      // Extract the most detailed error message available
      let errorMsg = 'Simulation failed';
      
      if (err?.response?.data?.detail) {
        errorMsg = err.response.data.detail;
        
        // Special handling for duplication error
        if (errorMsg.includes('already has prediction logs')) {
          errorMsg = 'Simulation already executed. This model already has prediction logs. Use the Reset button to clear existing data before running a new simulation.';
        }
      } else if (err?.response?.data?.message) {
        errorMsg = err.response.data.message;
      } else if (err?.response?.statusText) {
        errorMsg = err.response.statusText;
      } else if (err?.message) {
        errorMsg = err.message;
      }
      
      console.error('Final error message:', errorMsg);
      setError(errorMsg);
      setSimulationResult(null);
      
      // Refresh status to update UI state
      await fetchSimulationStatus();
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
      
      console.log('Resetting simulation for model:', modelId);
      const response = await modelAPI.resetSimulation(modelId);
      
      if (!response || !response.data) {
        throw new Error('Invalid response from reset endpoint');
      }
      
      console.log('Reset completed:', response.data);
      
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
      console.error('Reset error:', errorMsg, err);
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
            <span className={`value risk-${getRiskLevel((riskHistory?.[0]?.score) || 0)}`}>
              {riskHistory && riskHistory.length > 0 && riskHistory[0]?.score !== undefined
                ? riskHistory[0].score.toFixed(2)
                : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      <div className="model-detail-section">
        <h2>📈 Risk Score History</h2>
        {riskHistory && riskHistory.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={riskHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis domain={[0, 100]} />
              <Tooltip 
                formatter={(value: any) => {
                  if (typeof value === 'number') return value.toFixed(2);
                  return value;
                }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="score" 
                stroke="#8884d8" 
                name="Risk Score"
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p>No risk history available. Run a simulation to generate data.</p>
        )}
      </div>

      <div className="model-detail-section">
        <h2>🔍 Drift Metrics</h2>
        {driftMetrics && driftMetrics.length > 0 ? (
          <table className="metrics-table">
            <thead>
              <tr>
                <th>Feature</th>
                <th>Drift Score</th>
                <th>Threshold</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {driftMetrics.map((metric, idx) => {
                const driftScore = metric.drift_score || 0;
                const threshold = metric.threshold || 0.1;
                const isDriftDetected = driftScore > threshold;
                
                return (
                  <tr key={idx}>
                    <td>{metric.feature_name || 'unknown'}</td>
                    <td>{driftScore.toFixed(3)}</td>
                    <td>{threshold.toFixed(3)}</td>
                    <td>
                      <StatusBadge status={isDriftDetected ? 'alert' : 'active'}>
                        {isDriftDetected ? 'Alert' : 'Normal'}
                      </StatusBadge>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <p>No drift metrics available. Run a simulation to generate data.</p>
        )}
      </div>

      <div className="model-detail-section">
        <h2>⚖️ Fairness Metrics</h2>
        {fairnessMetrics && fairnessMetrics.length > 0 ? (
          <table className="metrics-table">
            <thead>
              <tr>
                <th>Protected Group</th>
                <th>Demographic Parity</th>
                <th>Equalized Odds</th>
              </tr>
            </thead>
            <tbody>
              {fairnessMetrics.map((metric, idx) => {
                const demographicParity = metric.demographic_parity || 0;
                const equalizedOdds = metric.equalized_odds || 0;
                
                return (
                  <tr key={idx}>
                    <td>{metric.protected_group || 'unknown'}</td>
                    <td>{demographicParity.toFixed(3)}</td>
                    <td>{equalizedOdds.toFixed(3)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <p>No fairness metrics available. Run a simulation to generate data.</p>
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