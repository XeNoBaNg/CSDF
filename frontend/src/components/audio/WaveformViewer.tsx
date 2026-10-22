import React, { useRef, useEffect, useState, useCallback } from 'react';
import {
  Activity,
  Sliders,
  Clock,
  Layers,
} from 'lucide-react';
import type { WaveformResponse, ForensicFinding } from '../../types';

interface WaveformViewerProps {
  waveform: WaveformResponse;
  currentTime?: number;
  onSeek?: (timeSeconds: number) => void;
  onBudgetChange?: (newBudget: number) => void;
  isLoading?: boolean;
  findings?: ForensicFinding[];
  selectedFindingId?: string | null;
}

export const WaveformViewer: React.FC<WaveformViewerProps> = ({
  waveform,
  currentTime = 0,
  onSeek,
  onBudgetChange,
  isLoading = false,
  findings = [],
  selectedFindingId = null,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [hoverInfo, setHoverInfo] = useState<{
    time: number;
    channelMins: number[];
    channelMaxs: number[];
    x: number;
  } | null>(null);

  const duration = waveform.duration_seconds || 1;
  const channels = waveform.channels || [];
  const numChannels = channels.length;

  // Render waveform onto canvas
  const renderCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !containerRef.current) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = containerRef.current.getBoundingClientRect();
    const width = Math.floor(rect.width);
    const height = Math.max(180, numChannels * 100);

    // Set canvas dimensions respecting DPR
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    ctx.save();
    ctx.scale(dpr, dpr);

    // Background
    ctx.fillStyle = '#030712'; // slate-950
    ctx.fillRect(0, 0, width, height);

    if (numChannels === 0 || !channels[0].min_amplitudes.length) {
      ctx.fillStyle = '#64748b';
      ctx.font = '12px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('No waveform data available', width / 2, height / 2);
      ctx.restore();
      return;
    }

    const channelHeight = height / numChannels;
    const pointsCount = channels[0].min_amplitudes.length;

    // Draw each channel
    channels.forEach((ch, chIdx) => {
      const topY = chIdx * channelHeight;
      const midY = topY + channelHeight / 2;
      const halfH = (channelHeight / 2) * 0.88;

      // Channel boundary & grid
      ctx.strokeStyle = '#1e293b'; // slate-800
      ctx.lineWidth = 1;
      if (chIdx > 0) {
        ctx.beginPath();
        ctx.moveTo(0, topY);
        ctx.lineTo(width, topY);
        ctx.stroke();
      }

      // Zero-amplitude center baseline
      ctx.strokeStyle = '#334155'; // slate-700
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(0, midY);
      ctx.lineTo(width, midY);
      ctx.stroke();
      ctx.setLineDash([]);

      // Amplitude limits (+1.0, -1.0)
      ctx.strokeStyle = '#1e293b';
      ctx.beginPath();
      ctx.moveTo(0, midY - halfH);
      ctx.lineTo(width, midY - halfH);
      ctx.moveTo(0, midY + halfH);
      ctx.lineTo(width, midY + halfH);
      ctx.stroke();

      // Channel Label
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px monospace';
      ctx.textAlign = 'left';
      ctx.fillText(
        numChannels === 1
          ? 'MONO'
          : chIdx === 0
          ? 'CH 1 (LEFT)'
          : `CH ${chIdx + 1} (RIGHT)`,
        10,
        topY + 14
      );

      // Amplitude labels
      ctx.fillStyle = '#475569';
      ctx.font = '9px monospace';
      ctx.textAlign = 'right';
      ctx.fillText('+1.0', width - 8, midY - halfH + 8);
      ctx.fillText(' 0.0', width - 8, midY - 2);
      ctx.fillText('-1.0', width - 8, midY + halfH);

      // Draw min/max envelope polygons
      const mins = ch.min_amplitudes;
      const maxs = ch.max_amplitudes;

      // Gradient for waveform bars
      const grad = ctx.createLinearGradient(0, midY - halfH, 0, midY + halfH);
      grad.addColorStop(0, '#06b6d4'); // cyan-500
      grad.addColorStop(0.5, '#22d3ee'); // cyan-400
      grad.addColorStop(1, '#0891b2'); // cyan-600

      ctx.fillStyle = grad;
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 1;

      // Draw envelope bars for each aggregated bucket
      for (let i = 0; i < pointsCount; i++) {
        const x = (i / (pointsCount - 1 || 1)) * width;
        const minVal = Math.max(-1.0, Math.min(1.0, mins[i] ?? 0));
        const maxVal = Math.max(-1.0, Math.min(1.0, maxs[i] ?? 0));

        const yTop = midY - maxVal * halfH;
        const yBottom = midY - minVal * halfH;
        const barHeight = Math.max(1, yBottom - yTop);

        ctx.fillRect(x - 0.75, yTop, 1.5, barHeight);
      }
    });

    // Draw findings overlay regions
    if (findings && findings.length > 0) {
      findings.forEach((f) => {
        const isSelected = selectedFindingId === f.id;
        const xStart = Math.min(width, Math.max(0, (f.start_time / duration) * width));
        const xEnd = Math.min(width, Math.max(0, (f.end_time / duration) * width));
        const regionWidth = Math.max(2, xEnd - xStart);

        if (f.category === 'silence') {
          ctx.fillStyle = isSelected ? 'rgba(6, 182, 212, 0.35)' : 'rgba(6, 182, 212, 0.16)';
          ctx.fillRect(xStart, 0, regionWidth, height);
          ctx.strokeStyle = isSelected ? '#22d3ee' : 'rgba(6, 182, 212, 0.5)';
          ctx.lineWidth = isSelected ? 2 : 1;
          ctx.strokeRect(xStart, 0, regionWidth, height);
        } else if (f.category === 'transition') {
          const eventX = f.event_time != null ? Math.min(width, Math.max(0, (f.event_time / duration) * width)) : (xStart + xEnd) / 2;
          ctx.fillStyle = isSelected ? 'rgba(244, 63, 94, 0.35)' : 'rgba(244, 63, 94, 0.18)';
          ctx.fillRect(xStart, 0, regionWidth, height);
          // Marker line at exact event time
          ctx.strokeStyle = isSelected ? '#f43f5e' : 'rgba(244, 63, 94, 0.85)';
          ctx.lineWidth = isSelected ? 2.5 : 1.5;
          ctx.beginPath();
          ctx.moveTo(eventX, 0);
          ctx.lineTo(eventX, height);
          ctx.stroke();
        } else if (f.category === 'spectral') {
          ctx.fillStyle = isSelected ? 'rgba(168, 85, 247, 0.35)' : 'rgba(168, 85, 247, 0.18)';
          ctx.fillRect(xStart, 0, regionWidth, height);
          ctx.strokeStyle = isSelected ? '#c084fc' : 'rgba(168, 85, 247, 0.5)';
          ctx.lineWidth = isSelected ? 2 : 1;
          ctx.strokeRect(xStart, 0, regionWidth, height);
        }
      });
    }

    // Draw playhead cursor
    if (Number.isFinite(currentTime) && currentTime >= 0 && duration > 0) {
      const playheadX = Math.min(width, Math.max(0, (currentTime / duration) * width));

      ctx.strokeStyle = '#f59e0b'; // amber-500
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(playheadX, 0);
      ctx.lineTo(playheadX, height);
      ctx.stroke();

      // Playhead handle
      ctx.fillStyle = '#f59e0b';
      ctx.beginPath();
      ctx.arc(playheadX, 6, 5, 0, Math.PI * 2);
      ctx.fill();
    }

    // Draw hover timestamp line
    if (hoverInfo) {
      ctx.strokeStyle = '#38bdf8'; // sky-400
      ctx.lineWidth = 1;
      ctx.setLineDash([2, 2]);
      ctx.beginPath();
      ctx.moveTo(hoverInfo.x, 0);
      ctx.lineTo(hoverInfo.x, height);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    ctx.restore();
  }, [channels, numChannels, duration, currentTime, hoverInfo, findings, selectedFindingId]);

  // Redraw on resize or update
  useEffect(() => {
    renderCanvas();
    const handleResize = () => renderCanvas();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [renderCanvas]);

  // Handle canvas mouse interaction
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || duration <= 0) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
    const time = (x / rect.width) * duration;

    // Lookup min/max at this index
    const pointsCount = channels[0]?.min_amplitudes.length || 0;
    const idx = Math.min(
      pointsCount - 1,
      Math.max(0, Math.floor((x / rect.width) * pointsCount))
    );

    const channelMins = channels.map((ch) => ch.min_amplitudes[idx] ?? 0);
    const channelMaxs = channels.map((ch) => ch.max_amplitudes[idx] ?? 0);

    setHoverInfo({ time, channelMins, channelMaxs, x });
  };

  const handleMouseLeave = () => {
    setHoverInfo(null);
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || duration <= 0 || !onSeek) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
    const seekTime = (x / rect.width) * duration;
    onSeek(seekTime);
  };

  return (
    <div className="space-y-3 p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-200">
              Deterministic Time-Domain Waveform Envelope
            </h3>
            <p className="text-[11px] text-slate-400">
              Min/max window aggregation ({waveform.point_budget} points, {waveform.aggregation_method})
            </p>
          </div>
        </div>

        {/* Telemetry & Resolution Selector */}
        <div className="flex items-center gap-3">
          {/* Signal Metrics */}
          <div className="flex items-center gap-2 font-mono text-[11px] bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
            <span className="text-slate-400">Peak:</span>
            <span className="text-cyan-400 font-semibold">{waveform.peak_amplitude.toFixed(4)}</span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-400">RMS:</span>
            <span className="text-emerald-400 font-semibold">{waveform.rms_energy.toFixed(4)}</span>
          </div>

          {/* Point Budget Selector */}
          {onBudgetChange && (
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <Sliders className="w-3.5 h-3.5 text-slate-500" />
              <select
                value={waveform.point_budget}
                onChange={(e) => onBudgetChange(parseInt(e.target.value, 10))}
                disabled={isLoading}
                className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-lg px-2 py-1 focus:outline-none focus:border-cyan-500"
                title="Select visualization point budget"
              >
                <option value={500}>500 pts</option>
                <option value={1000}>1,000 pts</option>
                <option value={2000}>2,000 pts</option>
                <option value={4000}>4,000 pts</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Waveform Canvas Area */}
      <div
        ref={containerRef}
        className="relative w-full rounded-xl overflow-hidden border border-slate-800 cursor-crosshair select-none bg-slate-950"
      >
        <canvas
          ref={canvasRef}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          onClick={handleCanvasClick}
          className="w-full block"
        />

        {/* Hover Inspector Tooltip */}
        {hoverInfo && (
          <div
            className="absolute top-2 pointer-events-none bg-slate-900/95 border border-slate-700/80 rounded-lg px-3 py-1.5 shadow-xl text-[11px] font-mono z-10 space-y-0.5"
            style={{
              left: Math.min(
                (containerRef.current?.getBoundingClientRect().width || 400) - 180,
                Math.max(10, hoverInfo.x - 70)
              ),
            }}
          >
            <div className="flex items-center gap-1 text-slate-300">
              <Clock className="w-3 h-3 text-cyan-400" />
              <span>Time: {hoverInfo.time.toFixed(3)}s</span>
            </div>
            {hoverInfo.channelMaxs.map((maxVal, idx) => (
              <div key={idx} className="text-slate-400 flex items-center justify-between gap-3">
                <span>CH {idx + 1}:</span>
                <span className="text-cyan-300">
                  [{hoverInfo.channelMins[idx]?.toFixed(3)}, +{maxVal.toFixed(3)}]
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Loading Overlay */}
        {isLoading && (
          <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center">
            <span className="text-xs font-mono text-cyan-400 animate-pulse">
              Computing Aggregated Envelope...
            </span>
          </div>
        )}
      </div>

      {/* Time Axis Bar */}
      <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 px-1">
        <span>0.00s</span>
        <span>{(duration * 0.25).toFixed(2)}s</span>
        <span>{(duration * 0.5).toFixed(2)}s</span>
        <span>{(duration * 0.75).toFixed(2)}s</span>
        <span>{duration.toFixed(2)}s</span>
      </div>

      {/* Downsampling Disclaimer */}
      <div className="text-[11px] text-slate-400 flex items-center justify-between pt-1 border-t border-slate-800/60">
        <span className="flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span>
            {waveform.downsampled
              ? `Bounded aggregation: ${waveform.total_samples.toLocaleString()} raw samples aggregated into ${waveform.point_budget} min/max buckets.`
              : `Full sample view: ${waveform.total_samples} raw samples displayed without decimation.`}
          </span>
        </span>
        <span className="font-mono text-[10px] text-slate-500">
          Rate: {waveform.sample_rate_hz.toLocaleString()} Hz
        </span>
      </div>
    </div>
  );
};
