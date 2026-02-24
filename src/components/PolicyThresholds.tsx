import React from 'react';
import './PolicyThresholds.css';

interface PolicyThreshold {
  label: string;
  currentValue: number;
  policyLimit: number;
  unit?: string;
  description?: string;
  severity?: 'safe' | 'warning' | 'critical';
}

interface PolicyThresholdsProps {
  thresholds: PolicyThreshold[];
  policyName?: string;
}

function getSeverity(current: number, limit: number): 'safe' | 'warning' | 'critical' {
  const ratio = current / limit;
  if (ratio >= 1.0) return 'critical';
  if (ratio >= 0.75) return 'warning';
  return 'safe';
}

function getPercentageWidth(current: number, limit: number): number {
  return Math.min((current / limit) * 100, 100);
}

export function PolicyThresholds({ thresholds, policyName }: PolicyThresholdsProps) {
  return (
    <div className="policy-thresholds-container">
      {policyName && (
        <h3 className="policy-name">Policy: {policyName}</h3>
      )}
      
      <div className="thresholds-list">
        {thresholds.map((threshold, index) => {
          const severity = threshold.severity || getSeverity(threshold.currentValue, threshold.policyLimit);
          const percentageWidth = getPercentageWidth(threshold.currentValue, threshold.policyLimit);
          
          return (
            <div key={index} className={`threshold-item severity-${severity}`}>
              <div className="threshold-header">
                <label className="threshold-label">{threshold.label}</label>
                <span className={`threshold-values severity-${severity}`}>
                  {threshold.currentValue.toFixed(2)}
                  {threshold.unit && <span className="unit">{threshold.unit}</span>}
                  <span className="divider">/</span>
                  {threshold.policyLimit.toFixed(2)}
                  {threshold.unit && <span className="unit">{threshold.unit}</span>}
                </span>
              </div>
              
              {threshold.description && (
                <p className="threshold-description">{threshold.description}</p>
              )}
              
              <div className="threshold-bar-container">
                <div 
                  className={`threshold-bar-fill severity-${severity}`}
                  style={{ width: `${percentageWidth}%` }}
                >
                  <span className="bar-label">
                    {percentageWidth > 10 && `${Math.round(percentageWidth)}%`}
                  </span>
                </div>
              </div>
              
              <div className="threshold-status">
                <span className={`status-indicator severity-${severity}`}>
                  {severity === 'safe' && '✓ Safe'}
                  {severity === 'warning' && '⚠ Warning'}
                  {severity === 'critical' && '✗ Critical'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
