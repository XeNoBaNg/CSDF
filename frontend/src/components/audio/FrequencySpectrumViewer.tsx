import React, { useRef, useEffect, useState, useCallback } from 'react';
import {
  Zap,
  TrendingUp,
  Info,
} from 'lucide-react';
import type { SpectrumResponse } from '../../types';

interface FrequencySpectrumViewerProps {
  spectrum: SpectrumResponse;
  onNumBinsChange?: (bins: number) => void;
  isLoading?: boolean;
}

export const FrequencySpectrumViewer: React.FC<FrequencySpectrumViewerProps> = ({
  spectrum,
  onNumBinsChange,
  isLoading = false,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [hoverInfo, setHoverInfo] = useState<{
    freq: number;
    db: number;
    x: number;
    y: number;
  } | null>(null);

  const frequencies = spectrum.frequencies_hz || [];
  const magnitudes = spectrum.magnitudes_db || [];
  const numPoints = Math.min(frequencies.length, magnitudes.length);
  const nyquist = spectrum.nyquist_hz || (frequencies[frequencies.length - 1] || 22050);

  // Compute min/max dB for scaling
  let minDb = -80.0;
  let maxDb = 0.0;
  if (magnitudes.length > 0) {
    minDb = Math.min(...magnitudes);
    maxDb = Math.max(...magnitudes);
    // Ensure reasonable visual dynamic range
    if (maxDb - minDb < 10) {
      minDb = maxDb - 40;
    }
  }

  // Render power spectrum curve to canvas
  const renderCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !containerRef.current) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = containerRef.current.getBoundingClientRect();
    const width = Math.floor(rect.width);
    const height = 220;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    ctx.save();
    ctx.scale(dpr, dpr);

    // Background
    ctx.fillStyle = '#030712';
    ctx.fillRect(0, 0, width, height);

    if (numPoints === 0) {
      ctx.fillStyle = '#64748b';
      ctx.font = '12px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('No frequency spectrum data available', width / 2, height / 2);
      ctx.restore();
      return;
    }

    const padding = { top: 20, right: 30, bottom: 25, left: 45 };
    const plotW = width - padding.left - padding.right;
    const plotH = height - padding.top - padding.bottom;

    // Helper functions for coordinates
    const getX = (freq: number) => padding.left + (freq / (nyquist || 1)) * plotW;
    const getY = (db: number) =>
      padding.top + (1 - (db - minDb) / (maxDb - minDb || 1)) * plotH;

    // Horizontal dB grid lines
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#64748b';
    ctx.font = '9px monospace';
    ctx.textAlign = 'right';

    const dbSteps = [0, -20, -40, -60, -80].filter((db) => db <= maxDb && db >= minDb);
    dbSteps.forEach((db) => {
      const y = getY(db);
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(padding.left + plotW, y);
      ctx.stroke();

      ctx.fillText(`${db.toFixed(0)} dB`, padding.left - 6, y + 3);
    });

    // Vertical Frequency grid lines
    const freqSteps = [500, 1000, 2500, 5000, 10000, 15000, 20000].filter(
      (f) => f < nyquist
    );

    ctx.textAlign = 'center';
    freqSteps.forEach((f) => {
      const x = getX(f);
      ctx.strokeStyle = '#1e293b';
      ctx.beginPath();
      ctx.moveTo(x, padding.top);
      ctx.lineTo(x, padding.top + plotH);
      ctx.stroke();

      ctx.fillText(
        f >= 1000 ? `${f / 1000}k` : `${f}`,
        x,
        padding.top + plotH + 15
      );
    });

    // Draw Spectrum Curve Fill Gradient
    const fillGrad = ctx.createLinearGradient(0, padding.top, 0, padding.top + plotH);
    fillGrad.addColorStop(0, 'rgba(16, 185, 129, 0.35)'); // emerald-500
    fillGrad.addColorStop(1, 'rgba(16, 185, 129, 0.02)');

    ctx.beginPath();
    ctx.moveTo(getX(frequencies[0]), padding.top + plotH);
    for (let i = 0; i < numPoints; i++) {
      const x = getX(frequencies[i]);
      const y = Math.min(padding.top + plotH, Math.max(padding.top, getY(magnitudes[i])));
      ctx.lineTo(x, y);
    }
    ctx.lineTo(getX(frequencies[numPoints - 1]), padding.top + plotH);
    ctx.closePath();
    ctx.fillStyle = fillGrad;
    ctx.fill();

    // Draw Stroke Line
    ctx.beginPath();
    for (let i = 0; i < numPoints; i++) {
      const x = getX(frequencies[i]);
      const y = Math.min(padding.top + plotH, Math.max(padding.top, getY(magnitudes[i])));
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = '#10b981'; // emerald-500
    ctx.lineWidth = 1.8;
    ctx.stroke();

    // Draw Dominant Peak Marker
    if (
      spectrum.dominant_frequency_hz !== null &&
      spectrum.dominant_frequency_hz !== undefined &&
      spectrum.dominant_magnitude_db !== null &&
      spectrum.dominant_magnitude_db !== undefined
    ) {
      const domX = getX(spectrum.dominant_frequency_hz);
      const domY = getY(spectrum.dominant_magnitude_db);

      // Vertical marker beacon line
      ctx.strokeStyle = '#f59e0b'; // amber-500
      ctx.lineWidth = 1.5;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(domX, padding.top);
      ctx.lineTo(domX, padding.top + plotH);
      ctx.stroke();
      ctx.setLineDash([]);

      // Peak circle
      ctx.fillStyle = '#f59e0b';
      ctx.beginPath();
      ctx.arc(domX, domY, 4.5, 0, Math.PI * 2);
      ctx.fill();

      // Peak label
      ctx.fillStyle = '#fef3c7'; // amber-100
      ctx.font = 'bold 9px monospace';
      ctx.textAlign = 'center';
      const labelText = `★ Peak: ${spectrum.dominant_frequency_hz.toFixed(1)} Hz (${spectrum.dominant_magnitude_db.toFixed(1)} dB)`;
      ctx.fillText(labelText, domX, Math.max(14, domY - 8));
    }

    // Hover crosshairs
    if (hoverInfo) {
      ctx.strokeStyle = '#38bdf8'; // sky-400
      ctx.lineWidth = 1;
      ctx.setLineDash([2, 2]);

      ctx.beginPath();
      ctx.moveTo(hoverInfo.x, padding.top);
      ctx.lineTo(hoverInfo.x, padding.top + plotH);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(padding.left, hoverInfo.y);
      ctx.lineTo(padding.left + plotW, hoverInfo.y);
      ctx.stroke();

      ctx.setLineDash([]);
    }

    ctx.restore();
  }, [frequencies, magnitudes, numPoints, nyquist, minDb, maxDb, spectrum, hoverInfo]);

  useEffect(() => {
    renderCanvas();
    const handleResize = () => renderCanvas();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [renderCanvas]);

  // Mouse hover listener
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || numPoints === 0 || nyquist <= 0) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
    const y = Math.max(0, Math.min(rect.height, e.clientY - rect.top));

    const padding = { top: 20, right: 30, bottom: 25, left: 45 };
    const plotW = rect.width - padding.left - padding.right;

    if (x < padding.left || x > padding.left + plotW) {
      setHoverInfo(null);
      return;
    }

    const freqFraction = (x - padding.left) / plotW;
    const freq = freqFraction * nyquist;

    // Find closest bin
    const idx = Math.min(
      numPoints - 1,
      Math.max(0, Math.round(freqFraction * (numPoints - 1)))
    );
    const db = magnitudes[idx] ?? minDb;

    setHoverInfo({ freq: frequencies[idx] || freq, db, x, y });
  };

  const handleMouseLeave = () => {
    setHoverInfo(null);
  };

  return (
    <div className="space-y-3 p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <TrendingUp className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-200">
              FFT Power Spectrum (Calibrated Frequency Axis)
            </h3>
            <p className="text-[11px] text-slate-400">
              One-sided rFFT magnitude scaled in decibels relative to peak (Hann window)
            </p>
          </div>
        </div>

        {/* Dominant Peak Badge & Bins Selector */}
        <div className="flex items-center gap-3">
          {spectrum.dominant_frequency_hz !== null && (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-mono font-medium">
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              <span>
                Dominant Peak: {spectrum.dominant_frequency_hz?.toFixed(1)} Hz (
                {spectrum.dominant_magnitude_db?.toFixed(1)} dB)
              </span>
            </div>
          )}

          {onNumBinsChange && (
            <div className="flex items-center gap-1 text-xs text-slate-400">
              <span className="text-[11px]">Bins:</span>
              <select
                value={spectrum.num_bins}
                onChange={(e) => onNumBinsChange(parseInt(e.target.value, 10))}
                disabled={isLoading}
                className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-lg px-2 py-1 focus:outline-none focus:border-emerald-500"
                title="Number of FFT frequency bins"
              >
                <option value={256}>256</option>
                <option value={512}>512</option>
                <option value={1024}>1024</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Spectrum Canvas Area */}
      <div
        ref={containerRef}
        className="relative w-full rounded-xl overflow-hidden border border-slate-800 cursor-crosshair select-none bg-slate-950"
      >
        <canvas
          ref={canvasRef}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          className="w-full block"
        />

        {/* Hover Inspector Tooltip */}
        {hoverInfo && (
          <div
            className="absolute pointer-events-none bg-slate-900/95 border border-emerald-500/40 rounded-lg px-3 py-1.5 shadow-xl text-[11px] font-mono z-10 space-y-0.5"
            style={{
              left: Math.min(
                (containerRef.current?.getBoundingClientRect().width || 400) - 180,
                Math.max(10, hoverInfo.x + 10)
              ),
              top: Math.min(150, Math.max(10, hoverInfo.y - 30)),
            }}
          >
            <div className="text-emerald-300 flex items-center gap-1.5">
              <span>Freq: {hoverInfo.freq.toFixed(1)} Hz</span>
            </div>
            <div className="text-slate-200">
              Power: {hoverInfo.db.toFixed(1)} dB
            </div>
          </div>
        )}

        {/* Loading Overlay */}
        {isLoading && (
          <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center">
            <span className="text-xs font-mono text-emerald-400 animate-pulse">
              Computing FFT Power Spectrum...
            </span>
          </div>
        )}
      </div>

      {/* Spectrum Footer */}
      <div className="text-[11px] text-slate-400 flex items-center justify-between pt-1 border-t border-slate-800/60">
        <span className="flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5 text-emerald-400" />
          <span>
            Computed across audio with safe finite log-clamping to prevent NaN/infinite values.
          </span>
        </span>
        <span className="font-mono text-[10px] text-slate-500">
          Nyquist Limit: {nyquist.toLocaleString()} Hz
        </span>
      </div>
    </div>
  );
};
