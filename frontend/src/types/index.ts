/**
 * Core type definitions for AudioSleuth frontend.
 */

export interface ComponentStatus {
  status: 'healthy' | 'degraded' | 'unhealthy' | string;
  details: Record<string, unknown>;
}

export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
  uptime_seconds: number;
  components: {
    storage?: ComponentStatus;
    cryptography?: ComponentStatus;
    persistence?: ComponentStatus;
    [key: string]: ComponentStatus | undefined;
  };
}

export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    timestamp: string;
    details?: Record<string, unknown>;
  };
}

export interface ForensicCase {
  id: string;
  title: string;
  investigator_name: string;
  notes?: string | null;
  description?: string | null;
  status: 'active' | 'closed' | string;
  created_at: string;
  updated_at: string;
  evidence_count: number;
}

export interface CaseCreatePayload {
  title: string;
  investigator_name: string;
  notes?: string;
  description?: string;
}

export interface CaseUpdatePayload {
  title?: string;
  investigator_name?: string;
  notes?: string;
  description?: string;
  status?: 'active' | 'closed';
}

export interface CaseStatusUpdatePayload {
  status: 'active' | 'closed';
  reason?: string;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  action: string;
  outcome: string;
  case_id?: string | null;
  evidence_id?: string | null;
  details: Record<string, unknown>;
}

export interface AuditListResponse {
  items: AuditEvent[];
  total: number;
  case_id?: string | null;
  disclaimer?: string;
}


export interface EvidenceItem {
  id: string;
  case_id: string;
  original_filename: string;
  file_size_bytes: number;
  sha256_hash: string;
  format: 'wav' | 'mp3' | 'flac' | string;
  mime_type: string;
  ingested_at: string;
  integrity_status: string;
}

export interface IntegrityVerificationResult {
  evidence_id: string;
  case_id: string;
  expected_sha256: string;
  calculated_sha256: string;
  status: 'match' | 'mismatch' | 'unverifiable' | string;
  verified_at: string;
  explanation: string;
  disclaimer: string;
}

// =========================================================================
// Phase 3: Audio Inspection & Visualization Types
// =========================================================================

export interface EncodedProperties {
  format: string;
  file_size_bytes: number;
  sha256_hash: string;
  codec?: string | null;
  bitrate_kbps?: number | null;
}

export interface DecodedProperties {
  duration_seconds: number;
  sample_rate_hz: number;
  channels: number;
  total_samples: number;
  sample_format?: string | null;
  bit_depth?: number | null;
}

export interface AudioMetadataResponse {
  evidence_id: string;
  case_id: string;
  original_filename: string;
  integrity_verified: boolean;
  encoded_properties: EncodedProperties;
  decoded_properties: DecodedProperties;
  embedded_metadata: Record<string, string | null>;
}

export interface ChannelWaveform {
  channel_index: number;
  min_amplitudes: number[];
  max_amplitudes: number[];
}

export interface WaveformResponse {
  evidence_id: string;
  source_sha256: string;
  sample_rate_hz: number;
  duration_seconds: number;
  total_samples: number;
  point_budget: number;
  downsampled: boolean;
  aggregation_method: string;
  time_axis: number[];
  channels: ChannelWaveform[];
  peak_amplitude: number;
  rms_energy: number;
}

export interface SpectrogramResponse {
  evidence_id: string;
  source_sha256: string;
  duration_seconds: number;
  sample_rate_hz: number;
  n_fft: number;
  hop_length: number;
  window_type: string;
  unit: string;
  min_db: number;
  max_db: number;
  time_axis: number[];
  freq_axis: number[];
  magnitudes_db: number[][];
}

export interface SpectrumResponse {
  evidence_id: string;
  source_sha256: string;
  sample_rate_hz: number;
  nyquist_hz: number;
  window_type: string;
  num_bins: number;
  frequencies_hz: number[];
  magnitudes_db: number[];
  dominant_frequency_hz?: number | null;
  dominant_magnitude_db?: number | null;
}

// =========================================================================
// Phase 4: Forensic Signal Anomaly Analysis & Findings Types
// =========================================================================

export type FindingCategory = 'silence' | 'transition' | 'spectral';
export type ReviewPriority = 'low' | 'medium' | 'high' | 'informational';

export interface ForensicFinding {
  id: string;
  evidence_id: string;
  source_sha256: string;
  detector_name: string;
  algorithm_version: string;
  category: FindingCategory;
  priority: ReviewPriority;
  start_time: number;
  end_time: number;
  duration_seconds: number;
  event_time?: number | null;
  metric_name: string;
  measured_value: number;
  applied_threshold: number;
  units: string;
  parameters: Record<string, unknown>;
  explanation: string;
  suggested_action: string;
  disclaimer: string;
}

export interface SilenceDetectionParams {
  window_duration_seconds?: number;
  hop_duration_seconds?: number;
  rms_threshold?: number;
  min_silence_duration_seconds?: number;
}

export interface TransitionDetectionParams {
  threshold?: number;
  min_separation_seconds?: number;
  context_window_seconds?: number;
}

export interface SpectralDetectionParams {
  n_fft?: number;
  hop_length?: number;
  threshold?: number;
  min_separation_seconds?: number;
  context_window_seconds?: number;
}

export interface AnalysisRequest {
  enable_silence?: boolean;
  enable_transitions?: boolean;
  enable_spectral_flux?: boolean;
  silence_params?: SilenceDetectionParams;
  transition_params?: TransitionDetectionParams;
  spectral_params?: SpectralDetectionParams;
}

export interface AnalysisSummary {
  total_findings: number;
  by_category: Record<string, number>;
  by_priority: Record<string, number>;
  execution_time_ms: number;
}

export interface AnalysisResponse {
  analysis_id: string;
  evidence_id: string;
  source_sha256: string;
  created_at: string;
  execution_status: string;
  summary: AnalysisSummary;
  findings: ForensicFinding[];
  parameters_applied: Record<string, unknown>;
}

// =========================================================================
// Phase 6B: Cross-Recording Forensic Comparison Schemas
// =========================================================================

export interface GlobalEvidenceListResponse {
  items: EvidenceItem[];
  total: number;
}

export interface ComparisonRequest {
  evidence_id_a: string;
  evidence_id_b: string;
  include_anomaly_comparison?: boolean;
  envelope_points?: number;
  spectral_bins?: number;
  notes?: string;
}

export interface MetadataComparison {
  filename_a: string;
  filename_b: string;
  format_a: string;
  format_b: string;
  format_match: boolean;
  file_size_bytes_a: number;
  file_size_bytes_b: number;
  file_size_diff_bytes: number;
  sha256_a: string;
  sha256_b: string;
  sha256_match: boolean;
  duration_seconds_a: number;
  duration_seconds_b: number;
  duration_diff_seconds: number;
  duration_match: boolean;
  sample_rate_hz_a: number;
  sample_rate_hz_b: number;
  sample_rate_match: boolean;
  channels_a: number;
  channels_b: number;
  channels_match: boolean;
  bit_depth_a?: number | null;
  bit_depth_b?: number | null;
  bit_depth_match: boolean;
}

export interface SignalComparison {
  peak_amplitude_a: number;
  peak_amplitude_b: number;
  peak_amplitude_diff: number;
  rms_energy_a: number;
  rms_energy_b: number;
  rms_energy_diff: number;
  rms_ratio_db: number;
  crest_factor_a: number;
  crest_factor_b: number;
  zero_crossing_rate_a: number;
  zero_crossing_rate_b: number;
  zero_crossing_rate_diff: number;
  envelope_correlation: number;
  channel_mixdown_policy: string;
}

export interface SpectralComparison {
  centroid_hz_a: number;
  centroid_hz_b: number;
  centroid_diff_hz: number;
  rolloff_hz_a: number;
  rolloff_hz_b: number;
  rolloff_diff_hz: number;
  flatness_a: number;
  flatness_b: number;
  flatness_diff: number;
  spectral_cosine_similarity: number;
  spectral_euclidean_distance: number;
  evaluated_frequency_ceiling_hz: number;
}

export interface AnomalyComparison {
  total_findings_a: number;
  total_findings_b: number;
  silence_findings_a: number;
  silence_findings_b: number;
  transition_findings_a: number;
  transition_findings_b: number;
  spectral_findings_a: number;
  spectral_findings_b: number;
  findings_density_per_min_a: number;
  findings_density_per_min_b: number;
  binned_distribution_a: number[];
  binned_distribution_b: number[];
  timeline_bins: number;
}

export interface ComparisonSummary {
  byte_match: boolean;
  duration_match: boolean;
  acoustic_similarity_label: string;
  transparent_similarity_score: number;
  scoring_formula_explanation: string;
  warnings: string[];
  explanation: string;
}

export interface ComparisonResponse {
  id: string;
  timestamp: string;
  evidence_id_a: string;
  evidence_id_b: string;
  case_id_a?: string | null;
  case_id_b?: string | null;
  metadata_comparison: MetadataComparison;
  signal_comparison: SignalComparison;
  spectral_comparison: SpectralComparison;
  anomaly_comparison?: AnomalyComparison | null;
  summary: ComparisonSummary;
  disclaimer: string;
}


