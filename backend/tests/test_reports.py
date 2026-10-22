"""Comprehensive unit and integration tests for Phase 6A Forensic PDF Report Generation."""

from pathlib import Path
import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient
from backend.app.evidence.storage import get_evidence_file_path
from backend.app.repositories.evidence_repository import EvidenceRepository


def test_generate_pdf_report_success(client: TestClient, sample_case_id: str, valid_wav_bytes: bytes):
    """Verifies successful PDF generation and download via GET /api/v1/evidence/{evidence_id}/report."""
    # 1. Upload valid evidence recording
    upload_res = client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("interview_recording.wav", valid_wav_bytes, "audio/wav")},
    )
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    # 2. Request forensic PDF report
    report_res = client.get(f"/api/v1/evidence/{evidence_id}/report")
    assert report_res.status_code == 200

    # 3. Verify content-type and headers
    assert report_res.headers["content-type"] == "application/pdf"
    content_disp = report_res.headers.get("content-disposition", "")
    assert "attachment" in content_disp
    assert f"AudioSleuth_Forensic_Report_{evidence_id}" in content_disp
    assert "x-report-id" in report_res.headers

    # 4. Verify valid PDF binary signature and non-empty size
    pdf_bytes = report_res.content
    assert pdf_bytes.startswith(b"%PDF-"), "Generated response must be a valid PDF document"
    assert len(pdf_bytes) > 15000, "Forensic PDF with visualizations should exceed 15 KB"


def test_generate_pdf_report_post_with_options(
    client: TestClient, sample_case_id: str, valid_wav_bytes: bytes
):
    """Verifies that POST /api/v1/evidence/{evidence_id}/report accepts custom options."""
    upload_res = client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("custody_item.wav", valid_wav_bytes, "audio/wav")},
    )
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    payload = {
        "include_visualizations": True,
        "include_audit": True,
        "run_analysis_if_missing": True,
        "examiner_notes": "Suspected splice point around 0.25 seconds.",
    }
    report_res = client.post(f"/api/v1/evidence/{evidence_id}/report", json=payload)
    assert report_res.status_code == 200
    assert report_res.headers["content-type"] == "application/pdf"
    assert report_res.content.startswith(b"%PDF-")


def test_generate_pdf_report_without_visualizations(
    client: TestClient, sample_case_id: str, valid_wav_bytes: bytes
):
    """Verifies PDF report generation when visualization graphics are omitted."""
    upload_res = client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("text_only.wav", valid_wav_bytes, "audio/wav")},
    )
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    report_res = client.get(f"/api/v1/evidence/{evidence_id}/report?include_visualizations=false")
    assert report_res.status_code == 200
    assert report_res.content.startswith(b"%PDF-")


def test_generate_pdf_report_with_case_validation(
    client: TestClient, sample_case_id: str, valid_wav_bytes: bytes
):
    """Verifies downloading report through case-evidence paired endpoint."""
    upload_res = client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("paired_evidence.wav", valid_wav_bytes, "audio/wav")},
    )
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    report_res = client.get(f"/api/v1/cases/{sample_case_id}/evidence/{evidence_id}/report")
    assert report_res.status_code == 200
    assert report_res.headers["content-type"] == "application/pdf"
    assert report_res.content.startswith(b"%PDF-")


def test_generate_pdf_report_case_evidence_mismatch(
    client: TestClient, sample_case_id: str, valid_wav_bytes: bytes
):
    """Verifies that attempting to download a report for evidence using the wrong case returns 400."""
    # Create Case 1 and upload evidence
    upload_res = client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("case1_audio.wav", valid_wav_bytes, "audio/wav")},
    )
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    # Create Case 2
    case2_res = client.post(
        "/api/v1/cases",
        json={"title": "Unrelated Case", "investigator_name": "Examiner 2"},
    )
    assert case2_res.status_code == 201
    case2_id = case2_res.json()["id"]

    # Try to request Case 1's evidence under Case 2
    report_res = client.get(f"/api/v1/cases/{case2_id}/evidence/{evidence_id}/report")
    assert report_res.status_code == 400
    err = report_res.json()["error"]
    assert err["code"] == "CASE_EVIDENCE_MISMATCH"


def test_generate_pdf_report_missing_evidence(client: TestClient):
    """Verifies that requesting a report for a nonexistent evidence ID returns 404."""
    report_res = client.get("/api/v1/evidence/EVD-DOES-NOT-EXIST/report")
    assert report_res.status_code == 404
    assert report_res.json()["error"]["code"] == "EVIDENCE_NOT_FOUND"


def test_generate_pdf_report_integrity_mismatch_rejected(
    client: TestClient, sample_case_id: str, valid_wav_bytes: bytes
):
    """Verifies that if stored evidence bytes are tampered on disk, report generation is rejected."""
    upload_res = client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("tamper_test.wav", valid_wav_bytes, "audio/wav")},
    )
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    repo = EvidenceRepository()
    evidence_item = repo.get_by_id(evidence_id)
    assert evidence_item is not None

    # Deliberately tamper with file bytes on disk
    stored_path = get_evidence_file_path(evidence_item.stored_filename)
    assert stored_path.exists()
    stored_path.write_bytes(b"CORRUPTED_TAMPERED_BYTES_DISASTER")

    # Attempting to generate a report MUST fail with INTEGRITY_MISMATCH
    report_res = client.get(f"/api/v1/evidence/{evidence_id}/report")
    assert report_res.status_code == 400
    err = report_res.json()["error"]
    assert err["code"] == "INTEGRITY_MISMATCH"
    assert "CRITICAL INTEGRITY FAILURE" in err["message"]


def test_generate_pdf_report_emits_audit_event(
    client: TestClient, sample_case_id: str, valid_wav_bytes: bytes
):
    """Verifies that report generation records a durable 'report_generated' audit event."""
    upload_res = client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("audit_report_test.wav", valid_wav_bytes, "audio/wav")},
    )
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    # Generate PDF report
    report_res = client.get(f"/api/v1/evidence/{evidence_id}/report")
    assert report_res.status_code == 200

    # Query audit trail
    audit_res = client.get(f"/api/v1/cases/{sample_case_id}/audit")
    assert audit_res.status_code == 200
    events = audit_res.json()["items"]

    report_events = [e for e in events if e["action"] == "report_generated" and e["evidence_id"] == evidence_id]
    assert len(report_events) >= 1
    assert report_events[0]["outcome"] == "success"
    assert "report_id" in report_events[0]["details"]
    assert report_events[0]["details"]["size_bytes"] > 0


def test_generate_pdf_report_with_detected_anomalies(
    client: TestClient, sample_case_id: str
):
    """Verifies PDF report generation with deliberately inserted acoustic silence & amplitude steps."""
    sr = 22050
    # Create audio with 0.5s tone, 0.4s digital silence, 0.5s tone with sharp step
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    tone1 = 0.5 * np.sin(2 * np.pi * 440.0 * t)
    silence = np.zeros(int(sr * 0.4), dtype=np.float32)
    tone2 = 0.9 * np.sin(2 * np.pi * 1200.0 * t)
    # introduce a step discontinuity
    tone2[100:105] = -0.9

    signal = np.concatenate([tone1, silence, tone2]).astype(np.float32)
    import io
    buf = io.BytesIO()
    sf.write(buf, signal, sr, format="WAV", subtype="PCM_16")
    wav_bytes = buf.getvalue()

    upload_res = client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("anomalous_audio.wav", wav_bytes, "audio/wav")},
    )
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    # Request report which runs analysis and includes the detected findings
    report_res = client.get(f"/api/v1/evidence/{evidence_id}/report")
    assert report_res.status_code == 200
    assert report_res.content.startswith(b"%PDF-")
    assert len(report_res.content) > 20000
