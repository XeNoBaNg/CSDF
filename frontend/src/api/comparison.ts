/**
 * API client functions for cross-recording forensic comparison and PDF report export.
 */

import { apiClient } from './client';
import type {
  ComparisonRequest,
  ComparisonResponse,
  GlobalEvidenceListResponse,
  EvidenceItem,
} from '../types';

/**
 * Lists all registered evidence recordings across cases (with optional case filter).
 */
export async function listAllEvidence(caseId?: string): Promise<EvidenceItem[]> {
  const params: Record<string, string> = {};
  if (caseId) {
    params.case_id = caseId;
  }
  const response = await apiClient.get<GlobalEvidenceListResponse>('/v1/evidence', { params });
  return response.data.items;
}

/**
 * Executes a cross-recording forensic comparison between two registered evidence recordings.
 */
export async function compareEvidence(
  request: ComparisonRequest
): Promise<ComparisonResponse> {
  const response = await apiClient.post<ComparisonResponse>(
    '/v1/evidence/compare',
    request
  );
  return response.data;
}

/**
 * Retrieves a previously stored cross-recording comparison result by its unique ID.
 */
export async function getComparison(
  comparisonId: string
): Promise<ComparisonResponse> {
  const response = await apiClient.get<ComparisonResponse>(
    `/v1/comparisons/${encodeURIComponent(comparisonId)}`
  );
  return response.data;
}

/**
 * Downloads a generated forensic comparison PDF report for a stored comparison record.
 */
export async function downloadComparisonReport(
  comparisonId: string
): Promise<void> {
  const response = await apiClient.get<Blob>(
    `/v1/comparisons/${encodeURIComponent(comparisonId)}/report`,
    {
      responseType: 'blob',
    }
  );

  let filename = `AudioSleuth_Comparison_${comparisonId}.pdf`;
  const disposition = response.headers['content-disposition'];
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename="?([^";]+)"?/);
    if (match && match[1]) {
      filename = match[1].trim();
    }
  }

  const blobUrl = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
  const link = document.createElement('a');
  link.href = blobUrl;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(blobUrl);
}

/**
 * Directly compares two evidence items and streams the compiled PDF report.
 */
export async function compareAndDownloadReport(
  request: ComparisonRequest
): Promise<void> {
  const response = await apiClient.post<Blob>(
    '/v1/evidence/compare/report',
    request,
    {
      responseType: 'blob',
    }
  );

  let filename = `AudioSleuth_Comparison_${request.evidence_id_a}_vs_${request.evidence_id_b}.pdf`;
  const disposition = response.headers['content-disposition'];
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename="?([^";]+)"?/);
    if (match && match[1]) {
      filename = match[1].trim();
    }
  }

  const blobUrl = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
  const link = document.createElement('a');
  link.href = blobUrl;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(blobUrl);
}
