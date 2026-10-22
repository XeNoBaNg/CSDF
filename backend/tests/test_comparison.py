"""Automated test suite for Phase 6B Cross-Recording Forensic Comparison.

Validates:
- Self-comparison / identical audio (1.0 similarity, byte-level hash match).
- Recordings with different durations, sample rates, and channels.
- Known spectral disparities (low tone vs high tone).
- Missing evidence records rejection (404).
- Tampered evidence pre-check rejection (400 INTEGRITY_MISMATCH).
- Durable audit event emission ('evidence_compared').
- Comparison retrieval and persistence.
- Comparison PDF report generation and download.
- Global evidence listing endpoint.
"""

import io
import soundfile as sf
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.evidence.storage import get_evidence_file_path


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Initializes a clean test environment with temporary database and evidence vault."""
    db_file = tmp_path / "test_comparison.db"
    vault_dir = tmp_path / "evidence_vault"
    vault_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("EVIDENCE_STORAGE_PATH", str(vault_dir))

    from backend.app.core.config import Settings
    fresh_settings = Settings(
        DATABASE_URL=f"sqlite:///{db_file}",
        EVIDENCE_STORAGE_PATH=str(vault_dir),
    )
    monkeypatch.setattr("backend.app.core.config.settings", fresh_settings)
    monkeypatch.setattr("backend.app.evidence.storage.settings", fresh_settings)
    monkeypatch.setattr("backend.app.analysis.decoder.settings", fresh_settings)

    from backend.app.repositories.database import init_db
    init_db(str(db_file))

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def _create_synthetic_wav_bytes(
    freq: float = 440.0,
    duration: float = 1.0,
    sample_rate: int = 44100,
    channels: int = 1,
) -> bytes:
    """Generates synthetic in-memory WAV audio bytes."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    sig = 0.5 * np.sin(2 * np.pi * freq * t)
    if channels == 2:
        sig = np.column_stack([sig, sig])
    buf = io.BytesIO()
    sf.write(buf, sig, sample_rate, format="WAV", subtype="PCM_16")
    return buf.getvalue()


def _upload_test_evidence(client: TestClient, case_id: str, filename: str, wav_bytes: bytes) -> str:
    """Helper to upload an evidence file to a case and return its evidence ID."""
    files = {"file": (filename, io.BytesIO(wav_bytes), "audio/wav")}
    res = client.post(f"/api/v1/cases/{case_id}/evidence", files=files)
    assert res.status_code == 201, f"Upload failed: {res.text}"
    return res.json()["id"]


def test_identical_recordings_comparison(client: TestClient):
    """Test comparing an evidence item against itself produces an exact byte match and 1.0 similarity."""
    case_res = client.post("/api/v1/cases", json={"title": "Self Comparison Case", "investigator_name": "Dr. Watson"})
    case_id = case_res.json()["id"]

    wav_bytes = _create_synthetic_wav_bytes(freq=440.0, duration=1.0, sample_rate=44100)
    evd_id = _upload_test_evidence(client, case_id, "sine440.wav", wav_bytes)

    comp_res = client.post(
        "/api/v1/evidence/compare",
        json={"evidence_id_a": evd_id, "evidence_id_b": evd_id, "include_anomaly_comparison": True},
    )
    assert comp_res.status_code == 200
    data = comp_res.json()

    assert data["evidence_id_a"] == evd_id
    assert data["evidence_id_b"] == evd_id
    meta = data["metadata_comparison"]
    assert meta["sha256_match"] is True
    assert meta["duration_match"] is True
    assert meta["sample_rate_match"] is True
    assert meta["channels_match"] is True
    assert meta["duration_diff_seconds"] == 0.0

    sig = data["signal_comparison"]
    assert sig["envelope_correlation"] == 1.0
    assert sig["peak_amplitude_diff"] == 0.0
    assert sig["rms_energy_diff"] == 0.0

    spec = data["spectral_comparison"]
    assert spec["spectral_cosine_similarity"] == 1.0
    assert spec["spectral_euclidean_distance"] == 0.0

    summary = data["summary"]
    assert summary["byte_match"] is True
    assert summary["transparent_similarity_score"] == 1.0
    assert "Byte-Identical Duplicate" in summary["acoustic_similarity_label"]


def test_different_durations_comparison(client: TestClient):
    """Test comparing recordings with substantially different durations."""
    case_res = client.post("/api/v1/cases", json={"title": "Duration Comparison", "investigator_name": "Inspector Lestrade"})
    case_id = case_res.json()["id"]

    wav_1s = _create_synthetic_wav_bytes(freq=440.0, duration=1.0)
    wav_2s = _create_synthetic_wav_bytes(freq=440.0, duration=2.5)

    evd_a = _upload_test_evidence(client, case_id, "tone_1s.wav", wav_1s)
    evd_b = _upload_test_evidence(client, case_id, "tone_2s.wav", wav_2s)

    comp_res = client.post(
        "/api/v1/evidence/compare",
        json={"evidence_id_a": evd_a, "evidence_id_b": evd_b},
    )
    assert comp_res.status_code == 200
    data = comp_res.json()

    meta = data["metadata_comparison"]
    assert meta["duration_match"] is False
    assert abs(meta["duration_diff_seconds"] - 1.5) < 0.05
    assert meta["sha256_match"] is False

    # Check that a duration warning was emitted
    warnings = data["summary"]["warnings"]
    assert any("duration disparity" in w.lower() for w in warnings)


def test_different_sample_rates_comparison(client: TestClient):
    """Test comparing recordings with different sampling frequencies."""
    case_res = client.post("/api/v1/cases", json={"title": "Sample Rate Comparison", "investigator_name": "Sherlock Holmes"})
    case_id = case_res.json()["id"]

    wav_44k = _create_synthetic_wav_bytes(freq=500.0, sample_rate=44100)
    wav_22k = _create_synthetic_wav_bytes(freq=500.0, sample_rate=22050)

    evd_a = _upload_test_evidence(client, case_id, "sr_44k.wav", wav_44k)
    evd_b = _upload_test_evidence(client, case_id, "sr_22k.wav", wav_22k)

    comp_res = client.post(
        "/api/v1/evidence/compare",
        json={"evidence_id_a": evd_a, "evidence_id_b": evd_b},
    )
    assert comp_res.status_code == 200
    data = comp_res.json()

    meta = data["metadata_comparison"]
    assert meta["sample_rate_match"] is False
    assert meta["sample_rate_hz_a"] == 44100
    assert meta["sample_rate_hz_b"] == 22050

    spec = data["spectral_comparison"]
    # Frequency ceiling should be evaluated up to 11025 Hz (Nyquist of 22050)
    assert spec["evaluated_frequency_ceiling_hz"] == 11025.0

    warnings = data["summary"]["warnings"]
    assert any("sampling rates differ" in w.lower() for w in warnings)


def test_known_spectral_differences(client: TestClient):
    """Test comparing low-frequency sine against high-frequency sine produces clear spectral divergence."""
    case_res = client.post("/api/v1/cases", json={"title": "Spectral Divergence", "investigator_name": "Mycroft"})
    case_id = case_res.json()["id"]

    wav_low = _create_synthetic_wav_bytes(freq=440.0, duration=1.0)
    wav_high = _create_synthetic_wav_bytes(freq=3000.0, duration=1.0)

    evd_low = _upload_test_evidence(client, case_id, "sine_440.wav", wav_low)
    evd_high = _upload_test_evidence(client, case_id, "sine_3000.wav", wav_high)

    comp_res = client.post(
        "/api/v1/evidence/compare",
        json={"evidence_id_a": evd_low, "evidence_id_b": evd_high},
    )
    assert comp_res.status_code == 200
    data = comp_res.json()

    spec = data["spectral_comparison"]
    assert abs(spec["centroid_hz_a"] - 440.0) < 50.0
    assert abs(spec["centroid_hz_b"] - 3000.0) < 100.0
    assert spec["centroid_diff_hz"] > 2000.0
    assert spec["spectral_cosine_similarity"] < 0.1
    assert "Divergent" in data["summary"]["acoustic_similarity_label"]


def test_missing_evidence_returns_404(client: TestClient):
    """Test providing a non-existent evidence ID triggers HTTP 404 EVIDENCE_NOT_FOUND."""
    case_res = client.post("/api/v1/cases", json={"title": "Missing Case", "investigator_name": "Examiner"})
    case_id = case_res.json()["id"]
    wav = _create_synthetic_wav_bytes()
    evd_a = _upload_test_evidence(client, case_id, "audio.wav", wav)

    res = client.post(
        "/api/v1/evidence/compare",
        json={"evidence_id_a": evd_a, "evidence_id_b": "EVD-NONEXISTENT-999"},
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "EVIDENCE_NOT_FOUND"


def test_tampered_evidence_rejected_with_integrity_mismatch(client: TestClient):
    """Test modifying raw disk bytes of evidence B causes comparison to abort with 400 INTEGRITY_MISMATCH."""
    case_res = client.post("/api/v1/cases", json={"title": "Tamper Test Case", "investigator_name": "Auditor"})
    case_id = case_res.json()["id"]
    wav_a = _create_synthetic_wav_bytes(freq=440.0)
    wav_b = _create_synthetic_wav_bytes(freq=880.0)

    evd_a = _upload_test_evidence(client, case_id, "file_a.wav", wav_a)
    evd_b = _upload_test_evidence(client, case_id, "file_b.wav", wav_b)

    # Corrupt evidence B physical disk file
    from backend.app.repositories.evidence_repository import EvidenceRepository
    repo = EvidenceRepository()
    item_b = repo.get_by_id(evd_b)
    file_path = get_evidence_file_path(item_b.stored_filename)

    with open(file_path, "ab") as f:
        f.write(b"MALICIOUS_TAMPERED_BYTES_ADDED")

    res = client.post(
        "/api/v1/evidence/compare",
        json={"evidence_id_a": evd_a, "evidence_id_b": evd_b},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INTEGRITY_MISMATCH"


def test_comparison_audit_event_logged(client: TestClient):
    """Test that executing a comparison records a durable audit event."""
    case_res = client.post("/api/v1/cases", json={"title": "Audit Comparison Case", "investigator_name": "Inspector"})
    case_id = case_res.json()["id"]
    wav = _create_synthetic_wav_bytes()
    evd_a = _upload_test_evidence(client, case_id, "aud1.wav", wav)
    evd_b = _upload_test_evidence(client, case_id, "aud2.wav", wav)

    comp_res = client.post(
        "/api/v1/evidence/compare",
        json={"evidence_id_a": evd_a, "evidence_id_b": evd_b},
    )
    assert comp_res.status_code == 200
    comp_id = comp_res.json()["id"]

    audit_res = client.get(f"/api/v1/cases/{case_id}/audit")
    assert audit_res.status_code == 200
    events = audit_res.json()["items"]
    compared_events = [e for e in events if e["action"] == "evidence_compared"]
    assert len(compared_events) >= 1
    evt = compared_events[0]
    assert evt["outcome"] == "success"
    assert evt["details"]["comparison_id"] == comp_id


def test_get_persisted_comparison_endpoint(client: TestClient):
    """Test retrieving stored comparison records via GET /api/v1/comparisons/{id}."""
    case_res = client.post("/api/v1/cases", json={"title": "Persist Case", "investigator_name": "Lead"})
    case_id = case_res.json()["id"]
    wav = _create_synthetic_wav_bytes()
    evd_a = _upload_test_evidence(client, case_id, "f1.wav", wav)
    evd_b = _upload_test_evidence(client, case_id, "f2.wav", wav)

    post_res = client.post(
        "/api/v1/evidence/compare",
        json={"evidence_id_a": evd_a, "evidence_id_b": evd_b},
    )
    comp_id = post_res.json()["id"]

    get_res = client.get(f"/api/v1/comparisons/{comp_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == comp_id

    # Nonexistent comparison
    not_found_res = client.get("/api/v1/comparisons/COMP-NONEXISTENT")
    assert not_found_res.status_code == 404


def test_comparison_pdf_report_download(client: TestClient):
    """Test generating and downloading a cross-recording comparison PDF report."""
    case_res = client.post("/api/v1/cases", json={"title": "PDF Comparison Case", "investigator_name": "Forensic Specialist"})
    case_id = case_res.json()["id"]
    wav_a = _create_synthetic_wav_bytes(freq=440.0, duration=1.0)
    wav_b = _create_synthetic_wav_bytes(freq=880.0, duration=1.0)
    evd_a = _upload_test_evidence(client, case_id, "item_a.wav", wav_a)
    evd_b = _upload_test_evidence(client, case_id, "item_b.wav", wav_b)

    # 1. Download via POST
    post_pdf_res = client.post(
        "/api/v1/evidence/compare/report",
        json={"evidence_id_a": evd_a, "evidence_id_b": evd_b, "include_anomaly_comparison": True},
    )
    assert post_pdf_res.status_code == 200
    assert post_pdf_res.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in post_pdf_res.headers["content-disposition"]
    pdf_bytes = post_pdf_res.content
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 2000

    comp_id = post_pdf_res.headers["x-comparison-id"]

    # 2. Download via GET /comparisons/{id}/report
    get_pdf_res = client.get(f"/api/v1/comparisons/{comp_id}/report")
    assert get_pdf_res.status_code == 200
    assert get_pdf_res.headers["content-type"] == "application/pdf"
    assert get_pdf_res.content.startswith(b"%PDF-")


def test_global_evidence_listing_endpoint(client: TestClient):
    """Test GET /api/v1/evidence returns all evidence items across cases."""
    case1 = client.post("/api/v1/cases", json={"title": "Case 1", "investigator_name": "Inv 1"}).json()["id"]
    case2 = client.post("/api/v1/cases", json={"title": "Case 2", "investigator_name": "Inv 2"}).json()["id"]

    wav = _create_synthetic_wav_bytes()
    evd1 = _upload_test_evidence(client, case1, "c1.wav", wav)
    evd2 = _upload_test_evidence(client, case2, "c2.wav", wav)

    res = client.get("/api/v1/evidence")
    assert res.status_code == 200
    items = res.json()["items"]
    ids = [it["id"] for it in items]
    assert evd1 in ids
    assert evd2 in ids

    # Filter by case1
    res_c1 = client.get(f"/api/v1/evidence?case_id={case1}")
    assert res_c1.status_code == 200
    items_c1 = res_c1.json()["items"]
    assert len(items_c1) == 1
    assert items_c1[0]["id"] == evd1
