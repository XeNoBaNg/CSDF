import React, { useState } from 'react';
import {
  Sliders,
  Play,
  RotateCcw,
  VolumeX,
  Zap,
  Radio,
  ChevronDown,
  ChevronUp,
  Cpu,
  RefreshCw,
} from 'lucide-react';
import type {
  AnalysisRequest,
  SilenceDetectionParams,
  TransitionDetectionParams,
  SpectralDetectionParams,
} from '../../types';

interface DetectorControlPanelProps {
  onRunAnalysis: (request: AnalysisRequest) => void;
  isLoading: boolean;
}

export const DetectorControlPanel: React.FC<DetectorControlPanelProps> = ({
  onRunAnalysis,
  isLoading,
}) => {
  const [enableSilence, setEnableSilence] = useState(true);
  const [enableTransitions, setEnableTransitions] = useState(true);
  const [enableSpectral, setEnableSpectral] = useState(true);

  const [showAdvanced, setShowAdvanced] = useState(false);

  // Detector custom parameters
  const [silenceThreshold, setSilenceThreshold] = useState(0.01);
  const [minSilenceDuration, setMinSilenceDuration] = useState(0.25);

  const [transitionThreshold, setTransitionThreshold] = useState(0.35);
  const [transitionSeparation, setTransitionSeparation] = useState(0.05);

  const [spectralThreshold, setSpectralThreshold] = useState(0.40);
  const [spectralNfft, setSpectralNfft] = useState(1024);

  const handleResetDefaults = () => {
    setEnableSilence(true);
    setEnableTransitions(true);
    setEnableSpectral(true);
    setSilenceThreshold(0.01);
    setMinSilenceDuration(0.25);
    setTransitionThreshold(0.35);
    setTransitionSeparation(0.05);
    setSpectralThreshold(0.40);
    setSpectralNfft(1024);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const silenceParams: SilenceDetectionParams = {
      rms_threshold: silenceThreshold,
      min_silence_duration_seconds: minSilenceDuration,
    };
    const transitionParams: TransitionDetectionParams = {
      threshold: transitionThreshold,
      min_separation_seconds: transitionSeparation,
    };
    const spectralParams: SpectralDetectionParams = {
      threshold: spectralThreshold,
      n_fft: spectralNfft,
    };

    onRunAnalysis({
      enable_silence: enableSilence,
      enable_transitions: enableTransitions,
      enable_spectral_flux: enableSpectral,
      silence_params: silenceParams,
      transition_params: transitionParams,
      spectral_params: spectralParams,
    });
  };

  return (
    <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-200">
              Explainable Forensic Signal Anomaly Detectors
            </h3>
            <p className="text-[11px] text-slate-400">
              Configure explainable signal processing methods (zero AI black-box classification)
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-xs text-slate-400 hover:text-slate-200 inline-flex items-center gap-1 transition-colors self-start sm:self-auto"
        >
          <Sliders className="w-3.5 h-3.5 text-cyan-400" />
          <span>{showAdvanced ? 'Hide Threshold Settings' : 'Configure Thresholds'}</span>
          {showAdvanced ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Detector Activation Checkboxes */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Silence Detector Toggle */}
          <label
            className={`p-3.5 rounded-xl border flex items-start gap-3 cursor-pointer transition-all ${
              enableSilence
                ? 'bg-cyan-950/20 border-cyan-500/40 text-slate-200'
                : 'bg-slate-950/60 border-slate-800/80 text-slate-400'
            }`}
          >
            <input
              type="checkbox"
              checked={enableSilence}
              onChange={(e) => setEnableSilence(e.target.checked)}
              className="mt-0.5 rounded border-slate-700 text-cyan-500 focus:ring-0 focus:outline-none accent-cyan-500"
            />
            <div className="space-y-1">
              <span className="text-xs font-bold flex items-center gap-1.5 text-cyan-300">
                <VolumeX className="w-3.5 h-3.5 text-cyan-400" />
                Silence & Low-Energy
              </span>
              <p className="text-[11px] text-slate-400 leading-snug">
                Detects contiguous zero-energy or low-RMS windows exceeding duration threshold.
              </p>
            </div>
          </label>

          {/* Abrupt Transition Detector Toggle */}
          <label
            className={`p-3.5 rounded-xl border flex items-start gap-3 cursor-pointer transition-all ${
              enableTransitions
                ? 'bg-rose-950/20 border-rose-500/40 text-slate-200'
                : 'bg-slate-950/60 border-slate-800/80 text-slate-400'
            }`}
          >
            <input
              type="checkbox"
              checked={enableTransitions}
              onChange={(e) => setEnableTransitions(e.target.checked)}
              className="mt-0.5 rounded border-slate-700 text-rose-500 focus:ring-0 focus:outline-none accent-rose-500"
            />
            <div className="space-y-1">
              <span className="text-xs font-bold flex items-center gap-1.5 text-rose-300">
                <Zap className="w-3.5 h-3.5 text-rose-400" />
                Amplitude Discontinuities
              </span>
              <p className="text-[11px] text-slate-400 leading-snug">
                Measures adjacent-sample amplitude steps (|x[n] - x[n-1]|) for splicing signatures.
              </p>
            </div>
          </label>

          {/* Spectral Flux Detector Toggle */}
          <label
            className={`p-3.5 rounded-xl border flex items-start gap-3 cursor-pointer transition-all ${
              enableSpectral
                ? 'bg-purple-950/20 border-purple-500/40 text-slate-200'
                : 'bg-slate-950/60 border-slate-800/80 text-slate-400'
            }`}
          >
            <input
              type="checkbox"
              checked={enableSpectral}
              onChange={(e) => setEnableSpectral(e.target.checked)}
              className="mt-0.5 rounded border-slate-700 text-purple-500 focus:ring-0 focus:outline-none accent-purple-500"
            />
            <div className="space-y-1">
              <span className="text-xs font-bold flex items-center gap-1.5 text-purple-300">
                <Radio className="w-3.5 h-3.5 text-purple-400" />
                Spectral Inconsistency
              </span>
              <p className="text-[11px] text-slate-400 leading-snug">
                Calculates normalized STFT spectral flux distance between consecutive time frames.
              </p>
            </div>
          </label>
        </div>

        {/* Collapsible Advanced Parameters */}
        {showAdvanced && (
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-4">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Mathematical Parameters & Decision Thresholds
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              {/* Silence parameters */}
              <div className="space-y-2 p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[11px] font-bold text-cyan-400 block">Silence Settings</span>
                <div className="space-y-1">
                  <label className="text-slate-400 text-[10px] block">RMS Energy Threshold (0.001 - 0.1)</label>
                  <input
                    type="number"
                    step="0.005"
                    min="0.001"
                    max="0.2"
                    value={silenceThreshold}
                    onChange={(e) => setSilenceThreshold(parseFloat(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 font-mono text-xs focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-slate-400 text-[10px] block">Min Silence Duration (seconds)</label>
                  <input
                    type="number"
                    step="0.05"
                    min="0.05"
                    max="5.0"
                    value={minSilenceDuration}
                    onChange={(e) => setMinSilenceDuration(parseFloat(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 font-mono text-xs focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              {/* Transition parameters */}
              <div className="space-y-2 p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[11px] font-bold text-rose-400 block">Discontinuity Settings</span>
                <div className="space-y-1">
                  <label className="text-slate-400 text-[10px] block">Delta Step Threshold (0.1 - 1.0)</label>
                  <input
                    type="number"
                    step="0.05"
                    min="0.1"
                    max="1.2"
                    value={transitionThreshold}
                    onChange={(e) => setTransitionThreshold(parseFloat(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 font-mono text-xs focus:outline-none focus:border-rose-500"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-slate-400 text-[10px] block">Min Separation (seconds)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    max="1.0"
                    value={transitionSeparation}
                    onChange={(e) => setTransitionSeparation(parseFloat(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 font-mono text-xs focus:outline-none focus:border-rose-500"
                  />
                </div>
              </div>

              {/* Spectral Flux parameters */}
              <div className="space-y-2 p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[11px] font-bold text-purple-400 block">Spectral Flux Settings</span>
                <div className="space-y-1">
                  <label className="text-slate-400 text-[10px] block">Normalized Flux Threshold (0.1 - 1.0)</label>
                  <input
                    type="number"
                    step="0.05"
                    min="0.1"
                    max="1.2"
                    value={spectralThreshold}
                    onChange={(e) => setSpectralThreshold(parseFloat(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 font-mono text-xs focus:outline-none focus:border-purple-500"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-slate-400 text-[10px] block">STFT N_fft Window Size</label>
                  <select
                    value={spectralNfft}
                    onChange={(e) => setSpectralNfft(parseInt(e.target.value, 10))}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 font-mono text-xs focus:outline-none focus:border-purple-500"
                  >
                    <option value={512}>512 samples</option>
                    <option value={1024}>1024 samples</option>
                    <option value={2048}>2048 samples</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={handleResetDefaults}
                className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset Default Thresholds</span>
              </button>
            </div>
          </div>
        )}

        {/* Action Button Row */}
        <div className="flex items-center justify-between pt-2">
          <p className="text-[11px] text-slate-500 italic">
            Findings will be localized with start and end timestamps and plotted as visual overlays.
          </p>

          <button
            type="submit"
            disabled={isLoading || (!enableSilence && !enableTransitions && !enableSpectral)}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-cyan-500/20"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Running Signal Processing...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 ml-0.5" />
                <span>Run Forensic Signal Analysis</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
