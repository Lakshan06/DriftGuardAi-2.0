import React from 'react';
import './SkeletonLoader.css';

export function SkeletonLoader() {
  return <div className="skeleton skeleton-line"></div>;
}

export function SkeletonChart() {
  return (
    <div className="skeleton-chart">
      <div className="skeleton skeleton-line" style={{ height: '8px', marginBottom: '12px' }}></div>
      <div className="skeleton skeleton-line" style={{ height: '8px', marginBottom: '12px' }}></div>
      <div className="skeleton skeleton-line" style={{ height: '8px', marginBottom: '12px' }}></div>
      <div className="skeleton skeleton-line" style={{ height: '200px', marginTop: '20px' }}></div>
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <div className="skeleton skeleton-line" style={{ height: '24px', width: '60%', marginBottom: '12px' }}></div>
      <div className="skeleton skeleton-line" style={{ height: '16px', marginBottom: '8px' }}></div>
      <div className="skeleton skeleton-line" style={{ height: '16px', marginBottom: '8px' }}></div>
      <div className="skeleton skeleton-line" style={{ height: '16px', width: '80%' }}></div>
    </div>
  );
}

export function SkeletonTable({ rows = 5, columns = 4 }) {
  return (
    <div className="skeleton-table">
      <div className="skeleton-table-header">
        {Array(columns).fill(null).map((_, i) => (
          <div key={i} className="skeleton skeleton-line" style={{ height: '16px' }}></div>
        ))}
      </div>
      {Array(rows).fill(null).map((_, rowIdx) => (
        <div key={rowIdx} className="skeleton-table-row">
          {Array(columns).fill(null).map((_, colIdx) => (
            <div key={colIdx} className="skeleton skeleton-line" style={{ height: '14px', width: '80%' }}></div>
          ))}
        </div>
      ))}
    </div>
  );
}
