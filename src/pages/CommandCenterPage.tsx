import React, { useEffect, useState } from 'react';
import { dashboardAPI } from '../services/dashboardAPI';
import {
  ExecutiveSummaryCard,
  RiskOverviewChart,
  DeploymentTrendChart,
  ComplianceDistributionWidget,
  GovernanceSimulationPanel
} from '../components/CommandCenter';
import '../styles/command-center.css';

export function CommandCenterPage() {
  const [summary, setSummary] = useState<any>(null);
  const [riskTrends, setRiskTrends] = useState<any>(null);
  const [deploymentTrends, setDeploymentTrends] = useState<any>(null);
  const [complianceDistribution, setComplianceDistribution] = useState<any>(null);
  const [executiveSummary, setExecutiveSummary] = useState<any>(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState(30);

  useEffect(() => {
    loadDashboard();
  }, [timeRange]);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load all dashboard data in parallel with better error isolation
      const results = await Promise.allSettled([
        dashboardAPI.getSummary(),
        dashboardAPI.getRiskTrends(timeRange),
        dashboardAPI.getDeploymentTrends(timeRange),
        dashboardAPI.getComplianceDistribution(),
        dashboardAPI.getExecutiveSummary()
      ]);

      // Process each result with error handling
      const summaryRes = results[0].status === 'fulfilled' ? results[0].value : null;
      const riskTrendsRes = results[1].status === 'fulfilled' ? results[1].value : null;
      const deploymentTrendsRes = results[2].status === 'fulfilled' ? results[2].value : null;
      const complianceRes = results[3].status === 'fulfilled' ? results[3].value : null;
      const executiveRes = results[4].status === 'fulfilled' ? results[4].value : null;

      // Set data with safe defaults for missing responses
      setSummary(summaryRes?.data || { error: 'Failed to load' });
      setRiskTrends(riskTrendsRes?.data || { trends: [] });
      setDeploymentTrends(deploymentTrendsRes?.data || { deployments: [] });
      setComplianceDistribution(complianceRes?.data || { total_models: 0 });
      setExecutiveSummary(executiveRes?.data || { narrative: 'System status unavailable' });

      // Check for specific errors
      const failedRequests = results.filter(r => r.status === 'rejected');
      if (failedRequests.length > 0) {
        console.warn('Some dashboard requests failed:', failedRequests);
      }

      setLoading(false);
    } catch (err: any) {
      console.error('Dashboard load error:', err);
      setError('Failed to load dashboard data: ' + (err.message || 'Unknown error'));
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="command-center-loading">
        <div className="spinner" />
        <p>Loading Executive Command Center...</p>
      </div>
    );
  }

  return (
    <div className="command-center">
      <div className="command-center-header">
        <h1>Executive Command Center</h1>
        <div className="header-controls">
          <select value={timeRange} onChange={(e) => setTimeRange(Number(e.target.value))} className="time-range-select">
            <option value={7}>Last 7 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={90}>Last 90 Days</option>
          </select>
          <button onClick={loadDashboard} className="refresh-btn">Refresh</button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

       {/* Executive Summary */}
       {executiveSummary && !executiveSummary.error && (
         <div className="command-section executive-narrative">
           <div className="narrative-card">
             <h2>Executive Narrative</h2>
             <p className="narrative-text">
               {executiveSummary.narrative || 'System operating normally'}
             </p>
            {executiveSummary.sdk_available && (
              <div className="sdk-indicator">AI-Powered Analysis</div>
            )}
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="command-section">
        <h2>System Overview</h2>
        <div className="cards-grid">
          <ExecutiveSummaryCard data={summary} />
        </div>
      </div>

      {/* Charts Section */}
      <div className="command-section">
        <h2>Trends & Distribution</h2>
        <div className="charts-grid">
          <div className="chart-container">
            <RiskOverviewChart data={riskTrends} />
          </div>
          <div className="chart-container">
            <DeploymentTrendChart data={deploymentTrends} />
          </div>
          <div className="chart-container">
            <ComplianceDistributionWidget data={complianceDistribution} />
          </div>
        </div>
      </div>

      {/* Governance Simulation */}
      <div className="command-section">
        <h2>Governance Simulation Mode</h2>
        <GovernanceSimulationPanel />
      </div>

      <footer className="command-footer">
        <p>Phase 7: Executive Command Center • Read-only • Safe Sandbox</p>
      </footer>
    </div>
  );
}
