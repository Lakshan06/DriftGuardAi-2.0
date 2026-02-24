import axios, { AxiosError, AxiosResponse } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
  timeout: 10000,
});

// Request interceptor - add token
api.interceptors.request.use((config: any) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle errors
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError<any>) => {
    let errorMessage = 'An error occurred';
    
    if (error.response) {
      // Response received with error status
      const status = error.response.status;
      const errorData = error.response.data || {};
      
      errorMessage = errorData.detail || errorData.error || error.response.statusText || 'Server error';
      
      // Handle 401 Unauthorized - clear token and redirect to login
      if (status === 401 || status === 403) {
        localStorage.removeItem('authToken');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('userName');
        
        // Trigger reload to reset auth state
        if (window.location.pathname !== '/login') {
          setTimeout(() => {
            window.location.href = '/login';
          }, 1000);
        }
      }
    } else if (error.request) {
      // Request made but no response
      errorMessage = 'No response from server. Please check if the API is running.';
    } else {
      // Error in request setup
      errorMessage = error.message || 'Request failed';
    }
    
    const customError = new Error(errorMessage);
    return Promise.reject(customError);
  }
);

export const authAPI = {
  login: async (email: string, password: string) => {
    try {
      const response = await api.post('/auth/login', { 
        email, 
        password 
      });
      return response;
    } catch (error: any) {
      throw error;
    }
  },
  logout: () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userName');
  },
};

export const modelAPI = {
  getModels: () => {
    return api.get('/models');
  },
  getModelById: (id: string) => {
    return api.get(`/models/${id}`);
  },
  createModel: (data: any) => {
    return api.post('/models', data);
  },
  runSimulation: (id: string) => {
    return api.post(`/models/${id}/run-simulation`);
  },
  getSimulationStatus: (id: string) => {
    return api.get(`/models/${id}/simulation-status`);
  },
  resetSimulation: (id: string) => {
    return api.post(`/models/${id}/reset-simulation`);
  },
  getModelDrift: async (id: string) => {
    const response = await api.get(`/models/drift/${id}`);
    
    // Normalize drift metrics: map backend fields to frontend expectations
    // Frontend expects: { metrics: [{ feature_name, drift_score, threshold }, ...] }
    // Backend returns: { metrics: [{ feature_name, psi_value, ks_statistic, drift_detected }, ...] }
    
    if (response.data && response.data.metrics && Array.isArray(response.data.metrics)) {
      response.data.metrics = response.data.metrics.map((metric: any) => ({
        feature_name: metric.feature_name || 'unknown',
        // Map PSI value to drift_score for frontend
        drift_score: metric.psi_value !== undefined ? parseFloat(metric.psi_value) : 0,
        // Use KS statistic as threshold reference (or default to 0.1)
        threshold: metric.ks_statistic !== undefined ? parseFloat(metric.ks_statistic) : 0.1,
        drift_detected: metric.drift_detected === true,
        timestamp: metric.timestamp
      }));
    } else {
      response.data = { metrics: [] };
    }
    
    return response;
  },
  getModelFairness: async (id: string) => {
    const response = await api.get(`/models/fairness/${id}`);
    
    // Normalize fairness metrics: map backend fields to frontend expectations
    // Frontend expects: { metrics: [{ protected_group, demographic_parity, equalized_odds }, ...] }
    // Backend returns: List[FairnessMetricResponse] with different field names
    
    // Backend returns list directly OR wrapped in array
    let fairnessData = Array.isArray(response.data) ? response.data : (response.data.metrics || []);
    
    if (!Array.isArray(fairnessData)) {
      fairnessData = [];
    }
    
    // Group metrics by protected_attribute for cleaner frontend display
    const groupedMetrics: { [key: string]: any } = {};
    
    fairnessData.forEach((metric: any) => {
      const protectedAttr = metric.protected_attribute || 'unknown';
      
      if (!groupedMetrics[protectedAttr]) {
        groupedMetrics[protectedAttr] = {
          protected_group: protectedAttr,
          // Use disparity_score for demographic_parity
          demographic_parity: parseFloat(metric.disparity_score || 0),
          // Use fairness_flag converted to odds ratio
          equalized_odds: metric.fairness_flag ? 0.5 : 0.95,
          approval_rate: parseFloat(metric.approval_rate || 0)
        };
      }
    });
    
    const normalizedMetrics = Object.values(groupedMetrics);
    
    return {
      ...response,
      data: {
        metrics: normalizedMetrics.length > 0 ? normalizedMetrics : []
      }
    };
  },
  getModelRiskHistory: async (id: string) => {
    const response = await api.get(`/models/risk/${id}`);
    
    // Normalize risk history: map risk_score -> score for Recharts
    // Frontend expects: { history: [{ timestamp, score }, ...] }
    // Backend returns: { history: [{ timestamp, risk_score, fairness_component, drift_component }, ...] }
    
    if (response.data && response.data.history && Array.isArray(response.data.history)) {
      response.data.history = response.data.history.map((entry: any) => ({
        timestamp: entry.timestamp || new Date().toISOString(),
        score: entry.risk_score !== undefined ? parseFloat(entry.risk_score) : 0,
        // Keep original fields for reference but ensure score is always present
        risk_score: entry.risk_score,
        fairness_component: entry.fairness_component,
        drift_component: entry.drift_component
      }));
    } else {
      response.data = { history: [] };
    }
    
    return response;
  },
};

export const governanceAPI = {
  getPolicies: () => {
    return api.get('/governance/policies/');
  },
  createPolicy: (data: any) => {
    return api.post('/governance/policies/', data);
  },
  updatePolicy: (id: string, data: any) => {
    return api.put(`/governance/policies/${id}/`, data);
  },
  evaluateGovernance: (modelId: string) => {
    return api.post(`/governance/models/${modelId}/evaluate/`, {});
  },
  deployModel: (modelId: string, data: any) => {
    return api.post(`/governance/models/${modelId}/deploy/`, data);
  },
};

export const auditAPI = {
  getDeploymentHistory: (modelId?: string) => {
    return api.get('/audit/deployments/', { params: { model_id: modelId } });
  },
  getAuditTrail: (modelId?: string) => {
    return api.get('/audit/trail/', { params: { model_id: modelId } });
  },
};