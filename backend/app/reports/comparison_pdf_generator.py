"""Forensic Cross-Recording Comparison PDF Report Generator for AudioSleuth.

Compiles evidence-based, side-by-side comparison reports containing
metadata alignment, signal energy statistics, STFT spectral metrics,
anomaly timeline distributions, and ISO/IEC 27037 forensic limitations.
"""

from datetime import datetime, timezone
import io
from typing import Any, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from backend.app.schemas.comparison import ComparisonResponse


class ComparisonNumberedCanvas(canvas.Canvas):
    """Two-pass canvas for dynamic page count ("Page X of Y") and running headers/footers."""

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
            self.drawString(margin, page_h - 26, "AudioSleuth Forensic Workstation — Cross-Recording Comparison Report")
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


class ComparisonPdfReportGenerator:
    """Builds a formatted forensic PDF comparison report from a ComparisonResponse."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name="CompTitle",
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=3,
        ))
        self.styles.add(ParagraphStyle(
            name="CompSubtitle",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0891b2"),
            spaceAfter=8,
        ))
        self.styles.add(ParagraphStyle(
            name="CompHeading",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=8,
            spaceAfter=4,
        ))
        self.styles.add(ParagraphStyle(
            name="CompBody",
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#334155"),
        ))
        self.styles.add(ParagraphStyle(
            name="CompBodyBold",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#0f172a"),
        ))
        self.styles.add(ParagraphStyle(
            name="CompMono",
            fontName="Courier",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#0f172a"),
        ))
        self.styles.add(ParagraphStyle(
            name="CompDisclaimer",
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#64748b"),
        ))

    def generate_pdf(self, comparison: ComparisonResponse) -> bytes:
        """Generates an in-memory PDF report document and returns raw bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=40,
            bottomMargin=42,
        )

        story: List[Any] = []
        col_w = 540  # Total printable width

        # Title & Header
        story.append(Paragraph("AudioSleuth — Forensic Cross-Recording Examination Report", self.styles["CompTitle"]))
        story.append(Paragraph("Automated Comparative Signal, Spectral, and Anomaly Timeline Analysis", self.styles["CompSubtitle"]))

        meta_hdr = [
            [
                Paragraph(f"<b>Comparison ID:</b> <font name='Courier'>{comparison.id}</font>", self.styles["CompBody"]),
                Paragraph(f"<b>Executed:</b> {comparison.timestamp[:19].replace('T', ' ')} UTC", self.styles["CompBody"]),
            ],
            [
                Paragraph(f"<b>Primary Evidence (A):</b> <font name='Courier'>{comparison.evidence_id_a}</font>", self.styles["CompBody"]),
                Paragraph(f"<b>Secondary Evidence (B):</b> <font name='Courier'>{comparison.evidence_id_b}</font>", self.styles["CompBody"]),
            ],
        ]
        t_hdr = Table(meta_hdr, colWidths=[col_w * 0.5, col_w * 0.5])
        t_hdr.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_hdr)
        story.append(Spacer(1, 8))

        # Section 1: Overview & High-Level Finding
        story.append(Paragraph("1. Forensic Executive Summary & Similarity Index", self.styles["CompHeading"]))
        summary = comparison.summary
        summ_data = [
            [
                Paragraph("<b>Overall Acoustic Label:</b>", self.styles["CompBody"]),
                Paragraph(f"<b>{summary.acoustic_similarity_label}</b>", self.styles["CompBodyBold"]),
                Paragraph("<b>Transparent Similarity:</b>", self.styles["CompBody"]),
                Paragraph(f"<b>{summary.transparent_similarity_score:.4f}</b> / 1.0000", self.styles["CompBodyBold"]),
            ],
            [
                Paragraph("<b>Byte-Level Match (SHA-256):</b>", self.styles["CompBody"]),
                Paragraph("EXACT MATCH" if summary.byte_match else "DIFFERENT HASHES", self.styles["CompBodyBold"]),
                Paragraph("<b>Duration Match (Δ ≤ 0.05s):</b>", self.styles["CompBody"]),
                Paragraph("MATCH" if summary.duration_match else "DISPARATE DURATION", self.styles["CompBodyBold"]),
            ],
        ]
        t_summ = Table(summ_data, colWidths=[col_w * 0.25, col_w * 0.25, col_w * 0.25, col_w * 0.25])
        t_summ.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_summ)
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Contextual Explanation:</b> {summary.explanation}", self.styles["CompBody"]))
        story.append(Spacer(1, 2))
        story.append(Paragraph(f"<b>Formula Basis:</b> <font color='#64748b'>{summary.scoring_formula_explanation}</font>", self.styles["CompDisclaimer"]))

        if summary.warnings:
            story.append(Spacer(1, 4))
            for w in summary.warnings:
                story.append(Paragraph(f"• <b>Warning:</b> {w}", self.styles["CompBody"]))

        story.append(Spacer(1, 8))

        # Section 2: Metadata & Container Properties Side-by-Side
        story.append(Paragraph("2. Evidence Custody & Recording Metadata Comparison", self.styles["CompHeading"]))
        meta = comparison.metadata_comparison
        meta_table = [
            [Paragraph("<b>Property</b>", self.styles["CompBodyBold"]), Paragraph("<b>Item A (Primary)</b>", self.styles["CompBodyBold"]), Paragraph("<b>Item B (Secondary)</b>", self.styles["CompBodyBold"]), Paragraph("<b>Comparison Status</b>", self.styles["CompBodyBold"])],
            [Paragraph("Filename", self.styles["CompBody"]), Paragraph(meta.filename_a, self.styles["CompBody"]), Paragraph(meta.filename_b, self.styles["CompBody"]), Paragraph("Identical" if meta.filename_a == meta.filename_b else "Different names", self.styles["CompBody"])],
            [Paragraph("Format / Container", self.styles["CompBody"]), Paragraph(meta.format_a, self.styles["CompBody"]), Paragraph(meta.format_b, self.styles["CompBody"]), Paragraph("Match" if meta.format_match else "Different format", self.styles["CompBody"])],
            [Paragraph("File Size (Bytes)", self.styles["CompBody"]), Paragraph(f"{meta.file_size_bytes_a:,}", self.styles["CompBody"]), Paragraph(f"{meta.file_size_bytes_b:,}", self.styles["CompBody"]), Paragraph(f"Δ = {meta.file_size_diff_bytes:,} bytes", self.styles["CompBody"])],
            [Paragraph("Duration", self.styles["CompBody"]), Paragraph(f"{meta.duration_seconds_a:.4f}s", self.styles["CompBody"]), Paragraph(f"{meta.duration_seconds_b:.4f}s", self.styles["CompBody"]), Paragraph(f"Δ = {meta.duration_diff_seconds:.4f}s", self.styles["CompBody"])],
            [Paragraph("Sample Rate", self.styles["CompBody"]), Paragraph(f"{meta.sample_rate_hz_a:,} Hz", self.styles["CompBody"]), Paragraph(f"{meta.sample_rate_hz_b:,} Hz", self.styles["CompBody"]), Paragraph("Match" if meta.sample_rate_match else "Mismatch", self.styles["CompBody"])],
            [Paragraph("Channels", self.styles["CompBody"]), Paragraph(str(meta.channels_a), self.styles["CompBody"]), Paragraph(str(meta.channels_b), self.styles["CompBody"]), Paragraph("Match" if meta.channels_match else "Mismatch", self.styles["CompBody"])],
            [Paragraph("Bit Depth", self.styles["CompBody"]), Paragraph(f"{meta.bit_depth_a} bit" if meta.bit_depth_a else "Lossy / Variable", self.styles["CompBody"]), Paragraph(f"{meta.bit_depth_b} bit" if meta.bit_depth_b else "Lossy / Variable", self.styles["CompBody"]), Paragraph("Match" if meta.bit_depth_match else "Different", self.styles["CompBody"])],
            [Paragraph("SHA-256 Digest", self.styles["CompBody"]), Paragraph(meta.sha256_a, self.styles["CompMono"]), Paragraph(meta.sha256_b, self.styles["CompMono"]), Paragraph("EXACT MATCH" if meta.sha256_match else "Mismatch", self.styles["CompBodyBold"])],
        ]
        t_meta = Table(meta_table, colWidths=[col_w * 0.22, col_w * 0.28, col_w * 0.28, col_w * 0.22])
        t_meta.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0891b2")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(t_meta)
        story.append(Spacer(1, 8))

        # Section 3: Signal-Level Energy and Dynamics
        story.append(Paragraph("3. Signal Energy & Amplitude Dynamic Range Metrics", self.styles["CompHeading"]))
        sig = comparison.signal_comparison
        sig_table = [
            [Paragraph("<b>Metric</b>", self.styles["CompBodyBold"]), Paragraph("<b>Item A</b>", self.styles["CompBodyBold"]), Paragraph("<b>Item B</b>", self.styles["CompBodyBold"]), Paragraph("<b>Difference / Ratio</b>", self.styles["CompBodyBold"]), Paragraph("<b>Description</b>", self.styles["CompBodyBold"])],
            [Paragraph("Peak Amplitude", self.styles["CompBody"]), Paragraph(f"{sig.peak_amplitude_a:.5f}", self.styles["CompBody"]), Paragraph(f"{sig.peak_amplitude_b:.5f}", self.styles["CompBody"]), Paragraph(f"Δ = {sig.peak_amplitude_diff:.5f}", self.styles["CompBody"]), Paragraph("Maximum absolute sample value", self.styles["CompBody"])],
            [Paragraph("RMS Energy", self.styles["CompBody"]), Paragraph(f"{sig.rms_energy_a:.5f}", self.styles["CompBody"]), Paragraph(f"{sig.rms_energy_b:.5f}", self.styles["CompBody"]), Paragraph(f"{sig.rms_ratio_db:+.2f} dB", self.styles["CompBody"]), Paragraph("Root-mean-square signal energy", self.styles["CompBody"])],
            [Paragraph("Crest Factor", self.styles["CompBody"]), Paragraph(f"{sig.crest_factor_a:.2f}", self.styles["CompBody"]), Paragraph(f"{sig.crest_factor_b:.2f}", self.styles["CompBody"]), Paragraph(f"Δ = {abs(sig.crest_factor_a - sig.crest_factor_b):.2f}", self.styles["CompBody"]), Paragraph("Peak to RMS ratio (dynamic range)", self.styles["CompBody"])],
            [Paragraph("Zero Crossing Rate", self.styles["CompBody"]), Paragraph(f"{sig.zero_crossing_rate_a:.1f}/s", self.styles["CompBody"]), Paragraph(f"{sig.zero_crossing_rate_b:.1f}/s", self.styles["CompBody"]), Paragraph(f"Δ = {sig.zero_crossing_rate_diff:.1f}/s", self.styles["CompBody"]), Paragraph("Signal sign reversals per second", self.styles["CompBody"])],
            [Paragraph("Envelope Correlation", self.styles["CompBody"]), Paragraph(f"<b>r = {sig.envelope_correlation:.4f}</b>", self.styles["CompBody"]), Paragraph("—", self.styles["CompBody"]), Paragraph("r ∈ [-1.0, 1.0]", self.styles["CompBody"]), Paragraph("Pearson linear correlation of macro-amplitude envelopes", self.styles["CompBody"])],
        ]
        t_sig = Table(sig_table, colWidths=[col_w * 0.22, col_w * 0.16, col_w * 0.16, col_w * 0.18, col_w * 0.28])
        t_sig.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(t_sig)
        story.append(Spacer(1, 8))

        # Section 4: STFT Spectral Comparison
        story.append(Paragraph("4. STFT Spectral Characteristics & Frequency Distribution", self.styles["CompHeading"]))
        spec = comparison.spectral_comparison
        spec_table = [
            [Paragraph("<b>Spectral Feature</b>", self.styles["CompBodyBold"]), Paragraph("<b>Item A</b>", self.styles["CompBodyBold"]), Paragraph("<b>Item B</b>", self.styles["CompBodyBold"]), Paragraph("<b>Difference</b>", self.styles["CompBodyBold"]), Paragraph("<b>Forensic Significance</b>", self.styles["CompBodyBold"])],
            [Paragraph("Spectral Centroid", self.styles["CompBody"]), Paragraph(f"{spec.centroid_hz_a:.1f} Hz", self.styles["CompBody"]), Paragraph(f"{spec.centroid_hz_b:.1f} Hz", self.styles["CompBody"]), Paragraph(f"Δ = {spec.centroid_diff_hz:.1f} Hz", self.styles["CompBody"]), Paragraph("Center of mass of frequency spectrum", self.styles["CompBody"])],
            [Paragraph("Spectral Roll-Off (85%)", self.styles["CompBody"]), Paragraph(f"{spec.rolloff_hz_a:.1f} Hz", self.styles["CompBody"]), Paragraph(f"{spec.rolloff_hz_b:.1f} Hz", self.styles["CompBody"]), Paragraph(f"Δ = {spec.rolloff_diff_hz:.1f} Hz", self.styles["CompBody"]), Paragraph("Frequency below which 85% energy lies", self.styles["CompBody"])],
            [Paragraph("Spectral Flatness", self.styles["CompBody"]), Paragraph(f"{spec.flatness_a:.4f}", self.styles["CompBody"]), Paragraph(f"{spec.flatness_b:.4f}", self.styles["CompBody"]), Paragraph(f"Δ = {spec.flatness_diff:.4f}", self.styles["CompBody"]), Paragraph("Wiener entropy (tonal vs noise-like)", self.styles["CompBody"])],
            [Paragraph("Spectral Cosine Similarity", self.styles["CompBody"]), Paragraph(f"<b>{spec.spectral_cosine_similarity:.4f}</b>", self.styles["CompBody"]), Paragraph("—", self.styles["CompBody"]), Paragraph("Scale: [0.0, 1.0]", self.styles["CompBody"]), Paragraph("Normalized inner product of mean power spectra", self.styles["CompBody"])],
            [Paragraph("Spectral Euclidean Dist.", self.styles["CompBody"]), Paragraph(f"{spec.spectral_euclidean_distance:.4f}", self.styles["CompBody"]), Paragraph("—", self.styles["CompBody"]), Paragraph("Scale: [0.0, 2.0]", self.styles["CompBody"]), Paragraph("L2 distance between unit-normalized spectra", self.styles["CompBody"])],
        ]
        t_spec = Table(spec_table, colWidths=[col_w * 0.25, col_w * 0.16, col_w * 0.16, col_w * 0.17, col_w * 0.26])
        t_spec.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(t_spec)
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<i>Evaluated up to shared Nyquist ceiling: {spec.evaluated_frequency_ceiling_hz:.0f} Hz</i>", self.styles["CompDisclaimer"]))
        story.append(Spacer(1, 8))

        # Section 5: Anomaly Timeline Comparison (if available)
        if comparison.anomaly_comparison:
            story.append(Paragraph("5. Signal Anomaly Findings Timeline Comparison", self.styles["CompHeading"]))
            anom = comparison.anomaly_comparison
            anom_table = [
                [Paragraph("<b>Anomaly Detector</b>", self.styles["CompBodyBold"]), Paragraph("<b>Item A Count</b>", self.styles["CompBodyBold"]), Paragraph("<b>Item B Count</b>", self.styles["CompBodyBold"]), Paragraph("<b>Disparity (Δ)</b>", self.styles["CompBodyBold"])],
                [Paragraph("Silence Intervals (< -40 dB RMS)", self.styles["CompBody"]), Paragraph(str(anom.silence_findings_a), self.styles["CompBody"]), Paragraph(str(anom.silence_findings_b), self.styles["CompBody"]), Paragraph(str(abs(anom.silence_findings_a - anom.silence_findings_b)), self.styles["CompBody"])],
                [Paragraph("Amplitude Discontinuities", self.styles["CompBody"]), Paragraph(str(anom.transition_findings_a), self.styles["CompBody"]), Paragraph(str(anom.transition_findings_b), self.styles["CompBody"]), Paragraph(str(abs(anom.transition_findings_a - anom.transition_findings_b)), self.styles["CompBody"])],
                [Paragraph("Spectral Flux Inconsistencies", self.styles["CompBody"]), Paragraph(str(anom.spectral_findings_a), self.styles["CompBody"]), Paragraph(str(anom.spectral_findings_b), self.styles["CompBody"]), Paragraph(str(abs(anom.spectral_findings_a - anom.spectral_findings_b)), self.styles["CompBody"])],
                [Paragraph("<b>Total Flagged Intervals</b>", self.styles["CompBodyBold"]), Paragraph(f"<b>{anom.total_findings_a}</b>", self.styles["CompBodyBold"]), Paragraph(f"<b>{anom.total_findings_b}</b>", self.styles["CompBodyBold"]), Paragraph(f"<b>{abs(anom.total_findings_a - anom.total_findings_b)}</b>", self.styles["CompBodyBold"])],
                [Paragraph("Anomaly Density (events / min)", self.styles["CompBody"]), Paragraph(f"{anom.findings_density_per_min_a:.2f}", self.styles["CompBody"]), Paragraph(f"{anom.findings_density_per_min_b:.2f}", self.styles["CompBody"]), Paragraph(f"Δ = {abs(anom.findings_density_per_min_a - anom.findings_density_per_min_b):.2f}", self.styles["CompBody"])],
            ]
            t_anom = Table(anom_table, colWidths=[col_w * 0.40, col_w * 0.20, col_w * 0.20, col_w * 0.20])
            t_anom.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#475569")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("PADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(t_anom)
            story.append(Spacer(1, 4))
            dist_str_a = ", ".join(str(x) for x in anom.binned_distribution_a)
            dist_str_b = ", ".join(str(x) for x in anom.binned_distribution_b)
            story.append(Paragraph(f"<b>Item A 10-Bin Relative Distribution:</b> <font name='Courier'>[{dist_str_a}]</font>", self.styles["CompDisclaimer"]))
            story.append(Paragraph(f"<b>Item B 10-Bin Relative Distribution:</b> <font name='Courier'>[{dist_str_b}]</font>", self.styles["CompDisclaimer"]))
            story.append(Spacer(1, 8))

        # Section 6: Methodology, Legal Limitations & Examiner Sign-Off
        story.append(KeepTogether([
            Paragraph("6. Forensic Methodology, ISO/IEC 27037 Disclaimers & Examiner Sign-Off", self.styles["CompHeading"]),
            Paragraph(comparison.disclaimer, self.styles["CompDisclaimer"]),
            Spacer(1, 8),
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1")),
            Spacer(1, 6),
            Table([
                [
                    Paragraph("<b>Examining Forensic Specialist:</b> ___________________________", self.styles["CompBody"]),
                    Paragraph("<b>Signature:</b> ___________________________", self.styles["CompBody"]),
                    Paragraph("<b>Date:</b> ______________", self.styles["CompBody"]),
                ]
            ], colWidths=[col_w * 0.4, col_w * 0.4, col_w * 0.2]),
        ]))

        doc.build(story, canvasmaker=ComparisonNumberedCanvas)
        return buffer.getvalue()
