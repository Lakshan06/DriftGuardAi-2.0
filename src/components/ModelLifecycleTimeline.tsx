import React from 'react';
import './ModelLifecycleTimeline.css';

interface TimelineEvent {
  status: string;
  timestamp?: string;
  label: string;
  icon: string;
  description?: string;
}

interface ModelLifecycleTimelineProps {
  currentStatus: string;
  createdAt?: string;
  deployedAt?: string;
  hasOverride?: boolean;
}

export function ModelLifecycleTimeline({ 
  currentStatus, 
  createdAt,
  deployedAt,
  hasOverride 
}: ModelLifecycleTimelineProps) {
  
  const statuses = ['draft', 'evaluated', 'approved', 'deployed', 'override'];
  
  const getTimelineEvents = (): TimelineEvent[] => {
    const events: TimelineEvent[] = [
      {
        status: 'draft',
        timestamp: createdAt,
        label: 'Draft',
        icon: '📝',
        description: 'Model registered in system'
      },
      {
        status: 'evaluated',
        label: 'Evaluated',
        icon: '📊',
        description: 'Governance evaluation completed'
      },
      {
        status: 'approved',
        label: 'Approved',
        icon: '✅',
        description: 'Passed governance checks'
      },
      {
        status: 'deployed',
        timestamp: deployedAt,
        label: 'Deployed',
        icon: '🚀',
        description: 'Deployed to production'
      }
    ];
    
    if (hasOverride) {
      events.push({
        status: 'override',
        label: 'Override',
        icon: '⚠️',
        description: 'Deployed with governance override'
      });
    }
    
    return events;
  };
  
  const isStatusActive = (status: string): boolean => {
    const statusOrder = ['draft', 'evaluated', 'approved', 'deployed', 'override', 'at_risk', 'blocked'];
    const currentIndex = statusOrder.indexOf(currentStatus.toLowerCase());
    const statusIndex = statusOrder.indexOf(status);
    return statusIndex <= currentIndex;
  };
  
  const isStatusCurrent = (status: string): boolean => {
    return status.toLowerCase() === currentStatus.toLowerCase();
  };
  
  const events = getTimelineEvents();
  
  return (
    <div className="timeline-container">
      <div className="timeline">
        {events.map((event, index) => (
          <div key={index} className="timeline-item">
            <div className={`timeline-dot ${isStatusCurrent(event.status) ? 'current' : ''} ${isStatusActive(event.status) ? 'active' : 'inactive'}`}>
              <span className="timeline-icon">{event.icon}</span>
            </div>
            {index < events.length - 1 && (
              <div className={`timeline-line ${isStatusActive(event.status) && isStatusActive(events[index + 1].status) ? 'active' : ''}`}></div>
            )}
            <div className="timeline-content">
              <h4 className={`timeline-label ${isStatusCurrent(event.status) ? 'current' : ''}`}>
                {event.label}
              </h4>
              {event.description && (
                <p className="timeline-description">{event.description}</p>
              )}
              {event.timestamp && (
                <p className="timeline-timestamp">
                  {new Date(event.timestamp).toLocaleString()}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
