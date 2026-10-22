/**
 * API client functions for downloading forensic PDF reports.
 */

import { apiClient } from './client';

export interface ReportDownloadOptions {
  include_visualizations?: boolean;
  include_audit?: boolean;
  run_analysis?: boolean;
  notes?: string;
}

/**
 * Downloads a forensic examination PDF report for the specified evidence item.
 * Triggers standard browser file download with the server-supplied filename.
 */
export async function downloadEvidenceReport(
  evidenceId: string,
  options?: ReportDownloadOptions
): Promise<void> {
  const params: Record<string, string | boolean> = {};
  if (options?.include_visualizations !== undefined) {
    params.include_visualizations = options.include_visualizations;
  }
  if (options?.include_audit !== undefined) {
    params.include_audit = options.include_audit;
  }
  if (options?.run_analysis !== undefined) {
    params.run_analysis = options.run_analysis;
  }
  if (options?.notes) {
    params.notes = options.notes;
  }

  const response = await apiClient.get<Blob>(
    `/v1/evidence/${encodeURIComponent(evidenceId)}/report`,
    {
      params,
      responseType: 'blob',
    }
  );

  // Extract filename from Content-Disposition header if available
  let filename = `AudioSleuth_Forensic_Report_${evidenceId}.pdf`;
  const disposition = response.headers['content-disposition'];
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename="?([^";]+)"?/);
    if (match && match[1]) {
      filename = match[1].trim();
    }
  }

  // Create temporary anchor to trigger browser download
  const blobUrl = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
  const link = document.createElement('a');
  link.href = blobUrl;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();

  // Cleanup
  link.remove();
  window.URL.revokeObjectURL(blobUrl);
}
