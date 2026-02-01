import React from 'react';
import { PortfolioStatus } from '../types';

interface StatusBadgeProps {
  status: PortfolioStatus;
}

const statusConfig: Record<PortfolioStatus, { color: string; bg: string; label: string }> = {
  [PortfolioStatus.Draft]: { color: '#cbd5e1', bg: 'rgba(100, 116, 139, 0.2)', label: 'Draft' },
  [PortfolioStatus.Submitted]: { color: '#60a5fa', bg: 'rgba(59, 130, 246, 0.2)', label: 'Submitted' },
  [PortfolioStatus.PendingVote]: { color: '#facc15', bg: 'rgba(234, 179, 8, 0.2)', label: 'Pending Vote' },
  [PortfolioStatus.Approved]: { color: '#4ade80', bg: 'rgba(34, 197, 94, 0.2)', label: 'Approved' },
  [PortfolioStatus.Rejected]: { color: '#f87171', bg: 'rgba(239, 68, 68, 0.2)', label: 'Rejected' },
  [PortfolioStatus.Promoted]: { color: '#c084fc', bg: 'rgba(168, 85, 247, 0.2)', label: 'Promoted' },
};

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const config = statusConfig[status];

  return (
    <div
      className="px-4 py-1.5 rounded-full border text-sm font-semibold uppercase tracking-wide flex items-center gap-2"
      style={{
        backgroundColor: config.bg,
        borderColor: config.color,
        color: config.color,
      }}
    >
      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: config.color }}></span>
      {config.label}
    </div>
  );
};

export default StatusBadge;