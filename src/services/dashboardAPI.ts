import { api } from './api';

export const dashboardAPI = {
  // Get summary metrics
  getSummary: () => {
    return api.get('/dashboard/summary');
  },

  // Get risk trends
  getRiskTrends: (days: number = 30) => {
    return api.get('/dashboard/risk-trends', { params: { days } });
  },

  // Get deployment trends
  getDeploymentTrends: (days: number = 30) => {
    return api.get('/dashboard/deployment-trends', { params: { days } });
  },

  // Get compliance distribution
  getComplianceDistribution: () => {
    return api.get('/dashboard/compliance-distribution');
  },

  // Get executive summary with narrative
  getExecutiveSummary: () => {
    return api.get('/dashboard/executive-summary');
  },

  // Governance simulation
  simulateGovernanceCheck: (data: {
    risk_score: number;
    fairness_score: number;
    override?: boolean;
  }) => {
    return api.post('/simulation/governance-check', data);
  },

  // Batch governance simulation
  simulateBatchGovernanceCheck: (
    requests: Array<{
      risk_score: number;
      fairness_score: number;
      override?: boolean;
    }>
  ) => {
    return api.post('/simulation/batch-governance-check', requests);
  },
};
