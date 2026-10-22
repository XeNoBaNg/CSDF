import React, { useRef, useEffect, useState, useCallback } from 'react';
import {
  Clock,
  Zap,
  Info,
  Radio,
} from 'lucide-react';
import type { SpectrogramResponse, ForensicFinding } from '../../types';

interface SpectrogramViewerProps {
  spectrogram: SpectrogramResponse;
  currentTime?: number;
  onSeek?: (timeSeconds: number) => void;
  onParamsChange?: (nFft: number, hopLength: number) => void;
  isLoading?: boolean;
  findings?: ForensicFinding[];
  selectedFindingId?: string | null;
}

// Scientific "Inferno" colormap interpolation: t in [0, 1] -> [R, G, B]
function infernoColor(t: number): [number, number, number] {
  const clamped = Math.max(0, Math.min(1, t));

  // Control points: 0.0, 0.25, 0.5, 0.75, 1.0
  const c0: [number, number, number] = [3, 5, 20]; // deep dark purple
  const c1: [number, number, number] = [65, 12, 105]; // purple
  const c2: [number, number, number] = [182, 54, 86]; // magenta
  const c3: [number, number, number] = [245, 136, 12]; // orange
  const c4: [number, number, number] = [252, 255, 164]; // bright yellow

  if (clamped <= 0.25) {
    const s = clamped / 0.25;
    return [
      Math.round(c0[0] + s * (c1[0] - c0[0])),
      Math.round(c0[1] + s * (c1[1] - c0[1])),
      Math.round(c0[2] + s * (c1[2] - c0[2])),
    ];
  } else if (clamped <= 0.5) {
    const s = (clamped - 0.25) / 0.25;
    return [
      Math.round(c1[0] + s * (c2[0] - c1[0])),
      Math.round(c1[1] + s * (c2[1] - c1[1])),
      Math.round(c1[2] + s * (c2[2] - c1[2])),
    ];
  } else if (clamped <= 0.75) {
    const s = (clamped - 0.5) / 0.25;
    return [
      Math.round(c2[0] + s * (c3[0] - c2[0])),
      Math.round(c2[1] + s * (c3[1] - c2[1])),
      Math.round(c2[2] + s * (c3[2] - c2[2])),
    ];
  } else {
    const s = (clamped - 0.75) / 0.25;
    return [
      Math.round(c3[0] + s * (c4[0] - c3[0])),
      Math.round(c3[1] + s * (c4[1] - c3[1])),
      Math.round(c3[2] + s * (c4[2] - c3[2])),
    ];
  }
}

export const SpectrogramViewer: React.FC<SpectrogramViewerProps> = ({
  spectrogram,
  currentTime = 0,
  onSeek,
  onParamsChange,
  isLoading = false,
  findings = [],
  selectedFindingId = null,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [hoverInfo, setHoverInfo] = useState<{
    time: number;
    freq: number;
    db: number;
    x: number;
    y: number;
  } | null>(null);

  const [localNfft, setLocalNfft] = useState(spectrogram.n_fft || 1024);
  const [localHop, setLocalHop] = useState(spectrogram.hop_length || 256);

  const numFreqBins = spectrogram.freq_axis?.length || 0;
  const numTimeFrames = spectrogram.time_axis?.length || 0;
  const duration = spectrogram.duration_seconds || 1;
  const maxFreq = spectrogram.freq_axis?.[numFreqBins - 1] || 1;

  // Render STFT dB heatmap to canvas
  const renderCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !containerRef.current) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = containerRef.current.getBoundingClientRect();
    const width = Math.floor(rect.width);
    const height = 260;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    ctx.save();
    ctx.scale(dpr, dpr);

    // Dark background
    ctx.fillStyle = '#030712';
    ctx.fillRect(0, 0, width, height);

    if (numFreqBins === 0 || numTimeFrames === 0 || !spectrogram.magnitudes_db?.length) {
      ctx.fillStyle = '#64748b';
      ctx.font = '12px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('No STFT spectrogram data available', width / 2, height / 2);
      ctx.restore();
      return;
    }

    // Render offscreen image bitmap of spectrogram matrix
    const offscreen = document.createElement('canvas');
    offscreen.width = numTimeFrames;
    offscreen.height = numFreqBins;
    const offCtx = offscreen.getContext('2d');

    if (offCtx) {
      const imgData = offCtx.createImageData(numTimeFrames, numFreqBins);
      const data = imgData.data;

      const minDb = spectrogram.min_db;
      const maxDb = spectrogram.max_db;
      const dbRange = Math.max(1e-3, maxDb - minDb);

      // In STFT, row 0 is 0 Hz, row numFreqBins-1 is Nyquist.
      // On canvas, y=0 is top (high freq) and y=height is bottom (0 Hz).
      for (let f = 0; f < numFreqBins; f++) {
        // Invert Y so high frequencies appear at the top
        const targetRow = numFreqBins - 1 - f;
        const rowMagnitudes = spectrogram.magnitudes_db[f];
        if (!rowMagnitudes) continue;

        for (let t = 0; t < numTimeFrames; t++) {
          const dbVal = rowMagnitudes[t] ?? minDb;
          const normalized = (dbVal - minDb) / dbRange;
          const [r, g, b] = infernoColor(normalized);

          const pixelIndex = (targetRow * numTimeFrames + t) * 4;
          data[pixelIndex] = r;
          data[pixelIndex + 1] = g;
          data[pixelIndex + 2] = b;
          data[pixelIndex + 3] = 255;
        }
      }

      offCtx.putImageData(imgData, 0, 0);

      // Draw scaled offscreen canvas with smooth bilinear filtering
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(offscreen, 0, 0, width, height);
    }

    // Draw Frequency grid lines (e.g. 1 kHz, 5 kHz, 10 kHz, 15 kHz)
    const freqGridPoints = [1000, 2000, 5000, 10000, 15000, 20000].filter(
      (f) => f < maxFreq
    );

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);

    freqGridPoints.forEach((freq) => {
      const y = height - (freq / maxFreq) * height;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();

      // Frequency label
      ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
      ctx.font = '9px monospace';
      ctx.textAlign = 'left';
      ctx.fillText(`${freq >= 1000 ? `${freq / 1000}k` : freq} Hz`, 8, y - 3);
    });
    ctx.setLineDash([]);

    // Draw findings overlay regions
    if (findings && findings.length > 0) {
      findings.forEach((f) => {
        const isSelected = selectedFindingId === f.id;
        const xStart = Math.min(width, Math.max(0, (f.start_time / duration) * width));
        const xEnd = Math.min(width, Math.max(0, (f.end_time / duration) * width));
        const regionWidth = Math.max(2, xEnd - xStart);

        if (f.category === 'silence') {
          ctx.fillStyle = isSelected ? 'rgba(6, 182, 212, 0.40)' : 'rgba(6, 182, 212, 0.18)';
          ctx.fillRect(xStart, 0, regionWidth, height);
          ctx.strokeStyle = isSelected ? '#22d3ee' : 'rgba(6, 182, 212, 0.5)';
          ctx.lineWidth = isSelected ? 2 : 1;
          ctx.strokeRect(xStart, 0, regionWidth, height);
        } else if (f.category === 'transition') {
          const eventX = f.event_time != null ? Math.min(width, Math.max(0, (f.event_time / duration) * width)) : (xStart + xEnd) / 2;
          ctx.fillStyle = isSelected ? 'rgba(244, 63, 94, 0.40)' : 'rgba(244, 63, 94, 0.20)';
          ctx.fillRect(xStart, 0, regionWidth, height);
          ctx.strokeStyle = isSelected ? '#f43f5e' : 'rgba(244, 63, 94, 0.85)';
          ctx.lineWidth = isSelected ? 2.5 : 1.5;
          ctx.beginPath();
          ctx.moveTo(eventX, 0);
          ctx.lineTo(eventX, height);
          ctx.stroke();
        } else if (f.category === 'spectral') {
          ctx.fillStyle = isSelected ? 'rgba(168, 85, 247, 0.40)' : 'rgba(168, 85, 247, 0.22)';
          ctx.fillRect(xStart, 0, regionWidth, height);
          ctx.strokeStyle = isSelected ? '#c084fc' : 'rgba(168, 85, 247, 0.6)';
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

      ctx.fillStyle = '#f59e0b';
      ctx.beginPath();
      ctx.arc(playheadX, 6, 4, 0, Math.PI * 2);
      ctx.fill();
    }

    // Draw hover crosshairs
    if (hoverInfo) {
      ctx.strokeStyle = '#38bdf8'; // sky-400
      ctx.lineWidth = 1;
      ctx.setLineDash([2, 2]);

      // Vertical line
      ctx.beginPath();
      ctx.moveTo(hoverInfo.x, 0);
      ctx.lineTo(hoverInfo.x, height);
      ctx.stroke();

      // Horizontal line
      ctx.beginPath();
      ctx.moveTo(0, hoverInfo.y);
      ctx.lineTo(width, hoverInfo.y);
      ctx.stroke();

      ctx.setLineDash([]);
    }

    ctx.restore();
  }, [
    spectrogram,
    numFreqBins,
    numTimeFrames,
    duration,
    maxFreq,
    currentTime,
    hoverInfo,
    findings,
    selectedFindingId,
  ]);

  // Redraw on updates or resize
  useEffect(() => {
    renderCanvas();
    const handleResize = () => renderCanvas();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [renderCanvas]);

  // Mouse hover inspector
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || duration <= 0 || maxFreq <= 0) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
    const y = Math.max(0, Math.min(rect.height, e.clientY - rect.top));

    const time = (x / rect.width) * duration;
    // Y=0 is high freq, Y=height is 0 Hz
    const freq = ((rect.height - y) / rect.height) * maxFreq;

    // Nearest matrix cell lookup
    const tIdx = Math.min(
      numTimeFrames - 1,
      Math.max(0, Math.floor((x / rect.width) * numTimeFrames))
    );
    const fIdx = Math.min(
      numFreqBins - 1,
      Math.max(0, Math.floor(((rect.height - y) / rect.height) * numFreqBins))
    );

    const db = spectrogram.magnitudes_db?.[fIdx]?.[tIdx] ?? spectrogram.min_db;

    setHoverInfo({ time, freq, db, x, y });
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

  const applyParams = () => {
    if (onParamsChange) {
      onParamsChange(localNfft, localHop);
    }
  };

  return (
    <div className="space-y-3 p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Radio className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-200">
              STFT Time-Frequency Magnitude Spectrogram
            </h3>
            <p className="text-[11px] text-slate-400">
              Hann window (N_fft={spectrogram.n_fft}, Hop={spectrogram.hop_length}, Mono Downmix)
            </p>
          </div>
        </div>

        {/* STFT Configuration Controls */}
        {onParamsChange && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400 text-[11px]">N_fft:</span>
            <select
              value={localNfft}
              onChange={(e) => setLocalNfft(parseInt(e.target.value, 10))}
              disabled={isLoading}
              className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-lg px-2 py-1 focus:outline-none focus:border-purple-500"
              title="Window size in samples"
            >
              <option value={512}>512</option>
              <option value={1024}>1024</option>
              <option value={2048}>2048</option>
            </select>

            <span className="text-slate-400 text-[11px] ml-1">Hop:</span>
            <select
              value={localHop}
              onChange={(e) => setLocalHop(parseInt(e.target.value, 10))}
              disabled={isLoading}
              className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-lg px-2 py-1 focus:outline-none focus:border-purple-500"
              title="Hop length in samples"
            >
              <option value={128}>128</option>
              <option value={256}>256</option>
              <option value={512}>512</option>
            </select>

            {(localNfft !== spectrogram.n_fft || localHop !== spectrogram.hop_length) && (
              <button
                type="button"
                onClick={applyParams}
                disabled={isLoading}
                className="px-2.5 py-1 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs transition-colors shadow-xs"
              >
                Apply
              </button>
            )}
          </div>
        )}
      </div>

      {/* Main Heatmap Container with Decibel Colorbar */}
      <div className="flex gap-2">
        {/* Canvas Area */}
        <div
          ref={containerRef}
          className="relative flex-1 rounded-xl overflow-hidden border border-slate-800 cursor-crosshair select-none bg-slate-950"
        >
          <canvas
            ref={canvasRef}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            onClick={handleCanvasClick}
            className="w-full block"
          />

          {/* Hover Crosshair Tooltip */}
          {hoverInfo && (
            <div
              className="absolute pointer-events-none bg-slate-900/95 border border-purple-500/40 rounded-lg px-3 py-1.5 shadow-xl text-[11px] font-mono z-10 space-y-0.5"
              style={{
                left: Math.min(
                  (containerRef.current?.getBoundingClientRect().width || 400) - 200,
                  Math.max(10, hoverInfo.x + 12)
                ),
                top: Math.min(200, Math.max(10, hoverInfo.y - 40)),
              }}
            >
              <div className="text-slate-300 flex items-center gap-1.5">
                <Clock className="w-3 h-3 text-cyan-400" />
                <span>Time: {hoverInfo.time.toFixed(3)}s</span>
              </div>
              <div className="text-purple-300 flex items-center gap-1.5">
                <Zap className="w-3 h-3 text-amber-400" />
                <span>Freq: {hoverInfo.freq.toFixed(1)} Hz</span>
              </div>
              <div className="text-emerald-400 font-bold">
                Magnitude: {hoverInfo.db.toFixed(1)} dB
              </div>
            </div>
          )}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center">
              <span className="text-xs font-mono text-purple-400 animate-pulse">
                Computing Short-Time Fourier Transform (STFT)...
              </span>
            </div>
          )}
        </div>

        {/* Decibel Colorbar Legend */}
        <div className="w-12 flex flex-col items-center justify-between py-1 text-[9px] font-mono text-slate-400 border border-slate-800/80 rounded-xl bg-slate-950 px-1">
          <span>{spectrogram.max_db.toFixed(0)} dB</span>
          <div
            className="w-3 flex-1 my-1 rounded-sm"
            style={{
              background:
                'linear-gradient(to bottom, #fcffa4, #f5880c, #b63656, #410c69, #030514)',
            }}
            title="Decibel magnitude colormap (Inferno scale)"
          />
          <span>{spectrogram.min_db.toFixed(0)} dB</span>
        </div>
      </div>

      {/* Frequency & Time Axis Labels */}
      <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 px-1">
        <span>0.00s</span>
        <span>{(duration * 0.5).toFixed(2)}s</span>
        <span>{duration.toFixed(2)}s</span>
      </div>

      {/* Forensic Footnote */}
      <div className="text-[11px] text-slate-400 flex items-center justify-between pt-1 border-t border-slate-800/60">
        <span className="flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5 text-purple-400" />
          <span>
            Dimensions: {numTimeFrames} time frames × {numFreqBins} frequency bins. Clamped to safe finite range: [{spectrogram.min_db.toFixed(1)} dB, {spectrogram.max_db.toFixed(1)} dB].
          </span>
        </span>
        <span className="font-mono text-[10px] text-slate-500">
          Nyquist: {(maxFreq).toLocaleString()} Hz
        </span>
      </div>
    </div>
  );
};
