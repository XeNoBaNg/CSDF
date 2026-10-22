/**
 * Phase 4 Forensic Signal Anomaly Analysis API Client.
 *
 * Dispatches explainable detection requests to the backend:
 * - Silence & low-energy interval detection
 * - Abrupt amplitude transition detection
 * - Spectral flux inconsistency detection
 */

import { apiClient } from './client';
import type { AnalysisRequest, AnalysisResponse } from '../types';

/**
 * Triggers synchronous explainable signal anomaly analysis on registered evidence.
 *
 * @param evidenceId Unique server-assigned evidence ID.
 * @param request Detector selection flags and threshold parameters.
 * @returns Comprehensive AnalysisResponse with timestamped ForensicFinding items.
 */
export async function analyzeEvidence(
  evidenceId: string,
  request?: AnalysisRequest
): Promise<AnalysisResponse> {
  const response = await apiClient.post<AnalysisResponse>(
    `/v1/evidence/${encodeURIComponent(evidenceId)}/analyze`,
    request || {}
  );
  return response.data;
}
