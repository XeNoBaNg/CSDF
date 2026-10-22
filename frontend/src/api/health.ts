/**
 * Health and diagnostics API calls.
 */

import { apiClient } from './client';
import type { HealthCheckResponse } from '../types';

export async function fetchHealthStatus(): Promise<HealthCheckResponse> {
  const response = await apiClient.get<HealthCheckResponse>('/health');
  return response.data;
}
