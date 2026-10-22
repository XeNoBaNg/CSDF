/**
 * Audio Inspection and Signal Visualization API Client.
 *
 * Implements non-destructive inspection calls:
 * - Metadata extraction (encoded file properties, decoded acoustic properties, embedded tags)
 * - Deterministic waveform envelope generation
 * - STFT magnitude spectrogram (time-frequency dB heatmap)
 * - FFT power spectrum (calibrated frequency axis, dominant frequency peak)
 * - Direct playback streaming URL
 */

import { apiClient } from './client';
import type {
  AudioMetadataResponse,
  WaveformResponse,
  SpectrogramResponse,
  SpectrumResponse,
} from '../types';

export interface WaveformQueryOptions {
  point_budget?: number;
}

export interface SpectrogramQueryOptions {
  n_fft?: number;
  hop_length?: number;
  max_freq_hz?: number;
}

export interface SpectrumQueryOptions {
  num_bins?: number;
  max_freq_hz?: number;
}

/**
 * Fetch extracted audio metadata and embedded tags for an evidence item.
 */
export async function getAudioMetadata(evidenceId: string): Promise<AudioMetadataResponse> {
  const response = await apiClient.get<AudioMetadataResponse>(
    `/v1/evidence/${encodeURIComponent(evidenceId)}/metadata`
  );
  return response.data;
}

/**
 * Fetch downsampled min/max waveform envelope for time-domain inspection.
 */
export async function getAudioWaveform(
  evidenceId: string,
  options?: WaveformQueryOptions
): Promise<WaveformResponse> {
  const response = await apiClient.get<WaveformResponse>(
    `/v1/evidence/${encodeURIComponent(evidenceId)}/waveform`,
    {
      params: options,
    }
  );
  return response.data;
}

/**
 * Fetch STFT magnitude spectrogram data in decibels.
 */
export async function getAudioSpectrogram(
  evidenceId: string,
  options?: SpectrogramQueryOptions
): Promise<SpectrogramResponse> {
  const response = await apiClient.get<SpectrogramResponse>(
    `/v1/evidence/${encodeURIComponent(evidenceId)}/spectrogram`,
    {
      params: options,
    }
  );
  return response.data;
}

/**
 * Fetch FFT power spectrum and detected dominant frequency peak.
 */
export async function getAudioSpectrum(
  evidenceId: string,
  options?: SpectrumQueryOptions
): Promise<SpectrumResponse> {
  const response = await apiClient.get<SpectrumResponse>(
    `/v1/evidence/${encodeURIComponent(evidenceId)}/spectrum`,
    {
      params: options,
    }
  );
  return response.data;
}

/**
 * Resolve direct audio streaming URL supporting HTTP Range partial content.
 */
export function getAudioPlaybackUrl(evidenceId: string): string {
  const base = apiClient.defaults.baseURL || '/api';
  return `${base}/v1/evidence/${encodeURIComponent(evidenceId)}/audio`;
}
