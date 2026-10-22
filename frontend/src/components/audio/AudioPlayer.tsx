import React, { useRef, useState, useEffect, useCallback } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  Volume2,
  VolumeX,
  Gauge,
  AlertCircle,
} from 'lucide-react';

interface AudioPlayerProps {
  src: string;
  onTimeUpdate?: (time: number) => void;
  externalSeekTime?: number | null;
  duration?: number;
  currentTime?: number;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({
  src,
  onTimeUpdate,
  externalSeekTime,
  duration: fallbackDuration = 0,
}) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [audioDuration, setAudioDuration] = useState(fallbackDuration);
  const [volume, setVolume] = useState(0.8);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Sync external seek requests (e.g. clicking on waveform or spectrogram)
  useEffect(() => {
    if (
      externalSeekTime !== null &&
      externalSeekTime !== undefined &&
      audioRef.current &&
      Math.abs(audioRef.current.currentTime - externalSeekTime) > 0.05
    ) {
      audioRef.current.currentTime = externalSeekTime;
      setCurrentTime(externalSeekTime);
    }
  }, [externalSeekTime]);

  // Handle time update
  const handleTimeUpdate = useCallback(() => {
    if (audioRef.current) {
      const time = audioRef.current.currentTime;
      setCurrentTime(time);
      if (onTimeUpdate) {
        onTimeUpdate(time);
      }
    }
  }, [onTimeUpdate]);

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      const dur = audioRef.current.duration;
      if (Number.isFinite(dur) && dur > 0) {
        setAudioDuration(dur);
      } else if (fallbackDuration > 0) {
        setAudioDuration(fallbackDuration);
      }
      audioRef.current.volume = volume;
      audioRef.current.playbackRate = playbackRate;
      setLoadError(null);
    }
  };

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch((err) => {
        console.warn('Playback error:', err);
        setLoadError('Failed to start audio playback. Decoder may not support format.');
      });
    }
  };

  const handleSeekChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = parseFloat(e.target.value);
    setCurrentTime(newTime);
    if (audioRef.current) {
      audioRef.current.currentTime = newTime;
    }
    if (onTimeUpdate) {
      onTimeUpdate(newTime);
    }
  };

  const handleRestart = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      setCurrentTime(0);
      if (onTimeUpdate) onTimeUpdate(0);
    }
  };

  const toggleMute = () => {
    if (!audioRef.current) return;
    const nextMuted = !isMuted;
    setIsMuted(nextMuted);
    audioRef.current.muted = nextMuted;
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    if (audioRef.current) {
      audioRef.current.volume = val;
      if (val === 0) {
        setIsMuted(true);
        audioRef.current.muted = true;
      } else if (isMuted) {
        setIsMuted(false);
        audioRef.current.muted = false;
      }
    }
  };

  const cyclePlaybackRate = () => {
    const rates = [0.5, 1.0, 1.5, 2.0];
    const currentIndex = rates.indexOf(playbackRate);
    const nextRate = rates[(currentIndex + 1) % rates.length];
    setPlaybackRate(nextRate);
    if (audioRef.current) {
      audioRef.current.playbackRate = nextRate;
    }
  };

  const formatTime = (seconds: number): string => {
    if (!Number.isFinite(seconds) || seconds < 0) return '00:00.00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const millis = Math.floor((seconds % 1) * 100);
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(millis).padStart(2, '0')}`;
  };

  const displayDuration = audioDuration > 0 ? audioDuration : fallbackDuration;
  const progressPercent = displayDuration > 0 ? (currentTime / displayDuration) * 100 : 0;

  return (
    <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 shadow-md space-y-3">
      {/* Hidden HTML5 Audio Element */}
      <audio
        ref={audioRef}
        src={src}
        preload="metadata"
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => {
          setIsPlaying(false);
          setCurrentTime(0);
        }}
        onError={() => setLoadError('Audio streaming or format decoding error')}
      />

      {loadError && (
        <div className="flex items-center gap-2 p-2.5 rounded-lg bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{loadError}</span>
        </div>
      )}

      {/* Main Controls Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Play/Pause & Transport */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={togglePlay}
            className="p-3 rounded-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold transition-all shadow-md hover:scale-105 active:scale-95"
            title={isPlaying ? 'Pause' : 'Play audio'}
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
          </button>

          <button
            type="button"
            onClick={handleRestart}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Restart from beginning"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          {/* Time Display */}
          <div className="font-mono text-xs bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 tracking-wider">
            <span className="text-cyan-400 font-semibold">{formatTime(currentTime)}</span>
            <span className="text-slate-500 mx-1.5">/</span>
            <span className="text-slate-400">{formatTime(displayDuration)}</span>
          </div>
        </div>

        {/* Scrubber Slider */}
        <div className="flex-1 max-w-md flex items-center gap-2">
          <input
            type="range"
            min={0}
            max={displayDuration || 1}
            step={0.01}
            value={currentTime}
            onChange={handleSeekChange}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400 hover:accent-cyan-300"
            title="Seek playback position"
          />
        </div>

        {/* Volume & Speed Controls */}
        <div className="flex items-center gap-3 self-end sm:self-auto">
          {/* Rate Button */}
          <button
            type="button"
            onClick={cyclePlaybackRate}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-[11px] font-mono text-slate-300 border border-slate-700 transition-colors"
            title="Adjust playback speed"
          >
            <Gauge className="w-3.5 h-3.5 text-cyan-400" />
            <span>{playbackRate}x</span>
          </button>

          {/* Volume Control */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={toggleMute}
              className="text-slate-400 hover:text-slate-200 transition-colors"
              title={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted || volume === 0 ? (
                <VolumeX className="w-4 h-4 text-rose-400" />
              ) : (
                <Volume2 className="w-4 h-4" />
              )}
            </button>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              className="w-16 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
              title="Volume"
            />
          </div>
        </div>
      </div>

      {/* Playback progress indicator bar */}
      <div className="w-full bg-slate-950 rounded-full h-1 overflow-hidden">
        <div
          className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-full transition-all duration-75"
          style={{ width: `${Math.min(100, Math.max(0, progressPercent))}%` }}
        />
      </div>
    </div>
  );
};
