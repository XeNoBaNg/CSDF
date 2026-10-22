"""Comprehensive unit and integration tests for Phase 5 Case Management and Durable Audit Trail."""

import io
from fastapi.testclient import TestClient
import numpy as np
import pytest
import soundfile as sf
from backend.app.models.case import CaseModel
from backend.app.repositories.case_repository import CaseRepository
from backend.app.repositories.database import get_db_connection


def test_create_case_success(client: TestClient):
    """Verifies that a valid case is created with active status and records an audit event."""
    payload = {
        "title": "Digital Audio Homicide Investigation #102",
        "investigator_name": "Special Agent Vance",
        "notes": "Recovered voice recorder from crime scene",
        "description": "Examine 911 dispatch audio for edit points and splices",
    }
    res = client.post("/api/v1/cases", json=payload)
    assert res.status_code == 201
    data = res.json()

    assert data["id"].startswith("CASE-")
    assert data["title"] == payload["title"]
    assert data["investigator_name"] == payload["investigator_name"]
    assert data["status"] == "active"
    assert data["evidence_count"] == 0
    assert "created_at" in data
    assert "updated_at" in data

    # Verify audit event was created
    audit_res = client.get(f"/api/v1/cases/{data['id']}/audit")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["total"] >= 1
    actions = [e["action"] for e in audit_data["items"]]
    assert "case_created" in actions


def test_create_case_validation_errors(client: TestClient):
    """Verifies that invalid payloads are rejected with 422 Unprocessable Entity."""
    # Missing required title and investigator_name
    res = client.post("/api/v1/cases", json={})
    assert res.status_code == 422

    # Title too short
    res_short = client.post("/api/v1/cases", json={"title": "A", "investigator_name": "Examiner"})
    assert res_short.status_code == 422


def test_get_case_details(client: TestClient, sample_case_id: str):
    """Verifies retrieval of registered case details."""
    res = client.get(f"/api/v1/cases/{sample_case_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == sample_case_id
    assert data["status"] == "active"


def test_get_nonexistent_case_rejected(client: TestClient):
    """Verifies that querying a non-existent case ID returns HTTP 404 CASE_NOT_FOUND."""
    res = client.get("/api/v1/cases/CASE-NONEXISTENT-9999")
    assert res.status_code == 404
    err = res.json()["error"]
    assert err["code"] == "CASE_NOT_FOUND"


def test_update_case_metadata(client: TestClient, sample_case_id: str):
    """Verifies updating case title, description, and notes via PATCH /api/v1/cases/{id}."""
    update_payload = {
        "title": "Renamed Case Title - Forensic Follow-up",
        "description": "Updated scope with secondary suspect audio",
        "investigator_name": "Senior Detective Harper",
    }
    patch_res = client.patch(f"/api/v1/cases/{sample_case_id}", json=update_payload)
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["title"] == update_payload["title"]
    assert data["description"] == update_payload["description"]
    assert data["investigator_name"] == update_payload["investigator_name"]

    # Verify audit event recorded
    audit_res = client.get(f"/api/v1/cases/{sample_case_id}/audit")
    assert audit_res.status_code == 200
    actions = [e["action"] for e in audit_res.json()["items"]]
    assert "case_updated" in actions


def test_case_status_lifecycle_close_and_reopen(client: TestClient, sample_case_id: str):
    """Verifies closing a case and reopening it with explicit status updates and audit events."""
    # 1. Close Case
    close_res = client.post(
        f"/api/v1/cases/{sample_case_id}/status",
        json={"status": "closed", "reason": "Investigation completed and report filed"},
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "closed"

    # 2. Reopen Case
    reopen_res = client.post(
        f"/api/v1/cases/{sample_case_id}/status",
        json={"status": "active", "reason": "New audio evidence discovered"},
    )
    assert reopen_res.status_code == 200
    assert reopen_res.json()["status"] == "active"

    # 3. Verify audit events contain both transitions
    audit_res = client.get(f"/api/v1/cases/{sample_case_id}/audit")
    assert audit_res.status_code == 200
    actions = [e["action"] for e in audit_res.json()["items"]]
    assert "case_closed" in actions
    assert "case_reopened" in actions


def test_case_status_filtering_in_list(client: TestClient):
    """Verifies listing cases filtered by status ('active', 'closed', 'all')."""
    # Create an active case
    c1 = client.post(
        "/api/v1/cases",
        json={"title": "Active Filter Case", "investigator_name": "Examiner 1"},
    ).json()

    # Create and close a second case
    c2 = client.post(
        "/api/v1/cases",
        json={"title": "Closed Filter Case", "investigator_name": "Examiner 2"},
    ).json()
    client.post(f"/api/v1/cases/{c2['id']}/status", json={"status": "closed"})

    # Query active
    active_res = client.get("/api/v1/cases?status=active")
    assert active_res.status_code == 200
    active_ids = [c["id"] for c in active_res.json()["cases"]]
    assert c1["id"] in active_ids
    assert c2["id"] not in active_ids

    # Query closed
    closed_res = client.get("/api/v1/cases?status=closed")
    assert closed_res.status_code == 200
    closed_ids = [c["id"] for c in closed_res.json()["cases"]]
    assert c2["id"] in closed_ids
    assert c1["id"] not in closed_ids

    # Query all
    all_res = client.get("/api/v1/cases?status=all")
    assert all_res.status_code == 200
    all_ids = [c["id"] for c in all_res.json()["cases"]]
    assert c1["id"] in all_ids
    assert c2["id"] in all_ids


def test_upload_evidence_to_closed_case_rejected(
    client: TestClient, sample_case_id: str, valid_wav_bytes: bytes
):
    """Verifies that attempting to upload evidence into a closed case is rejected (HTTP 400 CASE_CLOSED)."""
    # Close the case
    client.post(f"/api/v1/cases/{sample_case_id}/status", json={"status": "closed"})

    # Attempt to ingest evidence
    upload_res = client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("blocked.wav", valid_wav_bytes, "audio/wav")},
    )
    assert upload_res.status_code == 400
    assert upload_res.json()["error"]["code"] == "CASE_CLOSED"

    # Reopen case and verify upload succeeds
    client.post(f"/api/v1/cases/{sample_case_id}/status", json={"status": "active"})
    success_res = client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("allowed.wav", valid_wav_bytes, "audio/wav")},
    )
    assert success_res.status_code == 201


def test_case_evidence_listing_and_counts(
    client: TestClient, sample_case_id: str, valid_wav_bytes: bytes
):
    """Verifies listing evidence items belonging to a case and accurate evidence counts."""
    # Upload 2 evidence items
    client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("clip1.wav", valid_wav_bytes, "audio/wav")},
    )
    client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("clip2.wav", valid_wav_bytes, "audio/wav")},
    )

    list_res = client.get(f"/api/v1/cases/{sample_case_id}/evidence")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert len(items) >= 2

    # Check case evidence_count field
    case_res = client.get(f"/api/v1/cases/{sample_case_id}")
    assert case_res.status_code == 200
    assert case_res.json()["evidence_count"] >= 2


def test_audit_trail_system_queries(client: TestClient, sample_case_id: str, valid_wav_bytes: bytes):
    """Verifies system-wide audit querying, pagination, and action filtering."""
    # Trigger evidence upload and integrity verification to generate audit records
    upload_res = client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("audit_test.wav", valid_wav_bytes, "audio/wav")},
    )
    evidence_id = upload_res.json()["id"]

    verify_res = client.post(f"/api/v1/evidence/{evidence_id}/verify-integrity")
    assert verify_res.status_code == 200

    # Query system-wide audit
    audit_res = client.get("/api/v1/audit?limit=50")
    assert audit_res.status_code == 200
    data = audit_res.json()
    assert data["total"] > 0
    assert len(data["items"]) > 0
    assert "disclaimer" in data

    # Filter audit by evidence_id
    ev_audit_res = client.get(f"/api/v1/audit?evidence_id={evidence_id}")
    assert ev_audit_res.status_code == 200
    ev_events = ev_audit_res.json()["items"]
    assert len(ev_events) >= 2  # uploaded and integrity verified
    actions = [e["action"] for e in ev_events]
    assert "evidence_uploaded" in actions
    assert "integrity_verified" in actions

    # Retrieve single audit event by ID
    first_event_id = ev_events[0]["id"]
    single_res = client.get(f"/api/v1/audit/{first_event_id}")
    assert single_res.status_code == 200
    assert single_res.json()["id"] == first_event_id


def test_case_persistence_across_connection_resets(sample_case_id: str):
    """Verifies that case and evidence data persist durably across separate SQLite connections."""
    repo1 = CaseRepository()
    case1 = repo1.get_by_id(sample_case_id)
    assert case1 is not None

    # Connect with a second independent repository instance
    repo2 = CaseRepository()
    case2 = repo2.get_by_id(sample_case_id)
    assert case2 is not None
    assert case2.id == case1.id
    assert case2.title == case1.title
