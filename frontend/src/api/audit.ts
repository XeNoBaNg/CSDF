/**
 * Forensic audit trail API client.
 */

import { apiClient } from './client';
import type { AuditEvent, AuditListResponse } from '../types';

export interface AuditQueryParams {
  case_id?: string;
  evidence_id?: string;
  action?: string;
  limit?: number;
  offset?: number;
}

export async function listAuditEvents(params?: AuditQueryParams): Promise<AuditListResponse> {
  const response = await apiClient.get<AuditListResponse>('/v1/audit', { params });
  return response.data;
}

export async function getAuditEvent(eventId: string): Promise<AuditEvent> {
  const response = await apiClient.get<AuditEvent>(`/v1/audit/${encodeURIComponent(eventId)}`);
  return response.data;
}
