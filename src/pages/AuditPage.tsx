import { useState, useEffect } from 'react';
import { auditAPI } from '../services/api';
import { LoadingSpinner, ErrorMessage } from '../components/Common';
import { StatusBadge } from '../components/StatusBadge';

interface DeploymentRecord {
  id: string;
  model_id: string;
  model_name: string;
  timestamp: string;
  status: 'success' | 'failed' | 'in_progress';
  version: string;
  deployed_by: string;
}

interface AuditRecord {
  id: string;
  timestamp: string;
  action: string;
  actor: string;
  model_id: string;
  details: string;
}

export function AuditPage() {
  const [deploymentHistory, setDeploymentHistory] = useState<DeploymentRecord[]>([]);
  const [auditTrail, setAuditTrail] = useState<AuditRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'deployments' | 'audit'>('deployments');

  useEffect(() => {
    fetchAuditData();
  }, []);

  const fetchAuditData = async () => {
    try {
      setLoading(true);
      const results = await Promise.allSettled([
        auditAPI.getDeploymentHistory(),
        auditAPI.getAuditTrail(),
      ]);
      
      const deploymentsRes = results[0].status === 'fulfilled' ? results[0].value : null;
      const auditRes = results[1].status === 'fulfilled' ? results[1].value : null;
      
      setDeploymentHistory(deploymentsRes?.data?.deployments || []);
      setAuditTrail(auditRes?.data?.trail || []);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to load audit data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="page">
      <div className="page-header">
        <h1>📋 Audit & History</h1>
        <p>Track deployments and governance actions</p>
      </div>

      {error && <ErrorMessage message={error} onRetry={fetchAuditData} />}

      <div className="tabs">
        <button
          className={`tab-button ${activeTab === 'deployments' ? 'active' : ''}`}
          onClick={() => setActiveTab('deployments')}
        >
          📦 Deployment History
        </button>
        <button
          className={`tab-button ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          📝 Audit Trail
        </button>
      </div>

      {activeTab === 'deployments' && (
        <div className="audit-section">
          {deploymentHistory.length > 0 ? (
            <table className="audit-table">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Version</th>
                  <th>Status</th>
                  <th>Deployed By</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {deploymentHistory.map((record) => (
                  <tr key={record.id}>
                    <td>
                      <strong>{record.model_name}</strong>
                      <br />
                      <span className="text-muted">{record.model_id}</span>
                    </td>
                    <td>{record.version}</td>
                    <td>
                      <StatusBadge status={record.status}>
                        {record.status}
                      </StatusBadge>
                    </td>
                    <td>{record.deployed_by}</td>
                    <td>{new Date(record.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state">
              <p>No deployment records found</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="audit-section">
          {auditTrail.length > 0 ? (
            <div className="audit-list">
              {auditTrail.map((record) => (
                <div key={record.id} className="audit-record">
                  <div className="audit-record-header">
                    <span className="action-badge">{record.action}</span>
                    <span className="actor">{record.actor}</span>
                    <span className="timestamp">
                      {new Date(record.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div className="audit-record-body">
                    <p className="model-info">Model: {record.model_id}</p>
                    <p className="details">{record.details}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <p>No audit records found</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}