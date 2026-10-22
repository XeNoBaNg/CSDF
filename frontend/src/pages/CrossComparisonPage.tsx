import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  GitCompare,
  ArrowRight,
  ShieldCheck,
  FileAudio,
  RefreshCw,
  AlertTriangle,
  FileDown,
  Layers,
  Activity,
  SlidersHorizontal,
  Copy,
  Check,
  Search,
} from 'lucide-react';
import {
  listAllEvidence,
  compareEvidence,
  downloadComparisonReport,
} from '../api/comparison';
import { StatusBadge } from '../components/common/StatusBadge';
import type {
  ComparisonResponse,
  EvidenceItem,
} from '../types';

export const CrossComparisonPage: React.FC = () => {
  const [searchParams] = useSearchParams();

  const initialEvidenceA = searchParams.get('evidenceA') || '';
  const initialEvidenceB = searchParams.get('evidenceB') || '';

  // Evidence Selection State
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [selectedIdA, setSelectedIdA] = useState<string>(initialEvidenceA);
  const [selectedIdB, setSelectedIdB] = useState<string>(initialEvidenceB);
  const [searchA, setSearchA] = useState('');
  const [searchB, setSearchB] = useState('');

  // Options State
  const [includeAnomaly, setIncludeAnomaly] = useState(true);
  const [envelopePoints] = useState(500);

  // Execution & Result State
  const [isLoadingEvidence, setIsLoadingEvidence] = useState(true);
  const [isComparing, setIsComparing] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  // Load available evidence list on mount
  const loadEvidence = useCallback(async () => {
    setIsLoadingEvidence(true);
    try {
      const items = await listAllEvidence();
      setEvidenceList(items);

      // Auto-select if query params provided and exist
      if (initialEvidenceA && items.some((i) => i.id === initialEvidenceA)) {
        setSelectedIdA(initialEvidenceA);
      } else if (items.length > 0 && !selectedIdA) {
        setSelectedIdA(items[0].id);
      }

      if (initialEvidenceB && items.some((i) => i.id === initialEvidenceB)) {
        setSelectedIdB(initialEvidenceB);
      } else if (items.length > 1 && !selectedIdB) {
        setSelectedIdB(items[1].id);
      }
    } catch (err) {
      console.error('Failed to load evidence items:', err);
      setError('Failed to query registered evidence list.');
    } finally {
      setIsLoadingEvidence(false);
    }
  }, [initialEvidenceA, initialEvidenceB, selectedIdA, selectedIdB]);

  useEffect(() => {
    loadEvidence();
  }, [loadEvidence]);

  // Execute comparison
  const handleExecuteComparison = async () => {
    if (!selectedIdA || !selectedIdB) {
      setError('Please select two evidence recordings to compare.');
      return;
    }

    setIsComparing(true);
    setError(null);

    try {
      const result = await compareEvidence({
        evidence_id_a: selectedIdA,
        evidence_id_b: selectedIdB,
        include_anomaly_comparison: includeAnomaly,
        envelope_points: envelopePoints,
      });
      setComparison(result);
    } catch (err: unknown) {
      const errorMsg =
        (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data
          ?.error?.message || (err as Error)?.message || 'Failed to execute cross-recording comparison.';
      setError(errorMsg);
    } finally {
      setIsComparing(false);
    }
  };

  // Export comparison PDF report
  const handleDownloadPdf = async () => {
    if (!comparison) return;
    setIsExportingPdf(true);
    try {
      await downloadComparisonReport(comparison.id);
    } catch (err: unknown) {
      const errorMsg =
        (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data
          ?.error?.message || (err as Error)?.message || 'Failed to download comparison PDF report.';
      setError(errorMsg);
    } finally {
      setIsExportingPdf(false);
    }
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(key);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const formatBytes = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const selectedItemA = evidenceList.find((i) => i.id === selectedIdA);
  const selectedItemB = evidenceList.find((i) => i.id === selectedIdB);

  const filteredListA = evidenceList.filter(
    (i) =>
      i.original_filename.toLowerCase().includes(searchA.toLowerCase()) ||
      i.id.toLowerCase().includes(searchA.toLowerCase()) ||
      i.case_id.toLowerCase().includes(searchA.toLowerCase())
  );

  const filteredListB = evidenceList.filter(
    (i) =>
      i.original_filename.toLowerCase().includes(searchB.toLowerCase()) ||
      i.id.toLowerCase().includes(searchB.toLowerCase()) ||
      i.case_id.toLowerCase().includes(searchB.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2.5">
              <GitCompare className="w-6 h-6 text-cyan-400" />
              Cross-Recording Forensic Comparison
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-bold uppercase">
              Phase 6B Active
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Perform side-by-side forensic comparative analysis of container metadata, acoustic dynamics, STFT spectral envelopes, and anomaly timelines.
          </p>
        </div>

        {comparison && (
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleDownloadPdf}
              disabled={isExportingPdf}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
            >
              <FileDown className={`w-3.5 h-3.5 ${isExportingPdf ? 'animate-bounce' : ''}`} />
              <span>{isExportingPdf ? 'Generating PDF...' : 'Export Comparison PDF'}</span>
            </button>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 flex items-start gap-3 text-xs text-rose-300">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Comparison Verification Alert</p>
            <p className="text-[11px] text-rose-200 mt-0.5">{error}</p>
          </div>
          <button
            type="button"
            onClick={() => setError(null)}
            className="text-slate-400 hover:text-slate-200 text-sm font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {/* Dual Column Evidence Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Item A Selector Card */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-cyan-500/20 text-cyan-400 font-bold flex items-center justify-center text-xs">
                A
              </span>
              <h3 className="text-sm font-bold text-slate-100">Primary Evidence Recording</h3>
            </div>
            {selectedItemA && (
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {selectedItemA.format.toUpperCase()}
              </span>
            )}
          </div>

          {/* Search & Select A */}
          <div className="space-y-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-slate-500" />
              <input
                type="text"
                value={searchA}
                onChange={(e) => setSearchA(e.target.value)}
                placeholder="Search recording by filename or ID..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="max-h-44 overflow-y-auto space-y-1.5 p-1 bg-slate-950/60 rounded-xl border border-slate-800/80">
              {isLoadingEvidence ? (
                <div className="py-6 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                  <span>Loading evidence vault items...</span>
                </div>
              ) : filteredListA.length === 0 ? (
                <div className="py-6 text-center text-xs text-slate-500">Zero evidence records matched.</div>
              ) : (
                filteredListA.map((item) => {
                  const isSelected = selectedIdA === item.id;
                  return (
                    <div
                      key={item.id}
                      onClick={() => setSelectedIdA(item.id)}
                      className={`p-2.5 rounded-lg cursor-pointer transition-colors flex items-center justify-between text-xs ${
                        isSelected
                          ? 'bg-cyan-950/40 border border-cyan-500/40 text-cyan-200'
                          : 'bg-slate-900/60 hover:bg-slate-800/60 border border-transparent text-slate-300'
                      }`}
                    >
                      <div className="space-y-0.5 truncate pr-2">
                        <div className="flex items-center gap-1.5 font-semibold text-slate-200 truncate">
                          <FileAudio className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                          <span className="truncate">{item.original_filename}</span>
                        </div>
                        <p className="text-[10px] text-slate-500 font-mono">
                          {item.id} • {formatBytes(item.file_size_bytes)} • Case: {item.case_id}
                        </p>
                      </div>
                      {isSelected && <Check className="w-4 h-4 text-cyan-400 shrink-0" />}
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Selected Item A Preview */}
          {selectedItemA && (
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800/80 space-y-1.5 text-xs font-mono">
              <div className="flex items-center justify-between text-slate-400">
                <span>Selected:</span>
                <span className="text-slate-200 font-sans font-bold truncate">{selectedItemA.original_filename}</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Registered SHA-256:</span>
                <button
                  type="button"
                  onClick={() => copyToClipboard(selectedItemA.sha256_hash, 'a')}
                  className="text-cyan-400 hover:text-cyan-300 inline-flex items-center gap-1"
                >
                  <span className="truncate max-w-[150px]">{selectedItemA.sha256_hash.slice(0, 16)}...</span>
                  {copiedHash === 'a' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Item B Selector Card */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-purple-500/20 text-purple-400 font-bold flex items-center justify-center text-xs">
                B
              </span>
              <h3 className="text-sm font-bold text-slate-100">Secondary Evidence Recording</h3>
            </div>
            {selectedItemB && (
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {selectedItemB.format.toUpperCase()}
              </span>
            )}
          </div>

          {/* Search & Select B */}
          <div className="space-y-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-slate-500" />
              <input
                type="text"
                value={searchB}
                onChange={(e) => setSearchB(e.target.value)}
                placeholder="Search recording by filename or ID..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500"
              />
            </div>

            <div className="max-h-44 overflow-y-auto space-y-1.5 p-1 bg-slate-950/60 rounded-xl border border-slate-800/80">
              {isLoadingEvidence ? (
                <div className="py-6 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-purple-400" />
                  <span>Loading evidence vault items...</span>
                </div>
              ) : filteredListB.length === 0 ? (
                <div className="py-6 text-center text-xs text-slate-500">Zero evidence records matched.</div>
              ) : (
                filteredListB.map((item) => {
                  const isSelected = selectedIdB === item.id;
                  return (
                    <div
                      key={item.id}
                      onClick={() => setSelectedIdB(item.id)}
                      className={`p-2.5 rounded-lg cursor-pointer transition-colors flex items-center justify-between text-xs ${
                        isSelected
                          ? 'bg-purple-950/40 border border-purple-500/40 text-purple-200'
                          : 'bg-slate-900/60 hover:bg-slate-800/60 border border-transparent text-slate-300'
                      }`}
                    >
                      <div className="space-y-0.5 truncate pr-2">
                        <div className="flex items-center gap-1.5 font-semibold text-slate-200 truncate">
                          <FileAudio className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                          <span className="truncate">{item.original_filename}</span>
                        </div>
                        <p className="text-[10px] text-slate-500 font-mono">
                          {item.id} • {formatBytes(item.file_size_bytes)} • Case: {item.case_id}
                        </p>
                      </div>
                      {isSelected && <Check className="w-4 h-4 text-purple-400 shrink-0" />}
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Selected Item B Preview */}
          {selectedItemB && (
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800/80 space-y-1.5 text-xs font-mono">
              <div className="flex items-center justify-between text-slate-400">
                <span>Selected:</span>
                <span className="text-slate-200 font-sans font-bold truncate">{selectedItemB.original_filename}</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Registered SHA-256:</span>
                <button
                  type="button"
                  onClick={() => copyToClipboard(selectedItemB.sha256_hash, 'b')}
                  className="text-purple-400 hover:text-purple-300 inline-flex items-center gap-1"
                >
                  <span className="truncate max-w-[150px]">{selectedItemB.sha256_hash.slice(0, 16)}...</span>
                  {copiedHash === 'b' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Control Bar: Toggles & Compare Button */}
      <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4 text-xs text-slate-300">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={includeAnomaly}
              onChange={(e) => setIncludeAnomaly(e.target.checked)}
              className="rounded bg-slate-950 border-slate-700 text-cyan-500 focus:ring-0"
            />
            <span>Include Phase 4 Anomaly Timeline Comparison</span>
          </label>
        </div>

        <button
          type="button"
          onClick={handleExecuteComparison}
          disabled={isComparing || !selectedIdA || !selectedIdB}
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-linear-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold shadow-md shadow-cyan-600/20 transition-all disabled:opacity-50"
        >
          {isComparing ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Decoding & Comparing Signals...</span>
            </>
          ) : (
            <>
              <GitCompare className="w-4 h-4" />
              <span>Execute Forensic Comparison</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>

      {/* Results View */}
      {comparison && (
        <div className="space-y-6 animate-in fade-in zoom-in-95 duration-150">
          {/* Executive Summary Card */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <span className="text-[11px] font-mono text-cyan-400 font-bold">
                  {comparison.id}
                </span>
                <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2 mt-0.5">
                  <span>Acoustic Label:</span>
                  <span className="text-cyan-400">{comparison.summary.acoustic_similarity_label}</span>
                </h2>
              </div>

              <div className="flex items-center gap-3">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center">
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Similarity Index</div>
                  <div className="text-lg font-bold font-mono text-cyan-400">
                    {(comparison.summary.transparent_similarity_score * 100).toFixed(1)}%
                  </div>
                </div>

                <div className="space-y-1">
                  <StatusBadge
                    status={comparison.summary.byte_match ? 'Exact Byte Duplicate' : 'Distinct SHA-256 Hashes'}
                    variant={comparison.summary.byte_match ? 'healthy' : 'warning'}
                  />
                  <div>
                    <StatusBadge
                      status={comparison.summary.duration_match ? 'Duration Aligned' : 'Disparate Duration'}
                      variant={comparison.summary.duration_match ? 'healthy' : 'warning'}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Explanation & Formula */}
            <div className="space-y-2">
              <p className="text-xs text-slate-300 leading-relaxed">
                {comparison.summary.explanation}
              </p>
              <p className="text-[11px] text-slate-500 italic bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
                {comparison.summary.scoring_formula_explanation}
              </p>
            </div>

            {/* Warnings Callout */}
            {comparison.summary.warnings.length > 0 && (
              <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-500/30 text-xs text-amber-300 space-y-1">
                <div className="flex items-center gap-1.5 font-bold">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  <span>Analytical Observation Warnings</span>
                </div>
                {comparison.summary.warnings.map((w, idx) => (
                  <p key={idx} className="text-[11px] text-amber-200 pl-5">
                    • {w}
                  </p>
                ))}
              </div>
            )}
          </div>

          {/* Side-by-Side Metadata Table */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <FileAudio className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-slate-100">Evidence Custody & Recording Metadata</h3>
              </div>
              <span className="text-xs text-slate-500 font-mono">Format & Dimensions</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3 font-semibold">Parameter</th>
                    <th className="py-2.5 px-3 font-semibold text-cyan-400">Item A (Primary)</th>
                    <th className="py-2.5 px-3 font-semibold text-purple-400">Item B (Secondary)</th>
                    <th className="py-2.5 px-3 font-semibold">Comparison Delta</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  <tr>
                    <td className="py-2 px-3 font-sans text-slate-400">Original Filename</td>
                    <td className="py-2 px-3 text-slate-200">{comparison.metadata_comparison.filename_a}</td>
                    <td className="py-2 px-3 text-slate-200">{comparison.metadata_comparison.filename_b}</td>
                    <td className="py-2 px-3 font-sans">
                      {comparison.metadata_comparison.filename_a === comparison.metadata_comparison.filename_b
                        ? 'Identical'
                        : 'Different filenames'}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-sans text-slate-400">Media Format</td>
                    <td className="py-2 px-3 text-slate-200 uppercase">{comparison.metadata_comparison.format_a}</td>
                    <td className="py-2 px-3 text-slate-200 uppercase">{comparison.metadata_comparison.format_b}</td>
                    <td className="py-2 px-3">
                      <span className={comparison.metadata_comparison.format_match ? 'text-emerald-400' : 'text-amber-400'}>
                        {comparison.metadata_comparison.format_match ? 'Format Match' : 'Different Container'}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-sans text-slate-400">File Size (Bytes)</td>
                    <td className="py-2 px-3 text-slate-200">{comparison.metadata_comparison.file_size_bytes_a.toLocaleString()}</td>
                    <td className="py-2 px-3 text-slate-200">{comparison.metadata_comparison.file_size_bytes_b.toLocaleString()}</td>
                    <td className="py-2 px-3 text-slate-400">
                      Δ = {comparison.metadata_comparison.file_size_diff_bytes.toLocaleString()} bytes
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-sans text-slate-400">Duration (Seconds)</td>
                    <td className="py-2 px-3 text-slate-200">{comparison.metadata_comparison.duration_seconds_a.toFixed(4)}s</td>
                    <td className="py-2 px-3 text-slate-200">{comparison.metadata_comparison.duration_seconds_b.toFixed(4)}s</td>
                    <td className="py-2 px-3">
                      <span className={comparison.metadata_comparison.duration_match ? 'text-emerald-400' : 'text-amber-400'}>
                        Δ = {comparison.metadata_comparison.duration_diff_seconds.toFixed(4)}s
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-sans text-slate-400">Sampling Rate</td>
                    <td className="py-2 px-3 text-slate-200">{comparison.metadata_comparison.sample_rate_hz_a.toLocaleString()} Hz</td>
                    <td className="py-2 px-3 text-slate-200">{comparison.metadata_comparison.sample_rate_hz_b.toLocaleString()} Hz</td>
                    <td className="py-2 px-3">
                      <span className={comparison.metadata_comparison.sample_rate_match ? 'text-emerald-400' : 'text-amber-400'}>
                        {comparison.metadata_comparison.sample_rate_match ? 'Exact Match' : 'Rate Mismatch'}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-sans text-slate-400">Channel Count</td>
                    <td className="py-2 px-3 text-slate-200">{comparison.metadata_comparison.channels_a} channel(s)</td>
                    <td className="py-2 px-3 text-slate-200">{comparison.metadata_comparison.channels_b} channel(s)</td>
                    <td className="py-2 px-3">
                      <span className={comparison.metadata_comparison.channels_match ? 'text-emerald-400' : 'text-amber-400'}>
                        {comparison.metadata_comparison.channels_match ? 'Exact Match' : 'Channel Mismatch'}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-sans text-slate-400">Cryptographic SHA-256</td>
                    <td className="py-2 px-3 text-slate-300 break-all text-[11px]">{comparison.metadata_comparison.sha256_a}</td>
                    <td className="py-2 px-3 text-slate-300 break-all text-[11px]">{comparison.metadata_comparison.sha256_b}</td>
                    <td className="py-2 px-3 font-bold">
                      <span className={comparison.metadata_comparison.sha256_match ? 'text-emerald-400' : 'text-rose-400'}>
                        {comparison.metadata_comparison.sha256_match ? '✓ IDENTICAL BYTES' : '✗ DIFFERENT HASHES'}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Signal Energy & Macro Dynamics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-sm font-bold text-slate-100">Signal Energy & Dynamics</h3>
                </div>
                <span className="text-[11px] font-mono text-slate-500">Amplitude Metrics</span>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">Peak Amplitude (|s|_max):</span>
                  <div className="font-mono text-slate-200 flex items-center gap-2">
                    <span className="text-cyan-400">{comparison.signal_comparison.peak_amplitude_a.toFixed(4)}</span>
                    <span className="text-slate-500">vs</span>
                    <span className="text-purple-400">{comparison.signal_comparison.peak_amplitude_b.toFixed(4)}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">RMS Energy:</span>
                  <div className="font-mono text-slate-200 flex items-center gap-2">
                    <span className="text-cyan-400">{comparison.signal_comparison.rms_energy_a.toFixed(4)}</span>
                    <span className="text-slate-500">vs</span>
                    <span className="text-purple-400">{comparison.signal_comparison.rms_energy_b.toFixed(4)}</span>
                    <span className="text-slate-500 text-[10px]">({comparison.signal_comparison.rms_ratio_db >= 0 ? '+' : ''}{comparison.signal_comparison.rms_ratio_db.toFixed(1)} dB)</span>
                  </div>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">Crest Factor (Dynamic Peakiness):</span>
                  <div className="font-mono text-slate-200 flex items-center gap-2">
                    <span className="text-cyan-400">{comparison.signal_comparison.crest_factor_a.toFixed(2)}</span>
                    <span className="text-slate-500">vs</span>
                    <span className="text-purple-400">{comparison.signal_comparison.crest_factor_b.toFixed(2)}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">Zero Crossing Rate:</span>
                  <div className="font-mono text-slate-200 flex items-center gap-2">
                    <span className="text-cyan-400">{comparison.signal_comparison.zero_crossing_rate_a.toFixed(0)}/s</span>
                    <span className="text-slate-500">vs</span>
                    <span className="text-purple-400">{comparison.signal_comparison.zero_crossing_rate_b.toFixed(0)}/s</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-cyan-950/20 border border-cyan-500/30 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-200">Envelope Pearson Correlation:</div>
                    <div className="text-[10px] text-slate-400">Linear correlation of normalized amplitude envelopes</div>
                  </div>
                  <div className="font-mono text-base font-bold text-cyan-400">
                    r = {comparison.signal_comparison.envelope_correlation.toFixed(4)}
                  </div>
                </div>
              </div>
            </div>

            {/* STFT Spectral Characteristics */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-purple-400" />
                  <h3 className="text-sm font-bold text-slate-100">STFT Spectral Comparison</h3>
                </div>
                <span className="text-[11px] font-mono text-slate-500">
                  Ceiling: {comparison.spectral_comparison.evaluated_frequency_ceiling_hz.toLocaleString()} Hz
                </span>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">Spectral Centroid:</span>
                  <div className="font-mono text-slate-200 flex items-center gap-2">
                    <span className="text-cyan-400">{comparison.spectral_comparison.centroid_hz_a.toFixed(0)} Hz</span>
                    <span className="text-slate-500">vs</span>
                    <span className="text-purple-400">{comparison.spectral_comparison.centroid_hz_b.toFixed(0)} Hz</span>
                    <span className="text-slate-400 text-[10px]">(Δ={comparison.spectral_comparison.centroid_diff_hz.toFixed(0)})</span>
                  </div>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">Spectral Roll-Off (85%):</span>
                  <div className="font-mono text-slate-200 flex items-center gap-2">
                    <span className="text-cyan-400">{comparison.spectral_comparison.rolloff_hz_a.toFixed(0)} Hz</span>
                    <span className="text-slate-500">vs</span>
                    <span className="text-purple-400">{comparison.spectral_comparison.rolloff_hz_b.toFixed(0)} Hz</span>
                    <span className="text-slate-400 text-[10px]">(Δ={comparison.spectral_comparison.rolloff_diff_hz.toFixed(0)})</span>
                  </div>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">Spectral Flatness (Wiener entropy):</span>
                  <div className="font-mono text-slate-200 flex items-center gap-2">
                    <span className="text-cyan-400">{comparison.spectral_comparison.flatness_a.toFixed(4)}</span>
                    <span className="text-slate-500">vs</span>
                    <span className="text-purple-400">{comparison.spectral_comparison.flatness_b.toFixed(4)}</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-purple-950/20 border border-purple-500/30 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-200">Spectral Cosine Similarity:</div>
                    <div className="text-[10px] text-slate-400">Inner product of L2-normalized power spectrum profiles</div>
                  </div>
                  <div className="font-mono text-base font-bold text-purple-400">
                    {comparison.spectral_comparison.spectral_cosine_similarity.toFixed(4)}
                  </div>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 text-[11px] font-mono text-slate-400">
                  <span>Spectral Euclidean Distance:</span>
                  <span className="text-slate-200">{comparison.spectral_comparison.spectral_euclidean_distance.toFixed(4)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Anomaly Timeline Comparison (if included) */}
          {comparison.anomaly_comparison && (
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <SlidersHorizontal className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-sm font-bold text-slate-100">Phase 4 Signal Anomaly Timeline Comparison</h3>
                </div>
                <span className="text-xs text-slate-500 font-mono">Counts & Temporal Density</span>
              </div>

              {/* Anomaly Counts Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-[10px] text-slate-400 uppercase font-bold">Silence Intervals</span>
                  <div className="flex items-center justify-between font-mono text-sm">
                    <span className="text-cyan-400">{comparison.anomaly_comparison.silence_findings_a}</span>
                    <span className="text-slate-500">vs</span>
                    <span className="text-purple-400">{comparison.anomaly_comparison.silence_findings_b}</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-[10px] text-slate-400 uppercase font-bold">Transitions</span>
                  <div className="flex items-center justify-between font-mono text-sm">
                    <span className="text-cyan-400">{comparison.anomaly_comparison.transition_findings_a}</span>
                    <span className="text-slate-500">vs</span>
                    <span className="text-purple-400">{comparison.anomaly_comparison.transition_findings_b}</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-[10px] text-slate-400 uppercase font-bold">Spectral Flux</span>
                  <div className="flex items-center justify-between font-mono text-sm">
                    <span className="text-cyan-400">{comparison.anomaly_comparison.spectral_findings_a}</span>
                    <span className="text-slate-500">vs</span>
                    <span className="text-purple-400">{comparison.anomaly_comparison.spectral_findings_b}</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-[10px] text-slate-400 uppercase font-bold">Total Anomalies</span>
                  <div className="flex items-center justify-between font-mono text-sm">
                    <span className="text-cyan-400 font-bold">{comparison.anomaly_comparison.total_findings_a}</span>
                    <span className="text-slate-500">vs</span>
                    <span className="text-purple-400 font-bold">{comparison.anomaly_comparison.total_findings_b}</span>
                  </div>
                </div>
              </div>

              {/* 10-Bin Relative Timeline Histogram */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-300">Normalized Timeline Distribution (10 Bins, 0% to 100%)</span>
                  <div className="flex items-center gap-3 font-mono text-[11px]">
                    <span className="text-cyan-400 flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-cyan-400" /> Item A
                    </span>
                    <span className="text-purple-400 flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-purple-400" /> Item B
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-10 gap-1.5 h-20 items-end pt-2">
                  {comparison.anomaly_comparison.binned_distribution_a.map((countA, idx) => {
                    const countB = comparison.anomaly_comparison?.binned_distribution_b[idx] || 0;
                    const maxVal = Math.max(
                      1,
                      ...comparison.anomaly_comparison!.binned_distribution_a,
                      ...comparison.anomaly_comparison!.binned_distribution_b
                    );
                    const hA = Math.max(4, Math.round((countA / maxVal) * 56));
                    const hB = Math.max(4, Math.round((countB / maxVal) * 56));

                    return (
                      <div key={idx} className="flex flex-col items-center gap-1 h-full justify-end group">
                        <div className="w-full flex items-end justify-center gap-0.5">
                          <div
                            style={{ height: `${hA}px` }}
                            className="w-1/2 rounded-t bg-cyan-500/70 group-hover:bg-cyan-400 transition-all"
                            title={`Item A Bin ${idx + 1} (${idx * 10}%-${(idx + 1) * 10}%): ${countA} findings`}
                          />
                          <div
                            style={{ height: `${hB}px` }}
                            className="w-1/2 rounded-t bg-purple-500/70 group-hover:bg-purple-400 transition-all"
                            title={`Item B Bin ${idx + 1} (${idx * 10}%-${(idx + 1) * 10}%): ${countB} findings`}
                          />
                        </div>
                        <span className="text-[9px] font-mono text-slate-500">{idx * 10}%</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Legal / ISO 27037 Evidentiary Disclaimer */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400 leading-relaxed space-y-1">
            <div className="flex items-center gap-1.5 text-slate-300 font-semibold">
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
              <span>ISO/IEC 27037 Digital Evidence Comparison Disclaimer</span>
            </div>
            <p className="italic">
              {comparison.disclaimer}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
