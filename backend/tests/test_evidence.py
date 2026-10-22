"""Automated test suite for Evidence Acquisition and Integrity Verification (Phase 2)."""

import hashlib
import io
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.core.config import settings
from backend.app.evidence.storage import get_evidence_file_path


def test_valid_wav_upload(client: TestClient, sample_case_id: str, valid_wav_bytes: bytes):
    """Test 1: Valid WAV upload returns 201 and correct metadata."""
    files = {"file": ("test_recording.wav", io.BytesIO(valid_wav_bytes), "audio/wav")}
    response = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)

    assert response.status_code == 201
    data = response.json()
    assert data["case_id"] == sample_case_id
    assert data["original_filename"] == "test_recording.wav"
    assert data["format"] == "wav"
    assert data["mime_type"] == "audio/wav"
    assert data["file_size_bytes"] == len(valid_wav_bytes)
    assert data["integrity_status"] == "verified"
    assert data["id"].startswith("EVD-")


def test_valid_mp3_upload(client: TestClient, sample_case_id: str, valid_mp3_bytes: bytes):
    """Test 2: Valid MP3 upload with ID3/MPEG header returns 201."""
    files = {"file": ("surveillance_audio.mp3", io.BytesIO(valid_mp3_bytes), "audio/mpeg")}
    response = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)

    assert response.status_code == 201
    data = response.json()
    assert data["format"] == "mp3"
    assert data["mime_type"] == "audio/mpeg"
    assert data["file_size_bytes"] == len(valid_mp3_bytes)


def test_valid_flac_upload(client: TestClient, sample_case_id: str, valid_flac_bytes: bytes):
    """Test 3: Valid FLAC upload with fLaC header returns 201."""
    files = {"file": ("lossless_evidence.flac", io.BytesIO(valid_flac_bytes), "audio/flac")}
    response = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)

    assert response.status_code == 201
    data = response.json()
    assert data["format"] == "flac"
    assert data["mime_type"] == "audio/flac"
    assert data["file_size_bytes"] == len(valid_flac_bytes)


def test_empty_upload_rejected(client: TestClient, sample_case_id: str):
    """Test 4: Empty 0-byte file upload is rejected with 400 Bad Request."""
    files = {"file": ("empty.wav", io.BytesIO(b""), "audio/wav")}
    response = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "MALFORMED_EVIDENCE"
    assert "empty" in data["error"]["message"].lower()


def test_unsupported_extension_rejected(client: TestClient, sample_case_id: str):
    """Test 5: Unsupported file extension is rejected with 415 Unsupported Media Type."""
    files = {"file": ("payload.exe", io.BytesIO(b"MZ\x90\x00..."), "application/octet-stream")}
    response = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)

    assert response.status_code == 415
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_mismatched_file_signature_rejected(client: TestClient, sample_case_id: str):
    """Test 6: File with .wav extension but arbitrary ASCII text content is rejected with 400."""
    fake_wav_content = b"This is plain text disguised as an audio file."
    files = {"file": ("disguised.wav", io.BytesIO(fake_wav_content), "audio/wav")}
    response = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "MALFORMED_EVIDENCE"
    assert "signature" in data["error"]["message"].lower() or "recognized" in data["error"]["message"].lower()


def test_oversized_upload_rejected(client: TestClient, sample_case_id: str, valid_wav_bytes: bytes, monkeypatch):
    """Test 7: Upload exceeding configured MAX_UPLOAD_SIZE_MB is rejected with 413."""
    # Temporarily set MAX_UPLOAD_SIZE_MB to 0 for threshold testing
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 0)

    files = {"file": ("oversized.wav", io.BytesIO(valid_wav_bytes), "audio/wav")}
    response = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)

    assert response.status_code == 413
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_missing_case_rejected(client: TestClient, valid_wav_bytes: bytes):
    """Test 8: Evidence upload to nonexistent case ID returns 404 CASE_NOT_FOUND."""
    nonexistent_id = "CASE-99999999-NOTFOUND"
    files = {"file": ("test.wav", io.BytesIO(valid_wav_bytes), "audio/wav")}
    response = client.post(f"/api/v1/cases/{nonexistent_id}/evidence", files=files)

    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "CASE_NOT_FOUND"


def test_correct_sha256_calculation(client: TestClient, sample_case_id: str, valid_wav_bytes: bytes):
    """Test 9: Registered SHA-256 matches an independently computed hash."""
    expected_hash = hashlib.sha256(valid_wav_bytes).hexdigest().lower()

    files = {"file": ("hash_check.wav", io.BytesIO(valid_wav_bytes), "audio/wav")}
    response = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)

    assert response.status_code == 201
    assert response.json()["sha256_hash"] == expected_hash


def test_integrity_verification_success(client: TestClient, sample_case_id: str, valid_wav_bytes: bytes):
    """Test 10: Integrity verification returns status 'match' for pristine evidence."""
    files = {"file": ("pristine.wav", io.BytesIO(valid_wav_bytes), "audio/wav")}
    upload_res = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)
    evidence_id = upload_res.json()["id"]

    verify_res = client.post(f"/api/v1/evidence/{evidence_id}/verify-integrity")
    assert verify_res.status_code == 200
    data = verify_res.json()

    assert data["evidence_id"] == evidence_id
    assert data["status"] == "match"
    assert data["expected_sha256"] == data["calculated_sha256"]
    assert "disclaimer" in data


def test_integrity_verification_tampering_mismatch(client: TestClient, sample_case_id: str, valid_wav_bytes: bytes):
    """Test 11a: Tampering with stored file produces status 'mismatch' without changing registered digest."""
    files = {"file": ("tamper_target.wav", io.BytesIO(valid_wav_bytes), "audio/wav")}
    upload_res = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)
    evidence_id = upload_res.json()["id"]
    original_digest = upload_res.json()["sha256_hash"]

    # Retrieve physical stored filename from storage directory
    evidence_dir = settings.resolved_evidence_dir
    stored_files = list(evidence_dir.glob(f"{evidence_id}.*"))
    assert len(stored_files) == 1
    target_file = stored_files[0]

    # Tamper by appending corrupted bytes
    with open(target_file, "ab") as f:
        f.write(b"MALICIOUS_TAMPERED_BYTES")

    # Run integrity verification
    verify_res = client.post(f"/api/v1/evidence/{evidence_id}/verify-integrity")
    assert verify_res.status_code == 200
    data = verify_res.json()

    assert data["status"] == "mismatch"
    assert data["expected_sha256"] == original_digest
    assert data["calculated_sha256"] != original_digest

    # Confirm original registered digest in repository was NOT altered
    details_res = client.get(f"/api/v1/evidence/{evidence_id}")
    assert details_res.status_code == 200
    assert details_res.json()["sha256_hash"] == original_digest


def test_integrity_verification_missing_file_unverifiable(client: TestClient, sample_case_id: str, valid_wav_bytes: bytes):
    """Test 11b: Deleted/missing physical evidence file returns status 'unverifiable'."""
    files = {"file": ("missing_target.wav", io.BytesIO(valid_wav_bytes), "audio/wav")}
    upload_res = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)
    evidence_id = upload_res.json()["id"]

    # Delete physical file on disk
    evidence_dir = settings.resolved_evidence_dir
    stored_files = list(evidence_dir.glob(f"{evidence_id}.*"))
    assert len(stored_files) == 1
    stored_files[0].unlink()

    # Run integrity verification
    verify_res = client.post(f"/api/v1/evidence/{evidence_id}/verify-integrity")
    assert verify_res.status_code == 200
    data = verify_res.json()

    assert data["status"] == "unverifiable"
    assert "unverifiable" in data["explanation"].lower()


def test_temp_file_cleanup_on_failure(client: TestClient, sample_case_id: str):
    """Test 12: Failed uploads cleanly remove all temporary files."""
    temp_dir = settings.resolved_evidence_dir / "temp"

    # Count temp files before
    initial_temp_count = len(list(temp_dir.glob("sleuth_upload_*"))) if temp_dir.exists() else 0

    # Attempt malformed upload
    files = {"file": ("corrupt.wav", io.BytesIO(b"NOT_A_WAV_HEADER_DATA"), "audio/wav")}
    response = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)
    assert response.status_code == 400

    # Verify temp files count did not increase
    post_temp_count = len(list(temp_dir.glob("sleuth_upload_*"))) if temp_dir.exists() else 0
    assert post_temp_count == initial_temp_count


def test_path_traversal_sanitization(client: TestClient, sample_case_id: str, valid_wav_bytes: bytes):
    """Test 13: Path traversal sequences in client filename are completely sanitized."""
    traversal_filename = "../../../../../windows/system32/cmd.exe...test.wav"
    files = {"file": (traversal_filename, io.BytesIO(valid_wav_bytes), "audio/wav")}
    response = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)

    assert response.status_code == 201
    data = response.json()
    sanitized = data["original_filename"]

    # Ensure path separators and traversal tokens are eliminated
    assert "/" not in sanitized
    assert "\\" not in sanitized
    assert ".." not in sanitized

    # Confirm physical file in evidence vault exists safely inside evidence vault
    evidence_id = data["id"]
    evidence_dir = settings.resolved_evidence_dir
    stored_files = list(evidence_dir.glob(f"{evidence_id}.*"))
    assert len(stored_files) == 1
    assert stored_files[0].parent.resolve() == evidence_dir.resolve()


def test_api_error_response_consistency(client: TestClient):
    """Test 14: Error responses follow unified envelope with success=False and structured code."""
    response = client.get("/api/v1/evidence/EVD-NONEXISTENT-ITEM")
    assert response.status_code == 404
    data = response.json()

    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "EVIDENCE_NOT_FOUND"
    assert "timestamp" in data["error"]
    assert "message" in data["error"]
