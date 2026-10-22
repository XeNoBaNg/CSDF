import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FolderArchive,
  Plus,
  Search,
  ShieldCheck,
  Calendar,
  User,
  HardDrive,
  ArrowRight,
  RefreshCw,
  Edit3,
  Lock,
  Unlock,
  History,
  X,
  CheckCircle2,
  AlertCircle,
  Check,
} from 'lucide-react';
import { listCases, updateCase, updateCaseStatus, getCaseAudit } from '../api/cases';
import { EmptyState } from '../components/common/EmptyState';
import type { ForensicCase, AuditEvent, CaseUpdatePayload } from '../types';

export const CaseHistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [cases, setCases] = useState<ForensicCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'closed'>('all');

  // Edit Case Modal State
  const [editingCase, setEditingCase] = useState<ForensicCase | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editInvestigator, setEditInvestigator] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  // Audit Trail Modal State
  const [auditCase, setAuditCase] = useState<ForensicCase | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditDisclaimer, setAuditDisclaimer] = useState<string>('');

  const fetchCases = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listCases(statusFilter);
      setCases(data.cases);
    } catch (err) {
      console.warn('Failed to fetch case list:', err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  // Status transition handler
  const handleToggleStatus = async (e: React.MouseEvent, c: ForensicCase) => {
    e.stopPropagation();
    const targetStatus = c.status === 'active' ? 'closed' : 'active';
    const reason =
      targetStatus === 'closed'
        ? 'Examiner marked case as closed'
        : 'Examiner reopened case for further examination';

    try {
      const updated = await updateCaseStatus(c.id, targetStatus, reason);
      setCases((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err) {
      console.error('Failed to update case status:', err);
    }
  };

  // Open Edit Modal
  const handleOpenEdit = (e: React.MouseEvent, c: ForensicCase) => {
    e.stopPropagation();
    setEditingCase(c);
    setEditTitle(c.title);
    setEditInvestigator(c.investigator_name);
    setEditDescription(c.description || c.notes || '');
    setEditError(null);
  };

  // Save Edit Metadata
  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCase) return;

    setIsUpdating(true);
    setEditError(null);

    const payload: CaseUpdatePayload = {
      title: editTitle.trim(),
      investigator_name: editInvestigator.trim(),
      description: editDescription.trim(),
      notes: editDescription.trim(),
    };

    try {
      const updated = await updateCase(editingCase.id, payload);
      setCases((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      setEditingCase(null);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data
          ?.error?.message || 'Failed to update case metadata.';
      setEditError(msg);
    } finally {
      setIsUpdating(false);
    }
  };

  // Open Audit Modal
  const handleOpenAudit = async (e: React.MouseEvent, c: ForensicCase) => {
    e.stopPropagation();
    setAuditCase(c);
    setAuditLoading(true);
    try {
      const res = await getCaseAudit(c.id);
      setAuditEvents(res.items);
      setAuditDisclaimer(res.disclaimer || '');
    } catch (err) {
      console.error('Failed to load case audit trail:', err);
    } finally {
      setAuditLoading(false);
    }
  };

  const filteredCases = cases.filter((c) => {
    const matchesSearch =
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.investigator_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const activeCount = cases.filter((c) => c.status === 'active').length;
  const closedCount = cases.filter((c) => c.status === 'closed').length;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <FolderArchive className="w-5 h-5 text-cyan-400" />
            <span>Forensic Case Registry & Lifecycle</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Durable SQLite persistence for case metadata, evidence relationships, and structured audit logs
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            type="button"
            onClick={fetchCases}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 hover:bg-slate-800 transition-colors"
            title="Refresh case list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            type="button"
            onClick={() => navigate('/cases/new')}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-xs transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>New Investigation</span>
          </button>
        </div>
      </div>

      {/* Filter Tabs and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-900 border border-slate-800">
        {/* Status Tabs */}
        <div className="flex items-center gap-1.5 text-xs">
          <button
            type="button"
            onClick={() => setStatusFilter('all')}
            className={`px-3 py-1 rounded-lg font-medium transition-colors ${
              statusFilter === 'all'
                ? 'bg-slate-800 text-slate-100 border border-slate-700'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All Cases ({cases.length})
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter('active')}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg font-medium transition-colors ${
              statusFilter === 'active'
                ? 'bg-emerald-950/40 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
            <span>Active ({activeCount})</span>
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter('closed')}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg font-medium transition-colors ${
              statusFilter === 'closed'
                ? 'bg-slate-800/80 text-amber-300 border border-amber-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Lock className="w-3 h-3 text-amber-400" />
            <span>Closed ({closedCount})</span>
          </button>
        </div>

        {/* Search input */}
        <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-lg px-3 py-1 text-xs w-full sm:w-72">
          <Search className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search title, ID, investigator..."
            className="bg-transparent text-slate-200 placeholder:text-slate-400 w-full focus:outline-none"
          />
          {searchQuery && (
            <button type="button" onClick={() => setSearchQuery('')} className="text-slate-500 hover:text-slate-300">
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Case List or Empty State */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 text-xs flex flex-col items-center justify-center gap-2">
          <RefreshCw className="w-5 h-5 animate-spin text-cyan-400" />
          <span>Querying SQLite Case Registry & Audit Tables...</span>
        </div>
      ) : filteredCases.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredCases.map((c) => {
            const isClosed = c.status === 'closed';

            return (
              <div
                key={c.id}
                onClick={() => navigate(`/cases/new?caseId=${encodeURIComponent(c.id)}`)}
                className={`p-5 rounded-2xl border transition-all duration-150 flex flex-col justify-between group shadow-sm cursor-pointer ${
                  isClosed
                    ? 'bg-slate-950/50 border-slate-800/70 opacity-80 hover:opacity-100 hover:border-slate-700'
                    : 'bg-slate-900/80 border-slate-800 hover:border-cyan-500/40'
                }`}
              >
                <div className="space-y-3">
                  {/* Top Bar: Case ID + Status + Evidence count */}
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-bold">
                        {c.id}
                      </span>
                      <span
                        className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                          isClosed
                            ? 'bg-amber-950/30 text-amber-300 border-amber-500/30'
                            : 'bg-emerald-950/30 text-emerald-300 border-emerald-500/30'
                        }`}
                      >
                        {isClosed ? <Lock className="w-2.5 h-2.5" /> : <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
                        <span>{c.status}</span>
                      </span>
                    </div>

                    <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
                      <HardDrive className="w-3.5 h-3.5 text-cyan-400" />
                      {c.evidence_count} evidence item(s)
                    </span>
                  </div>

                  {/* Title & Description */}
                  <div>
                    <h3 className="text-sm font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                      {c.title}
                    </h3>
                    {(c.description || c.notes) && (
                      <p className="text-xs text-slate-400 line-clamp-2 mt-1">
                        {c.description || c.notes}
                      </p>
                    )}
                  </div>
                </div>

                {/* Card Footer: Metadata and Action Buttons */}
                <div className="pt-4 mt-4 border-t border-slate-800/80 space-y-3">
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1">
                        <User className="w-3.5 h-3.5 text-slate-400" />
                        <span>{c.investigator_name}</span>
                      </span>
                      <span className="flex items-center gap-1 font-mono text-[11px]">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        <span>{c.created_at.split('T')[0]}</span>
                      </span>
                    </div>

                    <span className="text-cyan-400 text-xs font-semibold inline-flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <span>Open Workspace</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  </div>

                  {/* Action Button Bar */}
                  <div className="flex items-center justify-between pt-1 gap-2 border-t border-slate-800/40">
                    <div className="flex items-center gap-1.5">
                      {/* Edit Button */}
                      <button
                        type="button"
                        onClick={(e) => handleOpenEdit(e, c)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-800/70 hover:bg-slate-800 text-slate-300 hover:text-slate-100 text-[11px] font-medium border border-slate-700/60 transition-colors"
                        title="Edit case title or description"
                      >
                        <Edit3 className="w-3 h-3 text-cyan-400" />
                        <span>Edit</span>
                      </button>

                      {/* Audit Trail Button */}
                      <button
                        type="button"
                        onClick={(e) => handleOpenAudit(e, c)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-800/70 hover:bg-slate-800 text-slate-300 hover:text-slate-100 text-[11px] font-medium border border-slate-700/60 transition-colors"
                        title="View case audit log events"
                      >
                        <History className="w-3 h-3 text-purple-400" />
                        <span>Audit Log</span>
                      </button>
                    </div>

                    {/* Quick Close / Reopen Toggle */}
                    <button
                      type="button"
                      onClick={(e) => handleToggleStatus(e, c)}
                      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-medium border transition-colors ${
                        isClosed
                          ? 'bg-emerald-950/30 hover:bg-emerald-900/40 text-emerald-300 border-emerald-500/30'
                          : 'bg-amber-950/30 hover:bg-amber-900/40 text-amber-300 border-amber-500/30'
                      }`}
                      title={isClosed ? 'Reopen case for additional evidence' : 'Close case to prevent evidence modifications'}
                    >
                      {isClosed ? <Unlock className="w-3 h-3" /> : <Lock className="w-3 h-3" />}
                      <span>{isClosed ? 'Reopen Case' : 'Close Case'}</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
          <EmptyState
            icon={FolderArchive}
            title={searchQuery ? 'No Matching Cases' : 'No Cases in Selected View'}
            description={
              searchQuery
                ? 'No registered forensic cases match your search query.'
                : 'Zero cases match the active filter. Switch filter tabs or create a new investigation case to begin.'
            }
            actionText="Create Case"
            onAction={() => navigate('/cases/new')}
            className="py-16"
          />
        </div>
      )}

      {/* Database & Audit Persistence Notice */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-400">
        <span className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-cyan-400" />
          <span>SQLite Database:</span>
          <code className="font-mono text-slate-300">backend/data/audiosleuth.db</code>
          <span className="text-slate-600">•</span>
          <span>Cases & Audit Tables Initialized</span>
        </span>
        <span className="font-mono text-[11px] text-emerald-400 flex items-center gap-1 self-start sm:self-auto">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>Persistent Storage & Foreign Keys Active</span>
        </span>
      </div>

      {/* Edit Case Modal */}
      {editingCase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between p-4 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Edit3 className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-slate-100">
                  Edit Case Metadata — {editingCase.id}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setEditingCase(null)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveEdit} className="p-5 space-y-4">
              {editError && (
                <div className="p-3 rounded-lg bg-rose-950/30 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{editError}</span>
                </div>
              )}

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Case Title *</label>
                <input
                  type="text"
                  required
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Lead Investigator *</label>
                <input
                  type="text"
                  required
                  value={editInvestigator}
                  onChange={(e) => setEditInvestigator(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Description / Investigation Notes</label>
                <textarea
                  rows={3}
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setEditingCase(null)}
                  className="px-3.5 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isUpdating}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-xs disabled:opacity-50"
                >
                  {isUpdating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                  <span>Save Metadata</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Audit Trail Modal */}
      {auditCase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
          <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden flex flex-col max-h-[85vh] animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between p-4 border-b border-slate-800 shrink-0">
              <div className="flex items-center gap-2">
                <History className="w-4 h-4 text-purple-400" />
                <div>
                  <h3 className="text-sm font-bold text-slate-100">
                    Forensic Audit Trail — {auditCase.id}
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    {auditCase.title}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setAuditCase(null)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Event List */}
            <div className="p-5 overflow-y-auto space-y-3 flex-1">
              {auditLoading ? (
                <div className="p-8 text-center text-slate-400 text-xs flex flex-col items-center justify-center gap-2">
                  <RefreshCw className="w-5 h-5 animate-spin text-purple-400" />
                  <span>Loading durable audit log records...</span>
                </div>
              ) : auditEvents.length > 0 ? (
                auditEvents.map((evt) => (
                  <div
                    key={evt.id}
                    className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-cyan-400 font-bold uppercase text-[11px]">
                          {evt.action.replace('_', ' ')}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-1.5 py-0.2 rounded-full border uppercase ${
                            evt.outcome.includes('success') || evt.outcome.includes('match')
                              ? 'bg-emerald-950/40 text-emerald-300 border-emerald-500/30'
                              : 'bg-rose-950/40 text-rose-300 border-rose-500/30'
                          }`}
                        >
                          {evt.outcome}
                        </span>
                      </div>
                      <span className="font-mono text-[10px] text-slate-500">
                        {evt.timestamp}
                      </span>
                    </div>

                    <div className="font-mono text-[11px] text-slate-400 bg-slate-900/60 p-2 rounded border border-slate-800/60 break-all">
                      {JSON.stringify(evt.details, null, 2)}
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                      <span>Event ID: {evt.id}</span>
                      {evt.evidence_id && (
                        <button
                          type="button"
                          onClick={() => {
                            setAuditCase(null);
                            navigate(`/evidence/${encodeURIComponent(evt.evidence_id!)}`);
                          }}
                          className="text-cyan-400 hover:text-cyan-300 hover:underline inline-flex items-center gap-1"
                        >
                          <span>Evidence: {evt.evidence_id}</span>
                          <span>&rarr;</span>
                        </button>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-slate-400 text-xs">
                  Zero audit events recorded for this case.
                </div>
              )}
            </div>

            {/* Audit Modal Footer with ISO 27037 Disclaimer */}
            <div className="p-3.5 bg-slate-950 border-t border-slate-800 text-[10px] text-slate-500 shrink-0">
              <p className="italic">
                {auditDisclaimer ||
                  'Audit records are preserved in local SQLite database for compliance reporting and timeline tracking.'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
