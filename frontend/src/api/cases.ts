/**
 * Case management and evidence intake API functions.
 */

import { apiClient } from './client';
import type {
  ForensicCase,
  CaseCreatePayload,
  CaseUpdatePayload,
  EvidenceItem,
  AuditListResponse,
} from '../types';

export async function createCase(payload: CaseCreatePayload): Promise<ForensicCase> {
  const response = await apiClient.post<ForensicCase>('/v1/cases', payload);
  return response.data;
}

export async function listCases(status?: string): Promise<{ cases: ForensicCase[]; total: number }> {
  const params = status && status !== 'all' ? { status } : {};
  const response = await apiClient.get<{ cases: ForensicCase[]; total: number }>('/v1/cases', { params });
  return response.data;
}

export async function getCase(caseId: string): Promise<ForensicCase> {
  const response = await apiClient.get<ForensicCase>(`/v1/cases/${encodeURIComponent(caseId)}`);
  return response.data;
}

export async function updateCase(caseId: string, payload: CaseUpdatePayload): Promise<ForensicCase> {
  const response = await apiClient.patch<ForensicCase>(`/v1/cases/${encodeURIComponent(caseId)}`, payload);
  return response.data;
}

export async function updateCaseStatus(
  caseId: string,
  status: 'active' | 'closed',
  reason?: string
): Promise<ForensicCase> {
  const response = await apiClient.post<ForensicCase>(
    `/v1/cases/${encodeURIComponent(caseId)}/status`,
    { status, reason }
  );
  return response.data;
}

export async function getCaseAudit(
  caseId: string,
  limit: number = 100,
  offset: number = 0
): Promise<AuditListResponse> {
  const response = await apiClient.get<AuditListResponse>(
    `/v1/cases/${encodeURIComponent(caseId)}/audit`,
    { params: { limit, offset } }
  );
  return response.data;
}


export async function uploadEvidence(
  caseId: string,
  file: File,
  onProgress?: (percent: number) => void
): Promise<EvidenceItem> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<EvidenceItem>(
    `/v1/cases/${encodeURIComponent(caseId)}/evidence`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    }
  );

  return response.data;
}

export async function listCaseEvidence(
  caseId: string
): Promise<{ case_id: string; items: EvidenceItem[]; total: number }> {
  const response = await apiClient.get<{ case_id: string; items: EvidenceItem[]; total: number }>(
    `/v1/cases/${encodeURIComponent(caseId)}/evidence`
  );
  return response.data;
}
