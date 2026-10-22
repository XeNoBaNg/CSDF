import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  AudioLines,
  AlertTriangle,
  RefreshCw,
  Activity,
  Layers,
  ShieldCheck,
  Info,
  Cpu,
  FileDown,
  GitCompare,
} from 'lucide-react';
import {
  getAudioMetadata,
  getAudioWaveform,
  getAudioSpectrogram,
  getAudioSpectrum,
  getAudioPlaybackUrl,
} from '../api/inspection';
import { analyzeEvidence } from '../api/analysis';
import { downloadEvidenceReport } from '../api/reports';
import { StatusBadge } from '../components/common/StatusBadge';
import { AudioPlayer } from '../components/audio/AudioPlayer';
import { WaveformViewer } from '../components/audio/WaveformViewer';
import { SpectrogramViewer } from '../components/audio/SpectrogramViewer';
import { FrequencySpectrumViewer } from '../components/audio/FrequencySpectrumViewer';
import { MetadataInspector } from '../components/audio/MetadataInspector';
import { DetectorControlPanel } from '../components/analysis/DetectorControlPanel';
import { FindingsList } from '../components/analysis/FindingsList';
import type {
  AudioMetadataResponse,
  WaveformResponse,
  SpectrogramResponse,
  SpectrumResponse,
  AnalysisResponse,
  AnalysisRequest,
} from '../types';

export const AudioInspectionPage: React.FC = () => {
  const { evidenceId } = useParams<{ evidenceId: string }>();
  const navigate = useNavigate();

  // Active view tab: 'visualizers' | 'findings' | 'metadata' | 'methodology'
  const [activeTab, setActiveTab] = useState<'visualizers' | 'findings' | 'metadata' | 'methodology'>('visualizers');

  // Inspection Data States
  const [metadata, setMetadata] = useState<AudioMetadataResponse | null>(null);
  const [waveform, setWaveform] = useState<WaveformResponse | null>(null);
  const [spectrogram, setSpectrogram] = useState<SpectrogramResponse | null>(null);
  const [spectrum, setSpectrum] = useState<SpectrumResponse | null>(null);

  // Signal Analysis & Findings States (Phase 4)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null);

  // Report Export State (Phase 6A)
  const [isDownloadingReport, setIsDownloadingReport] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  // Loading & Error States
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isIntegrityTampered, setIsIntegrityTampered] = useState(false);

  // Playback & Cross-Component Seeking Sync
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [seekTimestamp, setSeekTimestamp] = useState<number | null>(null);

  // Configuration options
  const [pointBudget, setPointBudget] = useState<number>(1000);
  const [nFft, setNFft] = useState<number>(1024);
  const [hopLength, setHopLength] = useState<number>(256);
  const [spectrumBins, setSpectrumBins] = useState<number>(512);

  const [waveformLoading, setWaveformLoading] = useState(false);
  const [spectrogramLoading, setSpectrogramLoading] = useState(false);
  const [spectrumLoading, setSpectrumLoading] = useState(false);

  // Execute Signal Analysis function
  const handleExecuteAnalysis = useCallback(async (request?: AnalysisRequest) => {
    if (!evidenceId) return;
    setAnalysisLoading(true);
    setAnalysisError(null);

    try {
      const result = await analyzeEvidence(evidenceId, request);
      setAnalysisResult(result);
    } catch (err: unknown) {
      console.warn('Analysis execution error:', err);
      const apiErr = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error;
      setAnalysisError(apiErr?.message || 'Failed to execute forensic signal analysis.');
    } finally {
      setAnalysisLoading(false);
    }
  }, [evidenceId]);

  // Initial Full Load
  const fetchAllInspectionData = useCallback(async () => {
    if (!evidenceId) return;
    setLoading(true);
    setError(null);
    setIsIntegrityTampered(false);

    try {
      // Step 1: Fetch metadata (which performs pre-check SHA-256 verification)
      const metaRes = await getAudioMetadata(evidenceId);
      setMetadata(metaRes);

      // Step 2: Fetch signal visualizations concurrently
      const [waveRes, specRes, fftRes] = await Promise.all([
        getAudioWaveform(evidenceId, { point_budget: pointBudget }),
        getAudioSpectrogram(evidenceId, { n_fft: nFft, hop_length: hopLength }),
        getAudioSpectrum(evidenceId, { num_bins: spectrumBins }),
      ]);

      setWaveform(waveRes);
      setSpectrogram(specRes);
      setSpectrum(fftRes);

      // Step 3: Automatically execute baseline signal analysis with defaults
      handleExecuteAnalysis();
    } catch (err: unknown) {
      console.error('Failed to load audio inspection data:', err);
      const apiErr = (err as { response?: { data?: { error?: { code?: string; message?: string } } } })
        ?.response?.data?.error;

      if (apiErr?.code === 'INTEGRITY_MISMATCH') {
        setIsIntegrityTampered(true);
        setError(
          apiErr.message ||
            'Evidence file integrity verification failed! Stored file does not match recorded SHA-256 digest.'
        );
      } else {
        setError(apiErr?.message || 'Failed to inspect digital audio evidence.');
      }
    } finally {
      setLoading(false);
    }
  }, [evidenceId, pointBudget, nFft, hopLength, spectrumBins, handleExecuteAnalysis]);

  useEffect(() => {
    fetchAllInspectionData();
  }, [fetchAllInspectionData]);

  // Handle Point Budget update
  const handleBudgetChange = async (newBudget: number) => {
    if (!evidenceId) return;
    setPointBudget(newBudget);
    setWaveformLoading(true);
    try {
      const updated = await getAudioWaveform(evidenceId, { point_budget: newBudget });
      setWaveform(updated);
    } catch (err) {
      console.warn('Failed to update waveform budget:', err);
    } finally {
      setWaveformLoading(false);
    }
  };

  // Handle STFT params update
  const handleSpectrogramParamsChange = async (newNfft: number, newHop: number) => {
    if (!evidenceId) return;
    setNFft(newNfft);
    setHopLength(newHop);
    setSpectrogramLoading(true);
    try {
      const updated = await getAudioSpectrogram(evidenceId, {
        n_fft: newNfft,
        hop_length: newHop,
      });
      setSpectrogram(updated);
    } catch (err) {
      console.warn('Failed to update spectrogram params:', err);
    } finally {
      setSpectrogramLoading(false);
    }
  };

  // Handle Spectrum Bins update
  const handleSpectrumBinsChange = async (newBins: number) => {
    if (!evidenceId) return;
    setSpectrumBins(newBins);
    setSpectrumLoading(true);
    try {
      const updated = await getAudioSpectrum(evidenceId, { num_bins: newBins });
      setSpectrum(updated);
    } catch (err) {
      console.warn('Failed to update spectrum bins:', err);
    } finally {
      setSpectrumLoading(false);
    }
  };

  // Seeking callback from Waveform, Spectrogram, or Findings
  const handleCanvasSeek = (timeSeconds: number) => {
    setCurrentTime(timeSeconds);
    setSeekTimestamp(timeSeconds);
  };

  const handleSelectFinding = (findingId: string) => {
    setSelectedFindingId(findingId);
    const found = analysisResult?.findings.find((f) => f.id === findingId);
    if (found) {
      handleCanvasSeek(found.event_time ?? found.start_time);
    }
  };

  const handleDownloadReport = async () => {
    if (!evidenceId) return;
    setIsDownloadingReport(true);
    setReportError(null);
    try {
      await downloadEvidenceReport(evidenceId, {
        include_visualizations: true,
        include_audit: true,
        run_analysis: true,
      });
    } catch (err: unknown) {
      console.error('Failed to generate forensic report:', err);
      const msg =
        (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data
          ?.error?.message || 'Failed to compile or download forensic PDF report.';
      setReportError(msg);
    } finally {
      setIsDownloadingReport(false);
    }
  };

  if (!evidenceId) {
    return (
      <div className="max-w-7xl mx-auto p-8 text-center text-slate-400">
        Missing evidence identifier in URL path.
      </div>
    );
  }

  const totalFindingsCount = analysisResult?.summary.total_findings || 0;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Top Header & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="p-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 hover:bg-slate-800 transition-colors"
            title="Go back"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <AudioLines className="w-5 h-5 text-cyan-400" />
                <span>Forensic Audio Inspection Workspace</span>
              </h2>
              {metadata && (
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 uppercase font-bold">
                  {metadata.encoded_properties.format}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Evidence ID: <span className="font-mono text-slate-300">{evidenceId}</span>
              {metadata && ` • ${metadata.original_filename}`}
            </p>
          </div>
        </div>

        {/* Integrity Badge, Export Action & Refresh */}
        <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
          {metadata && (
            <StatusBadge
              status={metadata.integrity_verified ? 'SHA-256 Pristine' : 'Unverified'}
              variant={metadata.integrity_verified ? 'healthy' : 'warning'}
            />
          )}

          <button
            type="button"
            onClick={() => navigate(`/compare?evidenceA=${encodeURIComponent(evidenceId || '')}`)}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold shadow-xs transition-colors"
            title="Compare this recording against another evidence item"
          >
            <GitCompare className="w-4 h-4 text-cyan-400" />
            <span>Cross-Compare</span>
          </button>

          <button
            type="button"
            onClick={handleDownloadReport}
            disabled={isDownloadingReport || isIntegrityTampered || loading}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-xs disabled:opacity-50 transition-colors"
            title="Download forensic PDF examination report"
          >
            {isDownloadingReport ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Generating Report...</span>
              </>
            ) : (
              <>
                <FileDown className="w-4 h-4" />
                <span>Export PDF Report</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={fetchAllInspectionData}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 hover:bg-slate-800 transition-colors"
            title="Refresh inspection"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Report Generation Error Alert */}
      {reportError && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{reportError}</span>
          </div>
          <button
            type="button"
            onClick={() => setReportError(null)}
            className="text-xs text-slate-400 hover:text-slate-200"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Critical Integrity Tampering Alert */}
      {isIntegrityTampered && (
        <div className="p-5 rounded-2xl bg-rose-950/30 border border-rose-500/50 text-rose-200 space-y-3 shadow-lg">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-rose-400 shrink-0" />
            <div>
              <h3 className="text-sm font-bold text-rose-300">
                CRITICAL FORENSIC ALERT: Evidence Integrity Mismatch
              </h3>
              <p className="text-xs text-rose-300/80 mt-0.5">
                The stored audio file on disk has been altered or corrupted since registration.
              </p>
            </div>
          </div>
          <p className="text-xs text-rose-200/90 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-rose-500/20 font-mono">
            {error}
          </p>
          <p className="text-[11px] text-slate-400 italic">
            In accordance with digital forensic standards (ISO/IEC 27037), inspection and decoding have been aborted to prevent contaminated analysis.
          </p>
        </div>
      )}

      {/* General Non-Tampering Error */}
      {error && !isIntegrityTampered && (
        <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/30 text-amber-300 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={fetchAllInspectionData}
            className="px-3 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 text-xs font-semibold"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="p-16 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col items-center justify-center gap-3 text-slate-400">
          <RefreshCw className="w-7 h-7 text-cyan-400 animate-spin" />
          <span className="text-xs font-mono">
            Verifying SHA-256 & Decoding Audio Representation...
          </span>
        </div>
      )}

      {/* Main Workspace Body */}
      {!loading && !isIntegrityTampered && metadata && (
        <div className="space-y-6">
          {/* Master Playback Console */}
          <AudioPlayer
            src={getAudioPlaybackUrl(evidenceId)}
            duration={metadata.decoded_properties.duration_seconds}
            currentTime={currentTime}
            externalSeekTime={seekTimestamp}
            onTimeUpdate={(t) => setCurrentTime(t)}
          />

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800 gap-2 overflow-x-auto">
            <button
              type="button"
              onClick={() => setActiveTab('visualizers')}
              className={`inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors shrink-0 ${
                activeTab === 'visualizers'
                  ? 'border-cyan-400 text-cyan-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Signal Visualizations & Overlays</span>
              {totalFindingsCount > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  {totalFindingsCount}
                </span>
              )}
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('findings')}
              className={`inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors shrink-0 ${
                activeTab === 'findings'
                  ? 'border-cyan-400 text-cyan-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>Anomaly Detectors & Findings</span>
              {totalFindingsCount > 0 ? (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  {totalFindingsCount}
                </span>
              ) : (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-slate-800 text-slate-400">
                  0
                </span>
              )}
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('metadata')}
              className={`inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors shrink-0 ${
                activeTab === 'metadata'
                  ? 'border-cyan-400 text-cyan-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Properties & Embedded Tags</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('methodology')}
              className={`inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors shrink-0 ${
                activeTab === 'methodology'
                  ? 'border-cyan-400 text-cyan-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Info className="w-3.5 h-3.5" />
              <span>Methodology & Disclaimers</span>
            </button>
          </div>

          {/* Tab 1: Signal Visualizations & Overlays */}
          {activeTab === 'visualizers' && (
            <div className="space-y-6">
              {/* Findings Summary Indicator Bar */}
              {analysisResult && (
                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1.5 text-slate-300 font-semibold">
                      <Cpu className="w-4 h-4 text-cyan-400" />
                      <span>Detector Overlays Active:</span>
                    </span>
                    <span className="font-mono text-cyan-400 font-bold">
                      {totalFindingsCount} anomaly interval(s)
                    </span>
                    <span className="text-slate-600 hidden sm:inline">•</span>
                    <span className="text-slate-400 text-[11px] hidden sm:inline">
                      Executed in {analysisResult.summary.execution_time_ms} ms
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    {/* Color Legend */}
                    <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
                      <span className="flex items-center gap-1">
                        <span className="w-2.5 h-2.5 rounded-sm bg-cyan-500/50 border border-cyan-400 inline-block" />
                        <span>Silence</span>
                      </span>
                      <span className="flex items-center gap-1">
                        <span className="w-2.5 h-2.5 rounded-sm bg-rose-500/50 border border-rose-400 inline-block" />
                        <span>Discontinuity</span>
                      </span>
                      <span className="flex items-center gap-1">
                        <span className="w-2.5 h-2.5 rounded-sm bg-purple-500/50 border border-purple-400 inline-block" />
                        <span>Spectral Flux</span>
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() => setActiveTab('findings')}
                      className="px-2.5 py-1 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 text-xs font-semibold transition-colors shrink-0"
                    >
                      View Findings List →
                    </button>
                  </div>
                </div>
              )}

              {/* Waveform Envelope with Findings Overlay */}
              {waveform && (
                <WaveformViewer
                  waveform={waveform}
                  currentTime={currentTime}
                  onSeek={handleCanvasSeek}
                  onBudgetChange={handleBudgetChange}
                  isLoading={waveformLoading}
                  findings={analysisResult?.findings || []}
                  selectedFindingId={selectedFindingId}
                />
              )}

              {/* Time-Frequency STFT Spectrogram with Findings Overlay */}
              {spectrogram && (
                <SpectrogramViewer
                  spectrogram={spectrogram}
                  currentTime={currentTime}
                  onSeek={handleCanvasSeek}
                  onParamsChange={handleSpectrogramParamsChange}
                  isLoading={spectrogramLoading}
                  findings={analysisResult?.findings || []}
                  selectedFindingId={selectedFindingId}
                />
              )}

              {/* FFT Frequency Power Spectrum */}
              {spectrum && (
                <FrequencySpectrumViewer
                  spectrum={spectrum}
                  onNumBinsChange={handleSpectrumBinsChange}
                  isLoading={spectrumLoading}
                />
              )}
            </div>
          )}

          {/* Tab 2: Anomaly Detectors & Findings (Phase 4) */}
          {activeTab === 'findings' && (
            <div className="space-y-6">
              {/* Detector Control & Configuration Panel */}
              <DetectorControlPanel
                onRunAnalysis={handleExecuteAnalysis}
                isLoading={analysisLoading}
              />

              {analysisError && (
                <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>{analysisError}</span>
                </div>
              )}

              {/* Structured Findings List */}
              {analysisResult && (
                <FindingsList
                  findings={analysisResult.findings}
                  onSeekToTimestamp={handleCanvasSeek}
                  selectedFindingId={selectedFindingId}
                  onSelectFinding={handleSelectFinding}
                />
              )}
            </div>
          )}

          {/* Tab 3: Properties & Embedded Tags */}
          {activeTab === 'metadata' && <MetadataInspector metadata={metadata} />}

          {/* Tab 4: Forensic Methodology & Disclaimers */}
          {activeTab === 'methodology' && (
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-5 text-xs text-slate-300 leading-relaxed shadow-sm">
              <div className="flex items-center gap-2.5 border-b border-slate-800 pb-3">
                <ShieldCheck className="w-5 h-5 text-cyan-400" />
                <h3 className="text-sm font-bold text-slate-100">
                  Explainable Signal Anomaly Detection Methodology & Guidelines
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <h4 className="font-bold text-cyan-400">1. Silence & Low-Energy Intervals</h4>
                  <p className="text-[11px] text-slate-400">
                    Calculates sliding-window RMS energy: <code className="text-cyan-300 font-mono">RMS = sqrt(mean(x²))</code>.
                    Identifies contiguous segments below threshold. In natural recordings, ambient room tone is virtually always present;
                    true digital zero intervals (<code className="text-cyan-300 font-mono">&lt; 1e-6</code>) often indicate artificial muting or edited gaps.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <h4 className="font-bold text-rose-400">2. Abrupt Amplitude Discontinuities</h4>
                  <p className="text-[11px] text-slate-400">
                    Calculates instantaneous adjacent-sample amplitude difference: <code className="text-rose-300 font-mono">|x[n] - x[n-1]|</code>.
                    Detects sharp non-sinusoidal steps that exceed continuous speech gradients. Non-maximum suppression prevents duplicate warnings around sharp onset bursts.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <h4 className="font-bold text-purple-400">3. STFT Spectral Flux</h4>
                  <p className="text-[11px] text-slate-400">
                    Calculates normalized Euclidean distance between adjacent STFT magnitude vectors: <code className="text-purple-300 font-mono">||X_norm(t) - X_norm(t-1)||</code>.
                    Highlights moments where the acoustic frequency profile changes abruptly, flagging spliced transitions between different acoustic environments.
                  </p>
                </div>
              </div>

              {/* Crucial Academic Forensic Disclaimer */}
              <div className="p-4 rounded-xl bg-slate-950 border border-amber-500/30 text-amber-300/90 space-y-2">
                <h4 className="font-bold text-amber-300 flex items-center gap-2 text-xs">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  Forensic Limitation & Evidence Authentication Notice
                </h4>
                <p className="text-[11px] leading-relaxed text-slate-300">
                  Signal anomalies, low-energy intervals, amplitude steps, and spectral flux peaks are <strong>investigative indicators for manual examination</strong>,
                  NOT definitive proof of tampering, manipulation, or digital synthesis. Natural speech transitions (e.g., plosive consonants /p/, /t/, /k/), microphone rustle,
                  acoustic reverberation changes, and lossy compression artifacts routinely trigger similar mathematical indicators.
                </p>
                <p className="text-[11px] text-slate-400 italic">
                  Only cryptographic hash comparison can verify byte-for-byte evidence integrity. Signal anomaly analysis provides explainable observations to direct manual investigative scrutiny.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
