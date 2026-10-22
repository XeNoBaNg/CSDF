"""Forensic PDF Report Generator for AudioSleuth.

Compiles comprehensive, evidence-based PDF examination reports containing
persisted case records, evidence custody metadata, cryptographic hash verifications,
signal analysis findings, embedded waveforms and spectrograms, chronological audit trails,
and standardized ISO/IEC 27037 forensic disclaimers.
"""

from datetime import datetime, timezone
import io
from typing import Any, Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from backend.app.models.audit import AuditEventModel
from backend.app.models.case import CaseModel
from backend.app.models.evidence import EvidenceModel
from backend.app.schemas.analysis import AnalysisSummary, ForensicFinding
from backend.app.schemas.audio import AudioMetadataResponse


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas that dynamically counts total pages and draws running headers and footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        page_w, page_h = letter
        margin = 36.0  # 0.5 inch margins

        # Running Top Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(margin, page_h - 26, "AudioSleuth Forensic Workstation — Digital Evidence Examination Report")
            self.drawRightString(page_w - margin, page_h - 26, "CONFIDENTIAL / INVESTIGATIVE USE")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(margin, page_h - 30, page_w - margin, page_h - 30)

        # Running Bottom Footer (All Pages)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(margin, 32, page_w - margin, 32)

        self.drawString(margin, 20, "AudioSleuth Forensic Toolkit • PICT CSDF Lab")
        self.drawRightString(page_w - margin, 20, f"Page {self._pageNumber} of {total_pages}")
        self.restoreState()


class ForensicPdfReportGenerator:
    """Orchestrates ReportLab document creation for forensic evidence reports."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Initializes tailored typographic styles conforming to digital forensic reporting standards."""
        # Main Title
        self.styles.add(ParagraphStyle(
            name="ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            alignment=0,
            spaceAfter=3,
        ))

        # Subtitle
        self.styles.add(ParagraphStyle(
            name="ReportSubtitle",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0891b2"),
            alignment=0,
            spaceAfter=10,
        ))

        # Section Heading
        self.styles.add(ParagraphStyle(
            name="SectionHeading",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True,
        ))

        # Subsection Heading
        self.styles.add(ParagraphStyle(
            name="SubsectionHeading",
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=6,
            spaceAfter=2,
            keepWithNext=True,
        ))

        # Normal Body Text
        self.styles.add(ParagraphStyle(
            name="BodySmall",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#334155"),
        ))

        # Key-Value Label
        self.styles.add(ParagraphStyle(
            name="KVLabel",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569"),
        ))

        # Key-Value Value
        self.styles.add(ParagraphStyle(
            name="KVValue",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#0f172a"),
        ))

        # Monospace Text (Hashes, IDs)
        self.styles.add(ParagraphStyle(
            name="MonoText",
            fontName="Courier",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#0f172a"),
        ))

        # Table Header
        self.styles.add(ParagraphStyle(
            name="TableHeader",
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#f8fafc"),
        ))

        # Table Cell
        self.styles.add(ParagraphStyle(
            name="TableCell",
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#1e293b"),
        ))

        # Table Cell Monospace
        self.styles.add(ParagraphStyle(
            name="TableCellMono",
            fontName="Courier",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#1e293b"),
        ))

        # Disclaimer Callout Text
        self.styles.add(ParagraphStyle(
            name="DisclaimerText",
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=10.5,
            textColor=colors.HexColor("#475569"),
        ))

    def generate_report(
        self,
        report_id: str,
        generated_at: str,
        case: CaseModel,
        evidence: EvidenceModel,
        metadata: AudioMetadataResponse,
        integrity_status: str,
        calculated_sha256: str,
        findings: List[ForensicFinding],
        analysis_summary: Optional[AnalysisSummary] = None,
        applied_parameters: Optional[Dict[str, Any]] = None,
        waveform_png: Optional[bytes] = None,
        spectrogram_png: Optional[bytes] = None,
        audit_events: Optional[List[AuditEventModel]] = None,
        examiner_notes: Optional[str] = None,
    ) -> bytes:
        """Generates a complete forensic PDF examination report in memory."""
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=38,
        )

        story = []
        printable_w = letter[0] - 72  # 540 points

        # =====================================================================
        # Document Header Banner
        # =====================================================================
        story.append(Paragraph("FORENSIC DIGITAL AUDIO EXAMINATION REPORT", self.styles["ReportTitle"]))
        story.append(Paragraph(
            "AudioSleuth Forensic Toolkit • PICT Cyber Security & Digital Forensics Lab • SPPU",
            self.styles["ReportSubtitle"],
        ))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0891b2"), spaceAfter=8))

        # Metadata Header Box
        header_data = [
            [
                Paragraph("<b>Report Identifier:</b>", self.styles["KVLabel"]),
                Paragraph(f"<font color='#0891b2'><b>{report_id}</b></font>", self.styles["MonoText"]),
                Paragraph("<b>Generated Timestamp:</b>", self.styles["KVLabel"]),
                Paragraph(f"{generated_at} (UTC)", self.styles["KVValue"]),
            ],
            [
                Paragraph("<b>Software Engine:</b>", self.styles["KVLabel"]),
                Paragraph("AudioSleuth Core v1.0.0 (Offline)", self.styles["KVValue"]),
                Paragraph("<b>Examination Scope:</b>", self.styles["KVLabel"]),
                Paragraph("Integrity, Acoustic Properties & Anomalies", self.styles["KVValue"]),
            ],
        ]
        header_table = Table(header_data, colWidths=[105, 165, 110, 160])
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 10))

        # =====================================================================
        # Section 1: Investigation Case Record
        # =====================================================================
        story.append(Paragraph("1. INVESTIGATION CASE RECORD", self.styles["SectionHeading"]))
        case_data = [
            [
                Paragraph("<b>Case Reference:</b>", self.styles["KVLabel"]),
                Paragraph(f"<b>{case.id}</b>", self.styles["MonoText"]),
                Paragraph("<b>Case Lifecycle Status:</b>", self.styles["KVLabel"]),
                Paragraph(
                    f"<font color='{'#15803d' if case.status == 'active' else '#b45309'}'><b>{case.status.upper()}</b></font>",
                    self.styles["KVValue"],
                ),
            ],
            [
                Paragraph("<b>Investigation Title:</b>", self.styles["KVLabel"]),
                Paragraph(case.title, self.styles["KVValue"]),
                Paragraph("<b>Lead Examiner:</b>", self.styles["KVLabel"]),
                Paragraph(case.investigator_name, self.styles["KVValue"]),
            ],
            [
                Paragraph("<b>Creation Date:</b>", self.styles["KVLabel"]),
                Paragraph(case.created_at, self.styles["KVValue"]),
                Paragraph("<b>Examiner Notes:</b>", self.styles["KVLabel"]),
                Paragraph(case.description or case.notes or "None documented", self.styles["KVValue"]),
            ],
        ]
        if examiner_notes:
            case_data.append([
                Paragraph("<b>Report Notes:</b>", self.styles["KVLabel"]),
                Paragraph(examiner_notes, self.styles["KVValue"]),
                Paragraph("", self.styles["KVLabel"]),
                Paragraph("", self.styles["KVValue"]),
            ])

        case_table = Table(case_data, colWidths=[105, 165, 110, 160])
        case_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(case_table)
        story.append(Spacer(1, 10))

        # =====================================================================
        # Section 2: Evidence Item & Custody Verification Record
        # =====================================================================
        story.append(Paragraph("2. DIGITAL EVIDENCE & CUSTODY RECORD", self.styles["SectionHeading"]))
        file_size_fmt = self._format_bytes(evidence.file_size_bytes)
        is_match = integrity_status in ("match", "verified")

        evidence_data = [
            [
                Paragraph("<b>Evidence Identifier:</b>", self.styles["KVLabel"]),
                Paragraph(f"<b>{evidence.id}</b>", self.styles["MonoText"]),
                Paragraph("<b>Ingestion Timestamp:</b>", self.styles["KVLabel"]),
                Paragraph(evidence.ingested_at, self.styles["KVValue"]),
            ],
            [
                Paragraph("<b>Original Filename:</b>", self.styles["KVLabel"]),
                Paragraph(evidence.original_filename, self.styles["KVValue"]),
                Paragraph("<b>Format & MIME:</b>", self.styles["KVLabel"]),
                Paragraph(f"{evidence.format.upper()} ({evidence.mime_type})", self.styles["KVValue"]),
            ],
            [
                Paragraph("<b>Physical File Size:</b>", self.styles["KVLabel"]),
                Paragraph(f"{evidence.file_size_bytes:,} B ({file_size_fmt})", self.styles["KVValue"]),
                Paragraph("<b>Integrity Status:</b>", self.styles["KVLabel"]),
                Paragraph(
                    "<font color='#15803d'><b>PRISTINE BYTE MATCH (VERIFIED)</b></font>"
                    if is_match
                    else "<font color='#b91c1c'><b>CRITICAL MISMATCH / TAMPERED</b></font>",
                    self.styles["KVValue"],
                ),
            ],
            [
                Paragraph("<b>Intake SHA-256 Digest:</b>", self.styles["KVLabel"]),
                Paragraph(f"<b>{evidence.sha256_hash}</b>", self.styles["MonoText"]),
                Paragraph("<b>Disk Recalculated:</b>", self.styles["KVLabel"]),
                Paragraph(f"<b>{calculated_sha256}</b>", self.styles["MonoText"]),
            ],
        ]
        evidence_table = Table(evidence_data, colWidths=[105, 165, 110, 160])
        evidence_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(evidence_table)
        story.append(Spacer(1, 10))

        # =====================================================================
        # Section 3: Audio Signal Properties & Metadata Tags
        # =====================================================================
        story.append(Paragraph("3. SIGNAL CHARACTERISTICS & METADATA", self.styles["SectionHeading"]))
        dec = metadata.decoded_properties
        enc = metadata.encoded_properties

        meta_data = [
            [
                Paragraph("<b>Sampling Frequency:</b>", self.styles["KVLabel"]),
                Paragraph(f"{dec.sample_rate_hz:,} Hz", self.styles["KVValue"]),
                Paragraph("<b>Audio Duration:</b>", self.styles["KVLabel"]),
                Paragraph(f"{dec.duration_seconds:.3f} s ({self._format_duration(dec.duration_seconds)})", self.styles["KVValue"]),
            ],
            [
                Paragraph("<b>Channel Configuration:</b>", self.styles["KVLabel"]),
                Paragraph(f"{dec.channels} ({'Mono' if dec.channels == 1 else 'Stereo' if dec.channels == 2 else 'Multi'})", self.styles["KVValue"]),
                Paragraph("<b>Total Decoded Samples:</b>", self.styles["KVLabel"]),
                Paragraph(f"{dec.total_samples:,} samples", self.styles["KVValue"]),
            ],
            [
                Paragraph("<b>Sample Format:</b>", self.styles["KVLabel"]),
                Paragraph(dec.sample_format or "Unavailable / Standard Float", self.styles["KVValue"]),
                Paragraph("<b>Bit Depth:</b>", self.styles["KVLabel"]),
                Paragraph(f"{dec.bit_depth}-bit" if dec.bit_depth else "Unavailable (Lossy / VBR Container)", self.styles["KVValue"]),
            ],
            [
                Paragraph("<b>Audio Codec:</b>", self.styles["KVLabel"]),
                Paragraph(enc.codec or "Standard Container Codec", self.styles["KVValue"]),
                Paragraph("<b>Bitrate:</b>", self.styles["KVLabel"]),
                Paragraph(f"{enc.bitrate_kbps:.1f} kbps" if enc.bitrate_kbps else "Unavailable / Uncompressed", self.styles["KVValue"]),
            ],
        ]
        meta_table = Table(meta_data, colWidths=[105, 165, 110, 160])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(meta_table)

        # Embedded Container Metadata Tags (if present in dict)
        emb = metadata.embedded_metadata or {}
        emb_tags = []
        if isinstance(emb, dict):
            for k, v in emb.items():
                if v:
                    emb_tags.append(f"{k.capitalize()}: {v}")

        story.append(Spacer(1, 4))
        if emb_tags:
            tag_text = " • ".join(emb_tags)
            story.append(Paragraph(f"<b>Embedded Container Tags:</b> <font color='#334155'>{tag_text}</font>", self.styles["BodySmall"]))
        else:
            story.append(Paragraph("<b>Embedded Container Tags:</b> <i>No embedded metadata tags detected in audio file header.</i>", self.styles["BodySmall"]))

        story.append(Spacer(1, 10))

        # =====================================================================
        # Section 4: Acoustic Signal Visualizations
        # =====================================================================
        if waveform_png or spectrogram_png:
            story.append(Paragraph("4. ACOUSTIC SIGNAL VISUALIZATIONS", self.styles["SectionHeading"]))

            if waveform_png:
                wf_img = RLImage(io.BytesIO(waveform_png), width=printable_w, height=115)
                story.append(wf_img)
                story.append(Paragraph("<b>Figure 1:</b> Peak-preserving waveform envelope (min/max sample tracking) illustrating temporal amplitude distribution.", self.styles["DisclaimerText"]))
                story.append(Spacer(1, 6))

            if spectrogram_png:
                spec_img = RLImage(io.BytesIO(spectrogram_png), width=printable_w, height=140)
                story.append(spec_img)
                story.append(Paragraph("<b>Figure 2:</b> STFT time-frequency spectrogram (decibel calibrated scale, dynamic range floor -80 dB, Nyquist ceiling).", self.styles["DisclaimerText"]))
                story.append(Spacer(1, 8))

        # =====================================================================
        # Section 5: Explainable Signal Anomaly Findings
        # =====================================================================
        story.append(Paragraph("5. EXPLAINABLE SIGNAL ANOMALY FINDINGS", self.styles["SectionHeading"]))

        # Summary Metrics Box
        total_f = len(findings)
        by_cat = analysis_summary.by_category if analysis_summary else {}
        by_prio = analysis_summary.by_priority if analysis_summary else {}

        summary_p = Paragraph(
            f"<b>Analysis Summary:</b> Total Flagged Intervals: <b>{total_f}</b> | "
            f"Silence: {by_cat.get('silence', 0)} • Transitions: {by_cat.get('amplitude_discontinuity', 0)} • Spectral Flux: {by_cat.get('spectral_inconsistency', 0)} | "
            f"High Priority: {by_prio.get('high', 0)} • Medium: {by_prio.get('medium', 0)} • Low: {by_prio.get('low', 0)}",
            self.styles["BodySmall"],
        )
        story.append(summary_p)
        story.append(Spacer(1, 6))

        if total_f == 0:
            no_findings_p = Paragraph(
                "<i>No signal anomalies detected exceeding applied mathematical detector thresholds. "
                "The signal exhibits normal acoustic continuity within configured parameters.</i>",
                self.styles["BodySmall"],
            )
            story.append(no_findings_p)
            story.append(Spacer(1, 10))
        else:
            # Findings Table Header
            table_header = [
                Paragraph("<b>ID</b>", self.styles["TableHeader"]),
                Paragraph("<b>Category</b>", self.styles["TableHeader"]),
                Paragraph("<b>Priority</b>", self.styles["TableHeader"]),
                Paragraph("<b>Interval (s)</b>", self.styles["TableHeader"]),
                Paragraph("<b>Measured vs Thr.</b>", self.styles["TableHeader"]),
                Paragraph("<b>Investigative Context & Review Action</b>", self.styles["TableHeader"]),
            ]
            f_rows = [table_header]

            for finding in findings:
                prio_str = finding.priority.value.upper()
                prio_color = "#b91c1c" if prio_str == "HIGH" else "#b45309" if prio_str == "MEDIUM" else "#334155"

                time_str = (
                    f"{finding.start_time:.3f} - {finding.end_time:.3f}s"
                    if finding.end_time is not None
                    else f"t = {finding.event_time or finding.start_time:.3f}s"
                )

                f_id = getattr(finding, "id", getattr(finding, "finding_id", "FND"))
                f_thresh = getattr(finding, "applied_threshold", getattr(finding, "threshold_applied", None))
                f_expl = getattr(finding, "explanation", getattr(finding, "reason", "Signal anomaly detected"))
                f_action = getattr(finding, "suggested_action", "Manual examination recommended")

                score_str = (
                    f"{finding.measured_value:.4f} (thr: {f_thresh:.4f})"
                    if finding.measured_value is not None and f_thresh is not None
                    else "N/A"
                )

                cat_clean = finding.category.value.replace("_", " ").title()

                f_rows.append([
                    Paragraph(f"<b>{f_id}</b>", self.styles["TableCellMono"]),
                    Paragraph(cat_clean, self.styles["TableCell"]),
                    Paragraph(f"<font color='{prio_color}'><b>{prio_str}</b></font>", self.styles["TableCell"]),
                    Paragraph(time_str, self.styles["TableCellMono"]),
                    Paragraph(score_str, self.styles["TableCellMono"]),
                    Paragraph(f"{f_expl}. <i>Action: {f_action}</i>", self.styles["TableCell"]),
                ])

            # Widths summing to 540 pt
            findings_table = Table(f_rows, colWidths=[55, 75, 45, 80, 85, 200])
            findings_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(findings_table)
            story.append(Spacer(1, 10))

        # =====================================================================
        # Section 6: Chronological Audit Trail & Event History
        # =====================================================================
        if audit_events and len(audit_events) > 0:
            story.append(Paragraph("6. DURABLE CHAIN-OF-CUSTODY AUDIT TRAIL", self.styles["SectionHeading"]))

            audit_header = [
                Paragraph("<b>Event ID</b>", self.styles["TableHeader"]),
                Paragraph("<b>Timestamp (UTC)</b>", self.styles["TableHeader"]),
                Paragraph("<b>Action Type</b>", self.styles["TableHeader"]),
                Paragraph("<b>Outcome</b>", self.styles["TableHeader"]),
                Paragraph("<b>Milestone Details</b>", self.styles["TableHeader"]),
            ]
            audit_rows = [audit_header]

            for evt in audit_events:
                # Summarize details JSON for table
                det_summary = []
                if evt.details:
                    for k, v in list(evt.details.items())[:3]:
                        if not isinstance(v, (dict, list)):
                            det_summary.append(f"{k}: {v}")
                det_str = ", ".join(det_summary) if det_summary else "Recorded"

                audit_rows.append([
                    Paragraph(f"<b>{evt.id}</b>", self.styles["TableCellMono"]),
                    Paragraph(evt.timestamp.replace("T", " ")[:19], self.styles["TableCellMono"]),
                    Paragraph(evt.action.replace("_", " ").title(), self.styles["TableCell"]),
                    Paragraph(
                        f"<font color='{'#15803d' if evt.outcome == 'success' else '#b91c1c'}'><b>{evt.outcome.upper()}</b></font>",
                        self.styles["TableCell"],
                    ),
                    Paragraph(det_str, self.styles["TableCell"]),
                ])

            audit_table = Table(audit_rows, colWidths=[65, 95, 95, 55, 230])
            audit_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(audit_table)
            story.append(Spacer(1, 10))

        # =====================================================================
        # Section 7: Scientific Methodology & Forensic Evidentiary Disclaimers
        # =====================================================================
        disclaimer_elements = [
            Paragraph("7. FORENSIC METHODOLOGY, LIMITATIONS & EVIDENTIARY DISCLAIMERS", self.styles["SectionHeading"]),
            Paragraph(
                "<b>1. Investigative Indicators vs. Definitive Proof:</b> Signal anomalies flagged in this report are mathematical deviations from acoustic baseline continuity. They indicate localized regions warranting manual examiner inspection and do <u>NOT</u> constitute legal proof of tampering, digital synthesis, audio splicing, or malicious manipulation.",
                self.styles["DisclaimerText"],
            ),
            Spacer(1, 3),
            Paragraph(
                "<b>2. Natural Speech & Codec Artifacts:</b> Normal human speech dynamics routinely produce high-amplitude steps (e.g. plosive consonants /p/, /t/, /k/), natural pause silences, and spectral shifts. Additionally, lossy compression codecs (MP3/AAC quantization boundaries) and microphone handling noise can trigger threshold excursions without intentional tampering.",
                self.styles["DisclaimerText"],
            ),
            Spacer(1, 3),
            Paragraph(
                "<b>3. Cryptographic Scope:</b> A matching SHA-256 hash confirms byte-level physical identity between the recording as stored on disk and the recording as originally ingested. A matching hash does <u>NOT</u> establish recording authenticity or author identity prior to intake.",
                self.styles["DisclaimerText"],
            ),
            Spacer(1, 3),
            Paragraph(
                "<b>4. Legal Admissibility & ISO/IEC 27037 Notice:</b> This report is generated by the AudioSleuth academic toolkit as an investigative assistance document. Standard SQLite persistence does not provide hardware-secured or cryptographically certified WORM chain-of-custody archives.",
                self.styles["DisclaimerText"],
            ),
            Spacer(1, 14),
            # Sign-off block
            Table(
                [
                    [
                        Paragraph(f"<b>Examiner:</b> {case.investigator_name}", self.styles["BodySmall"]),
                        Paragraph("<b>Signature:</b> ___________________________", self.styles["BodySmall"]),
                        Paragraph(f"<b>Date:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}", self.styles["BodySmall"]),
                    ]
                ],
                colWidths=[180, 220, 140],
            ),
        ]
        story.append(KeepTogether(disclaimer_elements))

        # Build PDF with dynamic page numbering
        doc.build(story, canvasmaker=NumberedCanvas)
        return pdf_buffer.getvalue()

    def _format_bytes(self, bytes_val: int) -> str:
        """Formats bytes into human readable string."""
        if bytes_val < 1024:
            return f"{bytes_val} B"
        if bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024.0:.1f} KB"
        return f"{bytes_val / (1024.0 * 1024.0):.2f} MB"

    def _format_duration(self, seconds: float) -> str:
        """Formats duration into MM:SS format."""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
