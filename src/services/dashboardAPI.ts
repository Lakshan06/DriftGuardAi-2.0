import { api } from './api';

export const dashboardAPI = {
  // Get summary metrics
  getSummary: () => {
    console.log('Fetching dashboard summary');
    return api.get('/dashboard/summary');
  },

  // Get risk trends
  getRiskTrends: (days: number = 30) => {
    console.log('Fetching risk trends', { days });
    return api.get('/dashboard/risk-trends', { params: { days } });
  },

  // Get deployment trends
  getDeploymentTrends: (days: number = 30) => {
    console.log('Fetching deployment trends', { days });
    return api.get('/dashboard/deployment-trends', { params: { days } });
  },

  // Get compliance distribution
  getComplianceDistribution: () => {
    console.log('Fetching compliance distribution');
    return api.get('/dashboard/compliance-distribution');
  },

  // Get executive summary with narrative
  getExecutiveSummary: () => {
    console.log('Fetching executive summary');
    return api.get('/dashboard/executive-summary');
  },

  // Governance simulation
  simulateGovernanceCheck: (data: {
    risk_score: number;
    fairness_score: number;
    override?: boolean;
  }) => {
    console.log('Running governance simulation', data);
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
    console.log('Running batch governance simulation', { count: requests.length });
    return api.post('/simulation/batch-governance-check', requests);
  },
};
