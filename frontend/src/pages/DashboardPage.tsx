import React, { useEffect, useState } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import {
  FolderArchive,
  HardDrive,
  KeyRound,
  Database,
  Plus,
  ArrowRight,
  AudioLines,
  FileText,
  Activity,
  FolderOpen,
  FileDown,
  ShieldCheck,
  GitCompare,
} from 'lucide-react';
import { listCases } from '../api/cases';
import { EmptyState } from '../components/common/EmptyState';
import { StatusBadge } from '../components/common/StatusBadge';
import type { ForensicCase, HealthCheckResponse } from '../types';

interface OutletContextType {
  healthData: HealthCheckResponse | null;
  apiStatus: 'healthy' | 'degraded' | 'offline' | 'checking';
  refreshHealth: () => void;
}

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { healthData, apiStatus } = useOutletContext<OutletContextType>();
  const [cases, setCases] = useState<ForensicCase[]>([]);

  useEffect(() => {
    listCases()
      .then((data) => setCases(data.cases))
      .catch((err) => console.warn('Could not load dashboard cases:', err));
  }, []);

  const storageStatus = healthData?.components?.storage?.status || 'checking';
  const cryptoStatus = healthData?.components?.cryptography?.status || 'checking';
  const persistenceStatus = healthData?.components?.persistence?.status || 'checking';

  const latestCase = cases.length > 0 ? cases[0] : null;
  const totalEvidenceCount = cases.reduce((acc, c) => acc + c.evidence_count, 0);

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Forensic Notice Banner */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 mt-0.5">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-200">
              AudioSleuth Forensic Workstation — Phase 5 Case Management, SQLite Persistence & Audit Logging Active
            </h2>
            <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
              Durable SQLite case registry, lifecycle management (active/closed), non-destructive audio inspection, SHA-256 verification, explainable RMS/STFT signal detectors, and ISO/IEC 27037-compliant structured audit logging are fully operational.
            </p>
          </div>
        </div>
        <div className="shrink-0 flex items-center gap-2">
          <StatusBadge status={apiStatus} pulse={apiStatus === 'healthy'} />
        </div>
      </div>

      {/* Subsystem Readiness Telemetry */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Workstation Subsystem Telemetry
          </h2>
          <button
            onClick={() => navigate('/status')}
            className="text-xs text-cyan-400 hover:text-cyan-300 font-medium inline-flex items-center gap-1 transition-colors"
          >
            <span>Full Diagnostics</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Storage Telemetry */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 flex items-center gap-2">
                <HardDrive className="w-4 h-4 text-cyan-400" />
                Evidence Vault
              </span>
              <StatusBadge status={storageStatus} />
            </div>
            <div>
              <p className="text-lg font-bold text-slate-200 font-mono">
                {storageStatus === 'healthy' ? 'Local Vault Ready' : 'Pending Verification'}
              </p>
              <p className="text-[11px] text-slate-400 font-mono truncate mt-1">
                Preserved Evidence: {totalEvidenceCount} item(s)
              </p>
            </div>
          </div>

          {/* Cryptographic Engine */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 flex items-center gap-2">
                <KeyRound className="w-4 h-4 text-emerald-400" />
                Hashing Engine
              </span>
              <StatusBadge status={cryptoStatus} />
            </div>
            <div>
              <p className="text-lg font-bold text-slate-200 font-mono">
                SHA-256 Verified
              </p>
              <p className="text-[11px] text-slate-400 font-mono mt-1">
                Constant-Time Verification Active
              </p>
            </div>
          </div>

          {/* Persistence */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 flex items-center gap-2">
                <Database className="w-4 h-4 text-purple-400" />
                Case Persistence & Audit
              </span>
              <StatusBadge status={persistenceStatus} />
            </div>
            <div>
              <p className="text-lg font-bold text-slate-200 font-mono">
                SQLite Registry
              </p>
              <p className="text-[11px] text-slate-400 font-mono mt-1">
                {cases.length} Case(s) • Active: {cases.filter((c) => c.status === 'active').length} • Closed: {cases.filter((c) => c.status === 'closed').length}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Main Workspace Panels */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Investigation Card */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <FolderArchive className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-semibold text-slate-200">Active Investigation Case</h3>
            </div>
            {latestCase ? (
              <span
                className={`text-[11px] font-mono px-2 py-0.5 rounded border uppercase tracking-wider font-bold ${
                  latestCase.status === 'closed'
                    ? 'bg-amber-950/30 text-amber-300 border-amber-500/30'
                    : 'bg-emerald-950/30 text-emerald-300 border-emerald-500/30'
                }`}
              >
                {latestCase.status}
              </span>
            ) : (
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                Awaiting Intake
              </span>
            )}
          </div>

          {latestCase ? (
            <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3 my-auto">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-cyan-400 font-semibold">{latestCase.id}</span>
                <span className="text-[11px] text-slate-400 font-mono">{latestCase.evidence_count} evidence items</span>
              </div>
              <h4 className="text-base font-bold text-slate-100">{latestCase.title}</h4>
              <p className="text-xs text-slate-400">
                Lead Examiner: <span className="text-slate-200">{latestCase.investigator_name}</span>
              </p>
              {(latestCase.description || latestCase.notes) && (
                <p className="text-xs text-slate-400 italic line-clamp-2">{latestCase.description || latestCase.notes}</p>
              )}
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => navigate(`/cases/new?caseId=${encodeURIComponent(latestCase.id)}`)}
                  className="w-full inline-flex items-center justify-center gap-2 px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-xs transition-colors"
                >
                  <FolderOpen className="w-3.5 h-3.5" />
                  <span>Open Case & Manage Evidence</span>
                </button>
              </div>
            </div>
          ) : (
            <EmptyState
              icon={FolderArchive}
              title="No Active Case Loaded"
              description="Start a new investigation to register case metadata, record evidence files, and calculate cryptographic SHA-256 hashes."
              actionText="Start Investigation"
              onAction={() => navigate('/cases/new')}
              className="my-auto py-10"
            />
          )}

          <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span>Evidence Preserved: {totalEvidenceCount} files</span>
            <span>Total Cases: {cases.length}</span>
          </div>
        </div>

        {/* Forensic Signal Analysis Engine */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <AudioLines className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-semibold text-slate-200">Signal Anomaly Detectors</h3>
            </div>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-950/30 text-emerald-300 border border-emerald-500/30 font-bold">
              Operational
            </span>
          </div>

          <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3 my-auto">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-emerald-400 font-semibold">Phase 4 Engine</span>
              <span className="text-[11px] text-slate-400 font-mono">3 Detectors Active</span>
            </div>
            <h4 className="text-base font-bold text-slate-100">Explainable Audio Forensic Engine</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Short-time RMS energy silence detection, adjacent-sample amplitude transition analysis with temporal suppression, and normalized STFT spectral flux inconsistency analysis are online.
            </p>
            <div className="pt-2">
              <button
                type="button"
                onClick={() => navigate('/cases')}
                className="w-full inline-flex items-center justify-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold shadow-xs transition-colors"
              >
                <FolderArchive className="w-3.5 h-3.5" />
                <span>Select Case Evidence to Inspect</span>
              </button>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span>Configured Detectors: 3</span>
            <span>Mathematical Basis: RMS & STFT</span>
          </div>
        </div>
      </section>

      {/* Forensic Report & Investigation History Overview */}
      <section className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-slate-200">Forensic Reports & Chain of Custody</h3>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-950/30 text-emerald-300 border border-emerald-500/30 font-bold">
            Phase 6A Operational
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-cyan-400 font-semibold text-xs">
              <FileDown className="w-4 h-4" />
              <span>Evidence-Based PDF Generation</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Dynamically compiles case metadata, custody records, signal parameters, explainable anomaly findings, and durable audit logs into downloadable PDF reports.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold text-xs">
              <ShieldCheck className="w-4 h-4" />
              <span>Mandatory Integrity Re-Verification</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Recalculates physical SHA-256 before report compilation. Rejects tampered files with HTTP 400 <span className="font-mono text-rose-400">INTEGRITY_MISMATCH</span>.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-purple-400 font-semibold text-xs">
              <AudioLines className="w-4 h-4" />
              <span>Embedded Acoustic Visualizations</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Generates high-resolution in-memory waveform envelopes and calibrated STFT spectrogram charts embedded directly in report pages.
            </p>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <span className="text-slate-400 italic">
            ISO/IEC 27037 Disclaimer: Algorithmic findings are investigative indicators requiring human interpretation, not proof of tampering.
          </span>
          <button
            type="button"
            onClick={() => navigate(latestCase ? `/cases/new?caseId=${encodeURIComponent(latestCase.id)}` : '/cases')}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 border border-cyan-500/30 font-medium transition-colors shrink-0"
          >
            <FolderOpen className="w-3.5 h-3.5" />
            <span>Generate Reports in Case Vault</span>
          </button>
        </div>
      </section>

      {/* Investigation Action Guidance */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          onClick={() => navigate('/cases/new')}
          className="p-5 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500/50 cursor-pointer transition-all duration-150 flex items-center justify-between group shadow-xs"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Plus className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-200">New Investigation</h4>
              <p className="text-xs text-slate-400">Set up case & intake evidence</p>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-cyan-400 group-hover:translate-x-1 transition-all" />
        </div>

        <div
          onClick={() => navigate('/compare')}
          className="p-5 rounded-xl bg-slate-900 border border-slate-800 hover:border-purple-500/50 cursor-pointer transition-all duration-150 flex items-center justify-between group shadow-xs"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center group-hover:scale-105 transition-transform">
              <GitCompare className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-200">Cross-Comparison</h4>
              <p className="text-xs text-slate-400">Audio & spectral diff</p>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-purple-400 group-hover:translate-x-1 transition-all" />
        </div>

        <div
          onClick={() => navigate('/cases')}
          className="p-5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 cursor-pointer transition-all duration-150 flex items-center justify-between group shadow-xs"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-slate-800 text-slate-400 border border-slate-700 flex items-center justify-center group-hover:scale-105 transition-transform">
              <FolderArchive className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-200">Case Registry & Audit</h4>
              <p className="text-xs text-slate-400">View logs & case files</p>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-slate-200 group-hover:translate-x-1 transition-all" />
        </div>
      </section>
    </div>
  );
};
