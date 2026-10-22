import React, { useState } from 'react';
import {
  VolumeX,
  Zap,
  Radio,
  Clock,
  ExternalLink,
  Info,
  CheckCircle2,
  HelpCircle,
} from 'lucide-react';
import type { ForensicFinding, FindingCategory, ReviewPriority } from '../../types';

interface FindingsListProps {
  findings: ForensicFinding[];
  onSeekToTimestamp?: (seconds: number) => void;
  selectedFindingId?: string | null;
  onSelectFinding?: (findingId: string) => void;
}

export const FindingsList: React.FC<FindingsListProps> = ({
  findings,
  onSeekToTimestamp,
  selectedFindingId,
  onSelectFinding,
}) => {
  const [categoryFilter, setCategoryFilter] = useState<'all' | FindingCategory>('all');
  const [priorityFilter, setPriorityFilter] = useState<'all' | ReviewPriority>('all');

  const filteredFindings = findings.filter((f) => {
    if (categoryFilter !== 'all' && f.category !== categoryFilter) return false;
    if (priorityFilter !== 'all' && f.priority !== priorityFilter) return false;
    return true;
  });

  const countByCategory = {
    all: findings.length,
    silence: findings.filter((f) => f.category === 'silence').length,
    transition: findings.filter((f) => f.category === 'transition').length,
    spectral: findings.filter((f) => f.category === 'spectral').length,
  };

  const getPriorityStyle = (priority: ReviewPriority) => {
    switch (priority) {
      case 'high':
        return 'bg-rose-500/10 border-rose-500/30 text-rose-400';
      case 'medium':
        return 'bg-amber-500/10 border-amber-500/30 text-amber-400';
      case 'low':
        return 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400';
      default:
        return 'bg-slate-800 border-slate-700 text-slate-300';
    }
  };

  const getCategoryIcon = (category: FindingCategory) => {
    switch (category) {
      case 'silence':
        return <VolumeX className="w-3.5 h-3.5 text-cyan-400" />;
      case 'transition':
        return <Zap className="w-3.5 h-3.5 text-rose-400" />;
      case 'spectral':
        return <Radio className="w-3.5 h-3.5 text-purple-400" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Category and Priority Filter Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-900 border border-slate-800">
        {/* Category Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 text-xs">
          <button
            type="button"
            onClick={() => setCategoryFilter('all')}
            className={`px-3 py-1 rounded-lg font-medium transition-colors ${
              categoryFilter === 'all'
                ? 'bg-slate-800 text-slate-100 border border-slate-700'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All Findings ({countByCategory.all})
          </button>

          <button
            type="button"
            onClick={() => setCategoryFilter('silence')}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg font-medium transition-colors ${
              categoryFilter === 'silence'
                ? 'bg-cyan-950/40 text-cyan-300 border border-cyan-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <VolumeX className="w-3 h-3 text-cyan-400" />
            <span>Silence ({countByCategory.silence})</span>
          </button>

          <button
            type="button"
            onClick={() => setCategoryFilter('transition')}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg font-medium transition-colors ${
              categoryFilter === 'transition'
                ? 'bg-rose-950/40 text-rose-300 border border-rose-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Zap className="w-3 h-3 text-rose-400" />
            <span>Transitions ({countByCategory.transition})</span>
          </button>

          <button
            type="button"
            onClick={() => setCategoryFilter('spectral')}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg font-medium transition-colors ${
              categoryFilter === 'spectral'
                ? 'bg-purple-950/40 text-purple-300 border border-purple-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Radio className="w-3 h-3 text-purple-400" />
            <span>Spectral Flux ({countByCategory.spectral})</span>
          </button>
        </div>

        {/* Priority Filter */}
        <div className="flex items-center gap-2 self-start sm:self-auto text-xs">
          <span className="text-slate-500 text-[11px]">Priority:</span>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value as 'all' | ReviewPriority)}
            className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-lg px-2.5 py-1 focus:outline-none focus:border-cyan-500"
          >
            <option value="all">All Priorities</option>
            <option value="high">High Priority</option>
            <option value="medium">Medium Priority</option>
            <option value="low">Low Priority</option>
          </select>
        </div>
      </div>

      {/* Findings List or Empty State */}
      {filteredFindings.length > 0 ? (
        <div className="space-y-3">
          {filteredFindings.map((finding) => {
            const isSelected = selectedFindingId === finding.id;

            return (
              <div
                key={finding.id}
                onClick={() => onSelectFinding && onSelectFinding(finding.id)}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-slate-900 border-cyan-500 shadow-md ring-1 ring-cyan-500/40'
                    : 'bg-slate-900/80 border-slate-800 hover:border-slate-700 shadow-xs'
                }`}
              >
                {/* Finding Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-2.5">
                  <div className="flex items-center gap-2.5">
                    {/* Category Icon & Name */}
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-950 border border-slate-800 capitalize text-slate-200">
                      {getCategoryIcon(finding.category)}
                      <span>{finding.category} Anomaly</span>
                    </span>

                    {/* Priority Badge */}
                    <span
                      className={`px-2 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider border ${getPriorityStyle(
                        finding.priority
                      )}`}
                    >
                      {finding.priority} Priority
                    </span>

                    <span className="text-[11px] font-mono text-slate-500 hidden sm:inline">
                      {finding.id}
                    </span>
                  </div>

                  {/* Timestamp & Click-to-Seek Button */}
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onSeekToTimestamp) {
                          onSeekToTimestamp(finding.event_time ?? finding.start_time);
                        }
                      }}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-950 hover:bg-slate-800 text-cyan-400 hover:text-cyan-300 border border-slate-800 text-xs font-mono font-semibold transition-colors"
                      title="Seek player and visualizers to this timestamp"
                    >
                      <Clock className="w-3 h-3" />
                      <span>
                        {finding.start_time.toFixed(3)}s → {finding.end_time.toFixed(3)}s
                      </span>
                      <ExternalLink className="w-3 h-3 ml-0.5 opacity-70" />
                    </button>
                  </div>
                </div>

                {/* Finding Body */}
                <div className="pt-3 space-y-2.5">
                  {/* Metric Box */}
                  <div className="flex flex-wrap items-center gap-3 text-xs font-mono bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/80">
                    <span className="text-slate-400">
                      Metric ({finding.metric_name}):
                    </span>
                    <span className="text-cyan-300 font-bold">
                      {finding.measured_value.toFixed(4)} {finding.units}
                    </span>
                    <span className="text-slate-600">•</span>
                    <span className="text-slate-400">Decision Threshold:</span>
                    <span className="text-amber-300">
                      {finding.applied_threshold.toFixed(4)}
                    </span>
                    <span className="text-slate-600">•</span>
                    <span className="text-slate-400">Duration:</span>
                    <span className="text-slate-200">
                      {finding.duration_seconds.toFixed(3)}s
                    </span>
                  </div>

                  {/* Forensic Explanation */}
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {finding.explanation}
                  </p>

                  {/* Suggested Manual Review Action */}
                  <div className="p-2.5 rounded-lg bg-cyan-950/20 border border-cyan-500/20 text-xs text-cyan-200/90 flex items-start gap-2">
                    <HelpCircle className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-cyan-300 block text-[11px] uppercase tracking-wider">
                        Investigative Recommendation
                      </span>
                      <p className="text-[11px] text-cyan-100/80 mt-0.5">
                        {finding.suggested_action}
                      </p>
                    </div>
                  </div>

                  {/* Disclaimer notice */}
                  <p className="text-[10px] text-slate-500 italic border-t border-slate-800/50 pt-1.5 flex items-center gap-1">
                    <Info className="w-3 h-3 text-slate-500 shrink-0" />
                    <span>{finding.disclaimer}</span>
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="p-8 rounded-xl bg-slate-900/60 border border-slate-800 text-center space-y-2">
          <CheckCircle2 className="w-6 h-6 text-emerald-400 mx-auto" />
          <h4 className="text-xs font-bold text-slate-200">
            {findings.length === 0
              ? 'No Signal Anomalies Detected'
              : 'No Findings Match Active Filters'}
          </h4>
          <p className="text-[11px] text-slate-400 max-w-md mx-auto">
            {findings.length === 0
              ? 'Audio exhibits continuous acoustic characteristics within the configured decision thresholds. Zero silence intervals, amplitude discontinuities, or spectral flux spikes detected.'
              : 'Try clearing the priority or category filter to inspect findings from other detectors.'}
          </p>
        </div>
      )}
    </div>
  );
};
