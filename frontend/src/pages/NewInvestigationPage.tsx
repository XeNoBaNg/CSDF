import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  FolderPlus,
  ArrowLeft,
  UploadCloud,
  FileCheck2,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Check,
  ShieldCheck,
  KeyRound,
  FileAudio,
  FolderOpen,
  RefreshCw,
  HardDrive,
  Info,
  AudioLines,
  ArrowRight,
  Lock,
  Unlock,
  FileDown,
} from 'lucide-react';
import { createCase, listCases, uploadEvidence, listCaseEvidence, updateCaseStatus } from '../api/cases';
import { verifyEvidenceIntegrity } from '../api/evidence';
import { downloadEvidenceReport } from '../api/reports';
import { StatusBadge } from '../components/common/StatusBadge';
import type {
  ForensicCase,
  EvidenceItem,
  IntegrityVerificationResult,
} from '../types';

export const NewInvestigationPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedCaseId = searchParams.get('caseId');

  // Case Management State
  const [existingCases, setExistingCases] = useState<ForensicCase[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>(preselectedCaseId || '');
  const [caseMode, setCaseMode] = useState<'create' | 'select'>('create');
  const [caseTitle, setCaseTitle] = useState('');
  const [investigatorName, setInvestigatorName] = useState('');
  const [caseNotes, setCaseNotes] = useState('');
  const [activeCase, setActiveCase] = useState<ForensicCase | null>(null);
  const [caseLoading, setCaseLoading] = useState(false);
  const [caseError, setCaseError] = useState<string | null>(null);

  // Attached Case Evidence State
  const [caseEvidenceList, setCaseEvidenceList] = useState<EvidenceItem[]>([]);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [verifyingEvidenceId, setVerifyingEvidenceId] = useState<string | null>(null);
  const [itemVerificationResults, setItemVerificationResults] = useState<Record<string, IntegrityVerificationResult>>({});

  // Evidence Intake State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadedEvidence, setUploadedEvidence] = useState<EvidenceItem | null>(null);

  // Integrity Verification State
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<IntegrityVerificationResult | null>(null);
  const [copiedHash, setCopiedHash] = useState(false);

  // Forensic PDF Report State
  const [downloadingReportId, setDownloadingReportId] = useState<string | null>(null);
  const [reportDownloadError, setReportDownloadError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load case evidence items
  const loadCaseEvidence = useCallback(async (caseId: string) => {
    setEvidenceLoading(true);
    try {
      const data = await listCaseEvidence(caseId);
      setCaseEvidenceList(data.items);
    } catch (err) {
      console.warn('Failed to load case evidence items:', err);
    } finally {
      setEvidenceLoading(false);
    }
  }, []);

  // Load existing cases on mount
  const loadCases = useCallback(async () => {
    try {
      const data = await listCases();
      setExistingCases(data.cases);
      if (preselectedCaseId) {
        const found = data.cases.find((c) => c.id === preselectedCaseId);
        if (found) {
          setActiveCase(found);
          setSelectedCaseId(found.id);
          setCaseMode('select');
        }
      } else if (data.cases.length > 0 && caseMode === 'select' && !selectedCaseId) {
        setSelectedCaseId(data.cases[0].id);
        setActiveCase(data.cases[0]);
      }
    } catch (err) {
      console.warn('Failed to load existing cases:', err);
    }
  }, [preselectedCaseId, caseMode, selectedCaseId]);

  useEffect(() => {
    loadCases();
  }, [loadCases]);

  // Load evidence whenever activeCase changes
  useEffect(() => {
    if (activeCase?.id) {
      loadCaseEvidence(activeCase.id);
    } else {
      setCaseEvidenceList([]);
    }
  }, [activeCase?.id, loadCaseEvidence]);

  // Handle case selection change
  const handleSelectCaseChange = (id: string) => {
    setSelectedCaseId(id);
    const found = existingCases.find((c) => c.id === id);
    setActiveCase(found || null);
    // Reset evidence states
    setSelectedFile(null);
    setUploadedEvidence(null);
    setVerificationResult(null);
    setUploadError(null);
  };

  // Handle case status toggle (close / reopen)
  const handleToggleCaseStatus = async () => {
    if (!activeCase) return;
    const targetStatus = activeCase.status === 'active' ? 'closed' : 'active';
    const reason =
      targetStatus === 'closed'
        ? 'Examiner marked case as closed'
        : 'Examiner reopened case for further examination';

    try {
      const updated = await updateCaseStatus(activeCase.id, targetStatus, reason);
      setActiveCase(updated);
      setExistingCases((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } catch (err: unknown) {
      const errorMsg =
        (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data
          ?.error?.message || 'Failed to update case status.';
      setCaseError(errorMsg);
    }
  };

  // Handle verifying individual item in list
  const handleVerifyItem = async (evidenceId: string) => {
    setVerifyingEvidenceId(evidenceId);
    try {
      const result = await verifyEvidenceIntegrity(evidenceId);
      setItemVerificationResults((prev) => ({ ...prev, [evidenceId]: result }));
    } catch (err) {
      console.error('Integrity check failed for item:', evidenceId, err);
    } finally {
      setVerifyingEvidenceId(null);
    }
  };

  // Handle generating & downloading forensic PDF report
  const handleDownloadReport = async (evidenceId: string) => {
    setDownloadingReportId(evidenceId);
    setReportDownloadError(null);
    try {
      await downloadEvidenceReport(evidenceId);
    } catch (err: unknown) {
      const errorMsg =
        (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data
          ?.error?.message || (err as Error)?.message || 'Failed to generate forensic PDF report.';
      setReportDownloadError(`Report Generation Error (${evidenceId}): ${errorMsg}`);
    } finally {
      setDownloadingReportId(null);
    }
  };

  // Handle creating a new case
  const handleCreateCaseSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCaseError(null);
    setCaseLoading(true);

    try {
      const newCase = await createCase({
        title: caseTitle,
        investigator_name: investigatorName,
        notes: caseNotes,
      });
      setActiveCase(newCase);
      setSelectedCaseId(newCase.id);
      setExistingCases((prev) => [newCase, ...prev]);
      setCaseMode('select');
    } catch (err: unknown) {
      const errorMsg =
        (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data
          ?.error?.message || 'Failed to initialize forensic case record.';
      setCaseError(errorMsg);
    } finally {
      setCaseLoading(false);
    }
  };

  // File selection & drop validation
  const handleFileChange = (file: File | null) => {
    setUploadError(null);
    setUploadedEvidence(null);
    setVerificationResult(null);

    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (activeCase?.status === 'closed') {
      setUploadError('Evidence intake is locked because this case is marked as CLOSED. Reopen case first.');
      setSelectedFile(null);
      return;
    }

    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !['wav', 'mp3', 'flac'].includes(ext)) {
      setUploadError(`Unsupported format (.${ext || 'unknown'}). AudioSleuth currently accepts: WAV, MP3, FLAC.`);
      setSelectedFile(null);
      return;
    }

    const maxBytes = 100 * 1024 * 1024; // 100 MB
    if (file.size > maxBytes) {
      setUploadError(`Selected file exceeds the 100 MB limit (${(file.size / (1024 * 1024)).toFixed(1)} MB).`);
      setSelectedFile(null);
      return;
    }

    if (file.size === 0) {
      setUploadError('Selected file is empty (0 bytes).');
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  // Handle file drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (activeCase?.status !== 'closed') {
      setIsDragging(true);
    }
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (activeCase?.status === 'closed') {
      setUploadError('Evidence intake is locked because this case is marked as CLOSED. Reopen case first.');
      return;
    }
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  // Execute Evidence Upload
  const handleUploadSubmit = async () => {
    if (!activeCase || !selectedFile) return;

    if (activeCase.status === 'closed') {
      setUploadError('Cannot upload evidence: case is CLOSED.');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setUploadError(null);
    setVerificationResult(null);

    try {
      const evidence = await uploadEvidence(activeCase.id, selectedFile, (percent) => {
        setUploadProgress(percent);
      });
      setUploadedEvidence(evidence);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      // Update case evidence count and reload evidence items
      setActiveCase((prev) => (prev ? { ...prev, evidence_count: prev.evidence_count + 1 } : null));
      loadCases();
      if (activeCase?.id) {
        loadCaseEvidence(activeCase.id);
      }
    } catch (err: unknown) {
      const errorMsg =
        (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data
          ?.error?.message || 'Failed to ingest evidence recording.';
      setUploadError(errorMsg);
    } finally {
      setIsUploading(false);
      setUploadProgress(null);
    }
  };

  // Execute Integrity Verification
  const handleRunVerification = async () => {
    if (!uploadedEvidence) return;
    setIsVerifying(true);
    try {
      const result = await verifyEvidenceIntegrity(uploadedEvidence.id);
      setVerificationResult(result);
    } catch (err: unknown) {
      console.error('Integrity verification probe failed:', err);
    } finally {
      setIsVerifying(false);
    }
  };

  const copyHashToClipboard = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Navigation Breadcrumb */}
      <div>
        <button
          type="button"
          onClick={() => navigate('/')}
          className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Workstation Dashboard</span>
        </button>
      </div>

      {/* Case Management Card */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <FolderPlus className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">Step 1: Case Association</h2>
              <p className="text-xs text-slate-400">
                Bind audio evidence items to an existing or new forensic investigation record
              </p>
            </div>
          </div>

          {/* Mode Switcher */}
          {existingCases.length > 0 && (
            <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs self-start">
              <button
                type="button"
                onClick={() => setCaseMode('create')}
                className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                  caseMode === 'create'
                    ? 'bg-cyan-600 text-white shadow-xs'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Create New Case
              </button>
              <button
                type="button"
                onClick={() => {
                  setCaseMode('select');
                  if (!activeCase && existingCases.length > 0) {
                    handleSelectCaseChange(existingCases[0].id);
                  }
                }}
                className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                  caseMode === 'select'
                    ? 'bg-cyan-600 text-white shadow-xs'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Select Existing Case ({existingCases.length})
              </button>
            </div>
          )}
        </div>

        {caseError && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{caseError}</span>
          </div>
        )}

        {/* Existing Case Selector */}
        {caseMode === 'select' && existingCases.length > 0 ? (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="caseSelect" className="block text-xs font-semibold text-slate-300">
                Select Active Investigation Case
              </label>
              <select
                id="caseSelect"
                value={selectedCaseId}
                onChange={(e) => handleSelectCaseChange(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-sm text-slate-100 focus:outline-none focus:border-cyan-500"
              >
                {existingCases.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title} — ({c.id}) [Investigator: {c.investigator_name}]
                  </option>
                ))}
              </select>
            </div>

            {activeCase && (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-bold text-slate-200">{activeCase.title}</span>
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                        {activeCase.id}
                      </span>
                      <span
                        className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                          activeCase.status === 'closed'
                            ? 'bg-amber-950/30 text-amber-300 border-amber-500/30'
                            : 'bg-emerald-950/30 text-emerald-300 border-emerald-500/30'
                        }`}
                      >
                        {activeCase.status === 'closed' ? (
                          <Lock className="w-2.5 h-2.5" />
                        ) : (
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                        )}
                        <span>{activeCase.status}</span>
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">
                      Lead Examiner: <span className="text-slate-300">{activeCase.investigator_name}</span> • Attached Evidence: <span className="text-slate-300">{caseEvidenceList.length || activeCase.evidence_count} file(s)</span>
                    </p>
                    {(activeCase.description || activeCase.notes) && (
                      <p className="text-[11px] text-slate-400 italic">
                        Notes: {activeCase.description || activeCase.notes}
                      </p>
                    )}
                  </div>

                  <div className="shrink-0 flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleToggleCaseStatus}
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                        activeCase.status === 'active'
                          ? 'bg-amber-500/10 hover:bg-amber-500/20 border-amber-500/30 text-amber-300'
                          : 'bg-emerald-500/10 hover:bg-emerald-500/20 border-emerald-500/30 text-emerald-300'
                      }`}
                    >
                      {activeCase.status === 'active' ? (
                        <>
                          <Lock className="w-3.5 h-3.5" />
                          <span>Close Case</span>
                        </>
                      ) : (
                        <>
                          <Unlock className="w-3.5 h-3.5" />
                          <span>Reopen Case</span>
                        </>
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={() => navigate('/cases')}
                      className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-medium text-slate-300 transition-colors"
                    >
                      Registry
                    </button>
                  </div>
                </div>

                {activeCase.status === 'closed' && (
                  <div className="p-3 rounded-lg bg-amber-950/30 border border-amber-500/30 text-amber-200 text-xs flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <Lock className="w-4 h-4 text-amber-400 shrink-0" />
                      <span>
                        <strong>Case Closed:</strong> Evidence acquisition is locked under digital custody rules. Reopen this case to ingest additional recordings.
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={handleToggleCaseStatus}
                      className="shrink-0 px-3 py-1 rounded-md bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs shadow-xs transition-colors"
                    >
                      Reopen
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          /* Create Case Form */
          <form onSubmit={handleCreateCaseSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label htmlFor="caseTitle" className="block text-xs font-semibold text-slate-300">
                  Case Title / Reference <span className="text-rose-400">*</span>
                </label>
                <input
                  id="caseTitle"
                  type="text"
                  required
                  placeholder="e.g. CSDF-2026-CASE-001"
                  value={caseTitle}
                  onChange={(e) => setCaseTitle(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-slate-100 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="investigatorName" className="block text-xs font-semibold text-slate-300">
                  Lead Examiner <span className="text-rose-400">*</span>
                </label>
                <input
                  id="investigatorName"
                  type="text"
                  required
                  placeholder="e.g. PICT Forensic Investigator"
                  value={investigatorName}
                  onChange={(e) => setInvestigatorName(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-slate-100 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="caseNotes" className="block text-xs font-semibold text-slate-300">
                Investigation Notes & Circumstances
              </label>
              <textarea
                id="caseNotes"
                rows={2}
                placeholder="Initial investigative hypothesis, chain-of-custody transfer note, or suspected manipulation..."
                value={caseNotes}
                onChange={(e) => setCaseNotes(e.target.value)}
                className="w-full px-3.5 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-slate-100 focus:outline-none focus:border-cyan-500 resize-none"
              />
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={caseLoading}
                className="inline-flex items-center gap-2 px-5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-xs disabled:opacity-50 transition-colors"
              >
                {caseLoading ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <FolderOpen className="w-4 h-4" />
                )}
                <span>Initialize Case</span>
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Step 2: Evidence Acquisition Dropzone (Enabled when Case is Active) */}
      <div className={`p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-5 transition-opacity ${
        activeCase ? 'opacity-100' : 'opacity-50 pointer-events-none'
      }`}>
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <HardDrive className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">Step 2: Evidence Acquisition & Intake</h2>
              <p className="text-xs text-slate-400">
                Upload digital audio recording into isolated storage with immutable SHA-256 digest computation
              </p>
            </div>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            WAV • MP3 • FLAC (≤ 100 MB)
          </span>
        </div>

        {uploadError && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}

        {/* Drag and Drop Box or Locked State */}
        {activeCase?.status === 'closed' ? (
          <div className="border-2 border-dashed border-amber-500/30 rounded-xl p-8 text-center bg-slate-950/40 flex flex-col items-center justify-center">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-3 shadow-inner">
              <Lock className="w-6 h-6" />
            </div>
            <p className="text-sm font-semibold text-slate-200">
              Evidence Acquisition Locked (Case Closed)
            </p>
            <p className="text-xs text-slate-400 max-w-sm mt-1">
              In accordance with digital forensic evidence integrity rules, recordings cannot be ingested into a closed case. Reopen the case record above to proceed.
            </p>
            <button
              type="button"
              onClick={handleToggleCaseStatus}
              className="mt-4 inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-xs font-semibold text-white shadow-xs transition-colors"
            >
              <Unlock className="w-3.5 h-3.5" />
              <span>Reopen Case for Ingestion</span>
            </button>
          </div>
        ) : (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-150 flex flex-col items-center justify-center ${
              isDragging
                ? 'border-cyan-400 bg-cyan-500/10 scale-[1.01]'
                : 'border-slate-800 hover:border-slate-700 bg-slate-950/40'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".wav,.mp3,.flac"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  handleFileChange(e.target.files[0]);
                }
              }}
            />

            <div className="w-12 h-12 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-cyan-400 mb-3 shadow-inner">
              <UploadCloud className="w-6 h-6" />
            </div>

            <p className="text-sm font-semibold text-slate-200">
              {selectedFile ? selectedFile.name : 'Choose audio evidence file or drag and drop here'}
            </p>
            <p className="text-xs text-slate-400 max-w-sm mt-1">
              {selectedFile
                ? `${formatBytes(selectedFile.size)} • Ready for cryptographic intake`
                : 'Strict binary magic number validation is enforced on server. Original evidence remains unchanged.'}
            </p>

            <button
              type="button"
              className="mt-4 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-300 transition-colors"
            >
              Browse Local File
            </button>
          </div>
        )}

        {/* Upload Action Button & Progress */}
        {selectedFile && (
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-slate-950 border border-slate-800">
            <div className="flex items-center gap-3">
              <FileAudio className="w-5 h-5 text-cyan-400 shrink-0" />
              <div>
                <p className="text-xs font-semibold text-slate-200">{selectedFile.name}</p>
                <p className="text-[11px] text-slate-400">{formatBytes(selectedFile.size)}</p>
              </div>
            </div>

            <button
              type="button"
              onClick={handleUploadSubmit}
              disabled={isUploading}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-xs disabled:opacity-50 transition-colors self-start"
            >
              {isUploading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Ingesting Evidence... {uploadProgress !== null ? `${uploadProgress}%` : ''}</span>
                </>
              ) : (
                <>
                  <FileCheck2 className="w-4 h-4" />
                  <span>Ingest & Compute SHA-256</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Forensic Principle Disclaimer */}
        <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 flex items-start gap-2.5 text-xs text-slate-400">
          <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong className="text-slate-300">Evidence Handling Guarantee:</strong> AudioSleuth streams the file to compute SHA-256 without unbounded memory allocation and saves original bytes untouched. Decoders and signal algorithms in Phase 3/4 operate exclusively on working copies.
          </p>
        </div>
      </div>

      {/* Step 3: Ingested Evidence Details & Live Integrity Verification */}
      {uploadedEvidence && (
        <div className="p-6 rounded-2xl bg-slate-900 border border-cyan-500/30 space-y-6 shadow-lg shadow-cyan-950/20">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-100">Evidence Ingested & Registered</h3>
                <p className="text-xs text-slate-400">
                  Item successfully committed to evidence vault with cryptographic custody record
                </p>
              </div>
            </div>
            <StatusBadge status="verified" pulse />
          </div>

          {/* Registered Metadata Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-slate-400 block text-[11px] font-sans">Evidence Identifier</span>
              <span className="text-cyan-400 font-bold">{uploadedEvidence.id}</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-slate-400 block text-[11px] font-sans">Original Filename</span>
              <span className="text-slate-200 truncate block" title={uploadedEvidence.original_filename}>
                {uploadedEvidence.original_filename}
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-slate-400 block text-[11px] font-sans">File Size & Media Type</span>
              <span className="text-slate-200">
                {formatBytes(uploadedEvidence.file_size_bytes)} ({uploadedEvidence.file_size_bytes} B) • {uploadedEvidence.mime_type}
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-slate-400 block text-[11px] font-sans">Ingestion Timestamp (UTC)</span>
              <span className="text-slate-200">{uploadedEvidence.ingested_at}</span>
            </div>
          </div>

          {/* SHA-256 Digest Card */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5 font-sans">
                <KeyRound className="w-3.5 h-3.5 text-emerald-400" />
                Intake Cryptographic Hash (SHA-256)
              </span>
              <button
                type="button"
                onClick={() => copyHashToClipboard(uploadedEvidence.sha256_hash)}
                className="inline-flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300 font-sans transition-colors"
              >
                {copiedHash ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy Hash</span>
                  </>
                )}
              </button>
            </div>
            <p className="font-mono text-xs text-emerald-300 bg-slate-900/90 p-2.5 rounded-lg border border-slate-800 break-all select-all">
              {uploadedEvidence.sha256_hash}
            </p>
          </div>

          {/* Phase 3: Launch Audio Inspection Workspace CTA */}
          <div className="p-4 rounded-xl bg-gradient-to-r from-cyan-950/40 to-slate-900 border border-cyan-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <h4 className="text-xs font-bold text-slate-100 flex items-center gap-2">
                <AudioLines className="w-4 h-4 text-cyan-400" />
                <span>Forensic Audio Inspection & Signal Visualizer</span>
              </h4>
              <p className="text-[11px] text-slate-400">
                Inspect decoded waveform envelopes, STFT time-frequency spectrograms, FFT power spectra, and embedded audio tags.
              </p>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto shrink-0 flex-wrap">
              <button
                type="button"
                onClick={() => handleDownloadReport(uploadedEvidence.id)}
                disabled={downloadingReportId === uploadedEvidence.id}
                className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold shadow-md transition-all disabled:opacity-50"
                title="Generate and download forensic PDF report"
              >
                <FileDown className={`w-4 h-4 ${downloadingReportId === uploadedEvidence.id ? 'animate-bounce text-cyan-400' : 'text-cyan-400'}`} />
                <span>{downloadingReportId === uploadedEvidence.id ? 'Exporting PDF...' : 'Export PDF Report'}</span>
              </button>

              <button
                type="button"
                onClick={() => navigate(`/evidence/${encodeURIComponent(uploadedEvidence.id)}`)}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md transition-all"
              >
                <span>Inspect Audio & Signal</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Verification CTA Button */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
            <div>
              <h4 className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-cyan-400" />
                Live Integrity Re-Verification Probe
              </h4>
              <p className="text-[11px] text-slate-400">
                Recalculates SHA-256 from physical storage on disk and checks for byte-level alteration
              </p>
            </div>

            <button
              type="button"
              onClick={handleRunVerification}
              disabled={isVerifying}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 shadow-xs transition-colors self-start disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isVerifying ? 'animate-spin' : ''}`} />
              <span>Verify Stored Hash</span>
            </button>
          </div>

          {/* Verification Probe Output */}
          {verificationResult && (
            <div
              className={`p-4 rounded-xl border space-y-3 ${
                verificationResult.status === 'match'
                  ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                  : verificationResult.status === 'mismatch'
                  ? 'bg-rose-950/20 border-rose-500/30 text-rose-300'
                  : 'bg-amber-950/20 border-amber-500/30 text-amber-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold font-sans">Verification Result:</span>
                  <StatusBadge
                    status={
                      verificationResult.status === 'match'
                        ? 'Pristine Byte Match'
                        : verificationResult.status === 'mismatch'
                        ? 'CRITICAL TAMPERING'
                        : 'Unverifiable'
                    }
                    variant={
                      verificationResult.status === 'match'
                        ? 'healthy'
                        : verificationResult.status === 'mismatch'
                        ? 'unhealthy'
                        : 'warning'
                    }
                  />
                </div>
                <span className="text-[11px] font-mono text-slate-400">
                  {verificationResult.verified_at}
                </span>
              </div>

              <div className="space-y-1.5 text-xs font-mono bg-slate-950/80 p-3 rounded-lg border border-slate-800">
                <div className="flex flex-col sm:flex-row sm:justify-between text-slate-400 gap-1">
                  <span>Intake Expected Hash:</span>
                  <span className="text-slate-200 break-all">{verificationResult.expected_sha256}</span>
                </div>
                <div className="flex flex-col sm:flex-row sm:justify-between text-slate-400 gap-1">
                  <span>Storage Recalculated:</span>
                  <span
                    className={`break-all ${
                      verificationResult.status === 'match'
                        ? 'text-emerald-400'
                        : 'text-rose-400 font-bold'
                    }`}
                  >
                    {verificationResult.calculated_sha256 || 'N/A (File missing)'}
                  </span>
                </div>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                {verificationResult.explanation}
              </p>

              <p className="text-[11px] text-slate-400 italic font-sans border-t border-slate-800/60 pt-2">
                {verificationResult.disclaimer}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Attached Evidence Items Belonging to Case */}
      {activeCase && (
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2.5">
              <HardDrive className="w-5 h-5 text-cyan-400" />
              <div>
                <h3 className="text-sm font-bold text-slate-100">
                  Case Evidence Vault ({caseEvidenceList.length})
                </h3>
                <p className="text-xs text-slate-400">
                  Durable recordings preserved for case <span className="font-mono text-cyan-400">{activeCase.id}</span>
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => loadCaseEvidence(activeCase.id)}
              disabled={evidenceLoading}
              className="p-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
              title="Refresh evidence list"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${evidenceLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {reportDownloadError && (
            <div className="p-3 rounded-lg bg-rose-950/30 border border-rose-500/30 flex items-center justify-between text-xs text-rose-300">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
                <span>{reportDownloadError}</span>
              </div>
              <button
                type="button"
                onClick={() => setReportDownloadError(null)}
                className="text-slate-400 hover:text-slate-200 text-sm font-bold"
              >
                ✕
              </button>
            </div>
          )}

          {evidenceLoading && caseEvidenceList.length === 0 ? (
            <div className="py-6 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
              <span>Querying attached evidence records...</span>
            </div>
          ) : caseEvidenceList.length === 0 ? (
            <div className="py-8 text-center space-y-1">
              <p className="text-xs text-slate-400">No audio evidence recordings attached to this case yet.</p>
              <p className="text-[11px] text-slate-400">
                {activeCase.status === 'closed'
                  ? 'Case is closed. Reopen it above to acquire new evidence.'
                  : 'Use Step 2 above to ingest audio files into this case.'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {caseEvidenceList.map((item) => {
                const itemRes = itemVerificationResults[item.id];
                const isItemVerifying = verifyingEvidenceId === item.id;
                const isItemExporting = downloadingReportId === item.id;

                return (
                  <div
                    key={item.id}
                    className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-3"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-slate-900 text-cyan-400 border border-slate-800 mt-0.5">
                          <FileAudio className="w-4 h-4" />
                        </div>
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-slate-200">{item.original_filename}</span>
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                              {item.id}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 font-mono">
                            {formatBytes(item.file_size_bytes)} • {item.mime_type} • Ingested: {item.ingested_at.split('T')[0]}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
                        <button
                          type="button"
                          onClick={() => handleDownloadReport(item.id)}
                          disabled={isItemExporting}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-medium text-slate-300 transition-colors disabled:opacity-50"
                          title="Generate and download forensic PDF report"
                        >
                          <FileDown className={`w-3.5 h-3.5 ${isItemExporting ? 'animate-bounce text-cyan-400' : 'text-cyan-400'}`} />
                          <span>{isItemExporting ? 'Exporting...' : 'PDF Report'}</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => handleVerifyItem(item.id)}
                          disabled={isItemVerifying}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-medium text-slate-300 transition-colors disabled:opacity-50"
                        >
                          <ShieldCheck className={`w-3.5 h-3.5 ${isItemVerifying ? 'animate-spin text-cyan-400' : 'text-emerald-400'}`} />
                          <span>{isItemVerifying ? 'Verifying...' : 'Verify Hash'}</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => navigate(`/evidence/${encodeURIComponent(item.id)}`)}
                          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-xs transition-colors"
                        >
                          <AudioLines className="w-3.5 h-3.5" />
                          <span>Inspect Workspace</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Monospace SHA-256 with copy */}
                    <div className="flex items-center justify-between bg-slate-900/80 px-3 py-2 rounded-lg border border-slate-800/80 text-[11px] font-mono text-slate-300">
                      <span className="truncate pr-2">
                        <span className="text-slate-400 select-none">SHA-256: </span>
                        {item.sha256_hash}
                      </span>
                      <button
                        type="button"
                        onClick={() => copyHashToClipboard(item.sha256_hash)}
                        className="text-cyan-400 hover:text-cyan-300 shrink-0 font-sans text-[11px] inline-flex items-center gap-1"
                      >
                        <Copy className="w-3 h-3" />
                        <span>Copy</span>
                      </button>
                    </div>

                    {/* Inline verification result if requested */}
                    {itemRes && (
                      <div
                        className={`p-3 rounded-lg border text-xs ${
                          itemRes.status === 'match'
                            ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                            : 'bg-rose-950/20 border-rose-500/30 text-rose-300'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold">
                            {itemRes.status === 'match'
                              ? '✓ Storage Byte Integrity Verified (Match)'
                              : '✗ Discrepancy Detected (Tampered / Missing)'}
                          </span>
                          <span className="font-mono text-[10px] text-slate-400">{itemRes.verified_at}</span>
                        </div>
                        {itemRes.disclaimer && (
                          <p className="text-[10px] text-slate-400 mt-1 italic">{itemRes.disclaimer}</p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

