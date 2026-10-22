import React from 'react';

export type BadgeVariant = 'healthy' | 'degraded' | 'unhealthy' | 'neutral' | 'info' | 'warning';

interface StatusBadgeProps {
  status: string;
  variant?: BadgeVariant;
  pulse?: boolean;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  variant,
  pulse = false,
  className = '',
}) => {
  // Infer variant from status string if not explicitly given
  const resolvedVariant: BadgeVariant =
    variant ||
    (status.toLowerCase() === 'healthy' || status.toLowerCase() === 'verified'
      ? 'healthy'
      : status.toLowerCase() === 'degraded'
      ? 'degraded'
      : status.toLowerCase() === 'offline' || status.toLowerCase() === 'unhealthy'
      ? 'unhealthy'
      : 'neutral');

  const variantStyles: Record<BadgeVariant, { bg: string; dot: string }> = {
    healthy: {
      bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
      dot: 'bg-emerald-400',
    },
    degraded: {
      bg: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
      dot: 'bg-amber-400',
    },
    unhealthy: {
      bg: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
      dot: 'bg-rose-400',
    },
    info: {
      bg: 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400',
      dot: 'bg-cyan-400',
    },
    warning: {
      bg: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400',
      dot: 'bg-yellow-400',
    },
    neutral: {
      bg: 'bg-slate-800 border-slate-700 text-slate-300',
      dot: 'bg-slate-400',
    },
  };

  const style = variantStyles[resolvedVariant];

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${style.bg} ${className}`}
    >
      <span className="relative flex h-2 w-2">
        {pulse && (
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${style.dot}`}
          />
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${style.dot}`} />
      </span>
      <span className="capitalize">{status}</span>
    </span>
  );
};
