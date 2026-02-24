interface StatusBadgeProps {
  status: 'active' | 'inactive' | 'monitoring' | 'alert' | 'approved' | 'pending' | 'rejected' | 'success' | 'failed' | 'in_progress' | string;
  children: string;
}

export function StatusBadge({ status, children }: StatusBadgeProps) {
  const statusClasses: Record<string, string> = {
    active: 'badge-active',
    inactive: 'badge-inactive',
    monitoring: 'badge-monitoring',
    alert: 'badge-alert',
    approved: 'badge-approved',
    pending: 'badge-pending',
    rejected: 'badge-rejected',
    success: 'badge-success',
    failed: 'badge-failed',
    in_progress: 'badge-in-progress',
  };

  const badgeClass = statusClasses[status] || 'badge-inactive';
  return <span className={`badge ${badgeClass}`}>{children || status}</span>;
}