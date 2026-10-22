import React, { useState } from 'react';
import {
  KeyRound,
  Copy,
  Check,
  Tag,
  HardDrive,
  Cpu,
} from 'lucide-react';
import type { AudioMetadataResponse } from '../../types';

interface MetadataInspectorProps {
  metadata: AudioMetadataResponse;
}

export const MetadataInspector: React.FC<MetadataInspectorProps> = ({ metadata }) => {
  const [copiedHash, setCopiedHash] = useState(false);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const copyHash = (hash: string) => {
    navigator.clipboard.writeText(hash).then(() => {
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    });
  };

  const embeddedTags = Object.entries(metadata.embedded_metadata || {}).filter(
    ([_, val]) => val !== null && val !== undefined && val !== ''
  );

  return (
    <div className="space-y-4">
      {/* Dual Column: Encoded File Properties vs Decoded Acoustic Properties */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Encoded Properties Card */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-sm">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <HardDrive className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-slate-200">
                Encoded Storage Container Properties
              </h4>
              <p className="text-[11px] text-slate-400">
                Extracted from the immutable physical evidence bytes
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
              <span className="text-slate-400 text-[11px] block">Container Format</span>
              <span className="font-mono font-bold text-cyan-300 uppercase">
                {metadata.encoded_properties.format}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
              <span className="text-slate-400 text-[11px] block">Storage File Size</span>
              <span className="font-mono text-slate-200">
                {formatBytes(metadata.encoded_properties.file_size_bytes)}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
              <span className="text-slate-400 text-[11px] block">Audio Codec</span>
              <span className="font-mono text-slate-200">
                {metadata.encoded_properties.codec || 'Uncompressed PCM / Native'}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
              <span className="text-slate-400 text-[11px] block">Bitrate (Encoded)</span>
              <span className="font-mono text-slate-200">
                {metadata.encoded_properties.bitrate_kbps
                  ? `${metadata.encoded_properties.bitrate_kbps} kbps`
                  : 'N/A (Headerless/PCM)'}
              </span>
            </div>
          </div>

          {/* Intake SHA-256 Digest */}
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-400 font-medium flex items-center gap-1.5">
                <KeyRound className="w-3.5 h-3.5 text-emerald-400" />
                Intake Cryptographic Hash (SHA-256)
              </span>
              <button
                type="button"
                onClick={() => copyHash(metadata.encoded_properties.sha256_hash)}
                className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-sans"
              >
                {copiedHash ? (
                  <>
                    <Check className="w-3 h-3 text-emerald-400" />
                    <span>Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>
            <p className="font-mono text-[11px] text-emerald-300 break-all select-all bg-slate-900 p-2 rounded-lg border border-slate-800">
              {metadata.encoded_properties.sha256_hash}
            </p>
          </div>
        </div>

        {/* Decoded Acoustic Properties Card */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-sm">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-slate-200">
                Decoded Acoustic Signal Properties
              </h4>
              <p className="text-[11px] text-slate-400">
                Evaluated in-memory via non-destructive temporary decoding
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
              <span className="text-slate-400 text-[11px] block">Acoustic Duration</span>
              <span className="font-mono font-bold text-emerald-300">
                {metadata.decoded_properties.duration_seconds.toFixed(3)}s
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
              <span className="text-slate-400 text-[11px] block">Sample Rate</span>
              <span className="font-mono font-bold text-slate-200">
                {metadata.decoded_properties.sample_rate_hz.toLocaleString()} Hz
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
              <span className="text-slate-400 text-[11px] block">Channel Configuration</span>
              <span className="font-mono text-slate-200">
                {metadata.decoded_properties.channels === 1
                  ? '1 Channel (Mono)'
                  : metadata.decoded_properties.channels === 2
                  ? '2 Channels (Stereo)'
                  : `${metadata.decoded_properties.channels} Channels`}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
              <span className="text-slate-400 text-[11px] block">Decoded Total Samples</span>
              <span className="font-mono text-slate-200">
                {metadata.decoded_properties.total_samples.toLocaleString()}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
              <span className="text-slate-400 text-[11px] block">Sample Format</span>
              <span className="font-mono text-slate-200">
                {metadata.decoded_properties.sample_format || 'IEEE Float / Linear PCM'}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
              <span className="text-slate-400 text-[11px] block">Bit Depth</span>
              <span className="font-mono text-slate-200">
                {metadata.decoded_properties.bit_depth
                  ? `${metadata.decoded_properties.bit_depth}-bit`
                  : 'N/A (Float / VBR)'}
              </span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between text-xs">
            <span className="text-slate-400 text-[11px]">Integrity Pre-Verification:</span>
            <span className="font-mono text-emerald-400 font-semibold text-[11px]">
              {metadata.integrity_verified ? '✓ SHA-256 Passed Prior to Decoding' : 'Unverified'}
            </span>
          </div>
        </div>
      </div>

      {/* Embedded Metadata Tags Card */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Tag className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-slate-200">
                Embedded Audio Tags & Metadata Headers
              </h4>
              <p className="text-[11px] text-slate-400">
                Extracted via mutagen parser (ID3, RIFF INFO, Vorbis comments)
              </p>
            </div>
          </div>
          <span className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
            {embeddedTags.length} tag(s) detected
          </span>
        </div>

        {embeddedTags.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {embeddedTags.map(([key, val]) => (
              <div
                key={key}
                className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1"
              >
                <span className="text-slate-400 text-[11px] uppercase tracking-wider font-mono block">
                  {key}
                </span>
                <span className="text-xs text-slate-200 font-mono break-all block">
                  {String(val)}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center text-xs text-slate-400">
            No embedded ID3, RIFF INFO, or Vorbis metadata tags present in this evidence container.
          </div>
        )}
      </div>
    </div>
  );
};
