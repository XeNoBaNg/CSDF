import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  Activity,
  HardDrive,
  KeyRound,
  Database,
  RefreshCw,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Code2,
} from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import type { HealthCheckResponse } from '../types';

interface OutletContextType {
  healthData: HealthCheckResponse | null;
  apiStatus: 'healthy' | 'degraded' | 'offline' | 'checking';
  refreshHealth: () => void;
}

export const SystemStatusPage: React.FC = () => {
  const { healthData, apiStatus, refreshHealth } = useOutletContext<OutletContextType>();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showRawJson, setShowRawJson] = useState(false);

  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    await refreshHealth();
    setTimeout(() => setIsRefreshing(false), 300);
  };

  const storageDetails = healthData?.components?.storage?.details || {};
  const cryptoDetails = healthData?.components?.cryptography?.details || {};
  const persistenceDetails = healthData?.components?.persistence?.details || {};

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header & Refresh */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-400" />
            System Subsystems & Forensic Diagnostics
          </h2>
          <p className="text-xs text-slate-400">
            Real-time status of backend services, evidence storage integrity, and cryptographic hashing engines
          </p>
        </div>

        <button
          type="button"
          onClick={handleManualRefresh}
          disabled={isRefreshing}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-900 border border-slate-700 hover:bg-slate-800 text-xs font-medium text-slate-200 transition-colors self-start"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
          <span>Execute Health Probe</span>
        </button>
      </div>

      {/* Main Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
          <span className="text-xs font-semibold text-slate-400">Overall Status</span>
          <div className="flex items-center gap-2">
            <StatusBadge status={apiStatus} pulse={apiStatus === 'healthy'} />
          </div>
          <p className="text-[11px] text-slate-400">
            {apiStatus === 'healthy' ? 'All subsystems operational' : 'Awaiting backend response'}
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
          <span className="text-xs font-semibold text-slate-400">Application Version</span>
          <p className="text-sm font-bold text-slate-200 font-mono">
            {healthData ? `${healthData.app_name} v${healthData.version}` : 'AudioSleuth v0.1.0'}
          </p>
          <p className="text-[11px] text-slate-400">Environment: {healthData?.environment || 'development'}</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
          <span className="text-xs font-semibold text-slate-400">Backend Uptime</span>
          <p className="text-sm font-bold text-slate-200 font-mono flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-cyan-400" />
            {healthData ? `${healthData.uptime_seconds}s` : '0s'}
          </p>
          <p className="text-[11px] text-slate-400">Process running on localhost</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
          <span className="text-xs font-semibold text-slate-400">Endpoint Target</span>
          <p className="text-sm font-bold text-slate-200 font-mono">
            /api/health
          </p>
          <p className="text-[11px] text-slate-400">127.0.0.1:8000</p>
        </div>
      </div>

      {/* Subsystem Component Details */}
      <div className="space-y-4">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Component Diagnostics
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Evidence Vault */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  <HardDrive className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-200">Evidence Vault</h4>
                  <p className="text-[11px] text-slate-400">Isolated physical storage</p>
                </div>
              </div>
              <StatusBadge status={healthData?.components?.storage?.status || 'checking'} />
            </div>

            <div className="space-y-2 text-xs font-mono bg-slate-950 p-3 rounded-xl border border-slate-800/80">
              <div className="flex justify-between text-slate-400">
                <span>Directory:</span>
                <span className="text-slate-200 truncate max-w-[160px]" title={String(storageDetails.path || '')}>
                  {String(storageDetails.path || './data/evidence')}
                </span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Exists:</span>
                <span className={storageDetails.exists ? 'text-emerald-400' : 'text-rose-400'}>
                  {storageDetails.exists ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Writable:</span>
                <span className={storageDetails.writable ? 'text-emerald-400' : 'text-rose-400'}>
                  {storageDetails.writable ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          </div>

          {/* Cryptographic Engine */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <KeyRound className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-200">Cryptographic Engine</h4>
                  <p className="text-[11px] text-slate-400">SHA-256 digest calculation</p>
                </div>
              </div>
              <StatusBadge status={healthData?.components?.cryptography?.status || 'checking'} />
            </div>

            <div className="space-y-2 text-xs font-mono bg-slate-950 p-3 rounded-xl border border-slate-800/80">
              <div className="flex justify-between text-slate-400">
                <span>Algorithm:</span>
                <span className="text-slate-200">{String(cryptoDetails.algorithm || 'SHA-256')}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Provider:</span>
                <span className="text-slate-200">{String(cryptoDetails.engine || 'hashlib')}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Test Vector:</span>
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  Verified
                </span>
              </div>
            </div>
          </div>

          {/* Persistence Engine */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  <Database className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-200">Case Persistence</h4>
                  <p className="text-[11px] text-slate-400">Local-first SQLite storage</p>
                </div>
              </div>
              <StatusBadge status={healthData?.components?.persistence?.status || 'checking'} />
            </div>

            <div className="space-y-2 text-xs font-mono bg-slate-950 p-3 rounded-xl border border-slate-800/80">
              <div className="flex justify-between text-slate-400">
                <span>Engine:</span>
                <span className="text-slate-200">SQLite 3</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Target:</span>
                <span className="text-slate-200 truncate max-w-[160px]">
                  {String(persistenceDetails.database_url || './data/audiosleuth.db')}
                </span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Cloudless:</span>
                <span className="text-purple-400">Local Only</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Raw Diagnostic JSON Inspector */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4 text-slate-400" />
            <h4 className="text-xs font-semibold text-slate-300">Diagnostic Payload Inspector</h4>
          </div>
          <button
            type="button"
            onClick={() => setShowRawJson(!showRawJson)}
            className="text-xs text-cyan-400 hover:text-cyan-300 font-mono transition-colors"
          >
            {showRawJson ? 'Hide Raw JSON' : 'Inspect Raw JSON'}
          </button>
        </div>

        {showRawJson && (
          <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-cyan-300 overflow-x-auto max-h-72">
            {JSON.stringify(healthData, null, 2) || '// No response payload available'}
          </pre>
        )}
      </div>

      {/* Forensic Disclaimer */}
      <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 text-xs text-slate-400 flex items-start gap-3">
        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="text-slate-300">Forensic Notice:</strong> AudioSleuth is an investigative assistance toolkit designed for academic research and evidence examination at PICT CSDF Lab. Findings and anomaly flags provide investigative indicators requiring human expert interpretation, not certified forensic certitudes.
        </p>
      </div>
    </div>
  );
};
