/**
 * Evidence details and integrity verification API functions.
 */

import { apiClient } from './client';
import type { EvidenceItem, IntegrityVerificationResult } from '../types';

export async function getEvidence(evidenceId: string): Promise<EvidenceItem> {
  const response = await apiClient.get<EvidenceItem>(`/v1/evidence/${encodeURIComponent(evidenceId)}`);
  return response.data;
}

export async function verifyEvidenceIntegrity(
  evidenceId: string
): Promise<IntegrityVerificationResult> {
  const response = await apiClient.post<IntegrityVerificationResult>(
    `/v1/evidence/${encodeURIComponent(evidenceId)}/verify-integrity`
  );
  return response.data;
}
