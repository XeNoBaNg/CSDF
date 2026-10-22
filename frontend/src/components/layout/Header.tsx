import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Plus, Terminal, RefreshCw } from 'lucide-react';
import type { HealthCheckResponse } from '../../types';

interface HeaderProps {
  healthData: HealthCheckResponse | null;
  isLoading: boolean;
  onRefresh: () => void;
}

export const Header: React.FC<HeaderProps> = ({ healthData, isLoading, onRefresh }) => {
  const location = useLocation();

  const getPageTitle = (pathname: string): { title: string; subtitle: string } => {
    switch (pathname) {
      case '/':
        return {
          title: 'Forensic Investigation Dashboard',
          subtitle: 'Workstation overview, evidence integrity checks, and subsystem telemetry',
        };
      case '/cases':
        return {
          title: 'Investigation Case Registry',
          subtitle: 'Saved forensic cases, associated recordings, and historical audit logs',
        };
      case '/cases/new':
        return {
          title: 'Initialize New Forensic Case',
          subtitle: 'Register investigative case metadata and stage audio evidence items',
        };
      case '/status':
        return {
          title: 'Subsystem Diagnostics & Engine Telemetry',
          subtitle: 'Live health status for storage paths, SHA-256 engines, and API endpoints',
        };
      default:
        return {
          title: 'AudioSleuth Forensic Toolkit',
          subtitle: 'Digital Audio Forensics Workstation',
        };
    }
  };

  const { title, subtitle } = getPageTitle(location.pathname);

  return (
    <header className="h-16 px-6 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md flex items-center justify-between shrink-0">
      <div>
        <h1 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          {title}
        </h1>
        <p className="text-xs text-slate-400">{subtitle}</p>
      </div>

      <div className="flex items-center gap-3">
        {/* Real-time Subsystem Status Indicator */}
        <button
          type="button"
          onClick={onRefresh}
          disabled={isLoading}
          title="Refresh backend status"
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700 text-xs text-slate-300 font-mono transition-colors disabled:opacity-60"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-slate-400 ${isLoading ? 'animate-spin' : ''}`} />
          <span>
            {healthData
              ? `${healthData.app_name} v${healthData.version}`
              : 'Checking API...'}
          </span>
        </button>

        {/* Academic Lab Tag */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] text-slate-400 font-mono">
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          <span>PICT CSDF Workstation</span>
        </div>

        {/* Quick New Case CTA if not on new case page */}
        {location.pathname !== '/cases/new' && (
          <Link
            to="/cases/new"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium shadow-xs shadow-cyan-600/20 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Case</span>
          </Link>
        )}
      </div>
    </header>
  );
};
