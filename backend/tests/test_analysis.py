"""Comprehensive unit and integration tests for Phase 4 explainable signal anomaly detectors."""

import io
from pathlib import Path
import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient
from backend.app.analysis.silence import detect_silence_intervals
from backend.app.analysis.spectral import detect_spectral_inconsistencies
from backend.app.analysis.transitions import detect_amplitude_transitions
from backend.app.core.config import settings
from backend.app.evidence.storage import get_evidence_file_path
from backend.app.schemas.analysis import (
    AnalysisRequest,
    FindingCategory,
    ReviewPriority,
    SilenceDetectionParams,
    SpectralDetectionParams,
    TransitionDetectionParams,
)


# =========================================================================
# Detector A: Silence and Low-Energy Interval Tests
# =========================================================================


def test_silence_detector_pure_silence():
    """Verifies that pure digital zeros are detected as a continuous silence interval."""
    sr = 44100
    samples = np.zeros(sr * 2, dtype=np.float32)  # 2.0s of digital silence
    params = SilenceDetectionParams(
        rms_threshold=0.01,
        min_silence_duration_seconds=0.25,
    )

    findings = detect_silence_intervals(
        samples=samples,
        sample_rate=sr,
        evidence_id="EVD-TEST-SILENCE-01",
        source_sha256="test-sha256-hash",
        params=params,
    )

    assert len(findings) == 1
    f = findings[0]
    assert f.category == FindingCategory.SILENCE
    assert f.priority == ReviewPriority.MEDIUM  # Digital zero flagged as medium
    assert f.start_time == 0.0
    assert abs(f.end_time - 2.0) <= 0.05
    assert f.measured_value == 0.0
    assert "digital silence" in f.explanation.lower()
    assert "not definitive proof" in f.disclaimer.lower()


def test_silence_detector_known_interval():
    """Verifies that a known silent interval between two active tones is accurately localized."""
    sr = 44100
    # 0.5s tone (440 Hz) + 0.6s silence + 0.5s tone (440 Hz) = 1.6s total
    t1 = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    tone1 = 0.6 * np.sin(2 * np.pi * 440.0 * t1)
    silence = np.zeros(int(sr * 0.6))
    t2 = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    tone2 = 0.6 * np.sin(2 * np.pi * 440.0 * t2)

    signal = np.concatenate([tone1, silence, tone2]).astype(np.float32)

    params = SilenceDetectionParams(
        window_duration_seconds=0.05,
        hop_duration_seconds=0.025,
        rms_threshold=0.01,
        min_silence_duration_seconds=0.3,
    )

    findings = detect_silence_intervals(
        samples=signal,
        sample_rate=sr,
        evidence_id="EVD-TEST-SILENCE-02",
        source_sha256="test-sha256-hash",
        params=params,
    )

    assert len(findings) == 1
    f = findings[0]
    assert f.category == FindingCategory.SILENCE
    # Expected silence window starts around 0.5s and ends around 1.1s
    assert abs(f.start_time - 0.5) <= 0.06
    assert abs(f.end_time - 1.1) <= 0.06
    assert f.duration_seconds >= 0.5


def test_silence_detector_noise_above_threshold():
    """Verifies that constant background noise above the RMS threshold is not flagged as silence."""
    sr = 44100
    # Random uniform noise with amplitude 0.05 (RMS ~= 0.029, above threshold 0.01)
    np.random.seed(42)
    noise = np.random.uniform(-0.05, 0.05, sr * 1).astype(np.float32)

    params = SilenceDetectionParams(
        rms_threshold=0.01,
        min_silence_duration_seconds=0.25,
    )

    findings = detect_silence_intervals(
        samples=noise,
        sample_rate=sr,
        evidence_id="EVD-TEST-NOISE-01",
        source_sha256="test-sha256-hash",
        params=params,
    )

    assert len(findings) == 0


def test_silence_detector_min_duration_filtering():
    """Verifies that silence intervals shorter than min_silence_duration are filtered out."""
    sr = 44100
    # 0.5s tone + 0.1s silence (too short for 0.3s minimum) + 0.5s tone
    tone = (0.5 * np.sin(2 * np.pi * 440.0 * np.linspace(0, 0.5, int(sr * 0.5)))).astype(np.float32)
    short_silence = np.zeros(int(sr * 0.1), dtype=np.float32)
    signal = np.concatenate([tone, short_silence, tone])

    params = SilenceDetectionParams(
        rms_threshold=0.01,
        min_silence_duration_seconds=0.3,  # Requires at least 0.3s
    )

    findings = detect_silence_intervals(
        samples=signal,
        sample_rate=sr,
        evidence_id="EVD-TEST-SHORT-SILENCE",
        source_sha256="test-sha256-hash",
        params=params,
    )

    assert len(findings) == 0


# =========================================================================
# Detector B: Abrupt Amplitude Transition Tests
# =========================================================================


def test_transition_detector_artificial_discontinuity():
    """Verifies that a sharp step discontinuity is detected with accurate timestamping."""
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    # Continuous sine wave
    signal = 0.4 * np.sin(2 * np.pi * 440.0 * t)
    # Inject deliberate step jump at sample 22050 (T = 0.5s): jump from -0.4 to +0.5 (delta = 0.9)
    split_idx = sr // 2
    signal[split_idx:] += 0.85
    signal = signal.astype(np.float32)

    params = TransitionDetectionParams(
        threshold=0.40,
        min_separation_seconds=0.05,
    )

    findings = detect_amplitude_transitions(
        samples=signal,
        sample_rate=sr,
        evidence_id="EVD-TEST-DISC-01",
        source_sha256="test-sha256-hash",
        params=params,
    )

    assert len(findings) >= 1
    # Check that the primary finding is localized at approximately 0.5s
    discontinuity = [f for f in findings if abs((f.event_time or 0.0) - 0.5) <= 0.02]
    assert len(discontinuity) == 1
    assert discontinuity[0].category == FindingCategory.TRANSITION
    assert discontinuity[0].measured_value >= 0.8
    assert discontinuity[0].priority == ReviewPriority.HIGH


def test_transition_detector_smooth_sine_has_no_false_positives():
    """Verifies that a continuous smooth 440 Hz sine wave generates zero transition findings."""
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    # Max adjacent difference in 440Hz wave at amplitude 0.7 is roughly 2*pi*440/44100 * 0.7 ~= 0.044
    signal = (0.7 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)

    params = TransitionDetectionParams(threshold=0.35)

    findings = detect_amplitude_transitions(
        samples=signal,
        sample_rate=sr,
        evidence_id="EVD-TEST-SMOOTH",
        source_sha256="test-sha256-hash",
        params=params,
    )

    assert len(findings) == 0


def test_transition_detector_temporal_suppression():
    """Verifies that multiple adjacent spikes within min_separation_seconds are suppressed into one finding."""
    sr = 44100
    signal = np.zeros(sr, dtype=np.float32)
    # Inject two sharp spikes separated by only 200 samples (4.5 ms)
    signal[10000] = 0.8
    signal[10001] = 0.0
    signal[10150] = 0.9
    signal[10151] = 0.0

    params = TransitionDetectionParams(
        threshold=0.35,
        min_separation_seconds=0.05,  # 50 ms separation window
    )

    findings = detect_amplitude_transitions(
        samples=signal,
        sample_rate=sr,
        evidence_id="EVD-TEST-SUPPRESSION",
        source_sha256="test-sha256-hash",
        params=params,
    )

    # Clustered into single peak rather than multiple duplicates
    assert len(findings) == 1


# =========================================================================
# Detector C: Spectral Flux Inconsistency Tests
# =========================================================================


def test_spectral_flux_stable_sine_has_no_false_positives():
    """Verifies that a stationary continuous sine wave produces zero spectral flux peaks."""
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    signal = (0.7 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)

    params = SpectralDetectionParams(
        n_fft=1024,
        hop_length=256,
        threshold=0.40,
    )

    findings = detect_spectral_inconsistencies(
        samples=signal,
        sample_rate=sr,
        evidence_id="EVD-TEST-STABLE-SPECTRAL",
        source_sha256="test-sha256-hash",
        params=params,
    )

    assert len(findings) == 0


def test_spectral_flux_frequency_transition_detected():
    """Verifies that a sudden frequency jump (440 Hz to 2500 Hz) triggers a spectral flux anomaly."""
    sr = 44100
    t1 = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    t2 = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    tone1 = 0.7 * np.sin(2 * np.pi * 440.0 * t1)
    tone2 = 0.7 * np.sin(2 * np.pi * 2500.0 * t2)

    signal = np.concatenate([tone1, tone2]).astype(np.float32)

    params = SpectralDetectionParams(
        n_fft=1024,
        hop_length=256,
        threshold=0.30,
        min_separation_seconds=0.1,
    )

    findings = detect_spectral_inconsistencies(
        samples=signal,
        sample_rate=sr,
        evidence_id="EVD-TEST-FREQ-JUMP",
        source_sha256="test-sha256-hash",
        params=params,
    )

    assert len(findings) >= 1
    transition = [f for f in findings if abs((f.event_time or 0.0) - 0.5) <= 0.08]
    assert len(transition) == 1
    assert transition[0].category == FindingCategory.SPECTRAL
    assert transition[0].measured_value >= 0.30


def test_spectral_flux_silence_and_short_audio_safe():
    """Verifies that pure silence and ultra-short audio return empty lists without crashing."""
    sr = 44100
    silence = np.zeros(sr, dtype=np.float32)
    short = np.array([0.1, 0.2, 0.3], dtype=np.float32)

    findings_silence = detect_spectral_inconsistencies(
        samples=silence,
        sample_rate=sr,
        evidence_id="EVD-TEST-SILENT-FLUX",
        source_sha256="test-sha256-hash",
    )
    assert len(findings_silence) == 0

    findings_short = detect_spectral_inconsistencies(
        samples=short,
        sample_rate=sr,
        evidence_id="EVD-TEST-SHORT-FLUX",
        source_sha256="test-sha256-hash",
    )
    assert len(findings_short) == 0


# =========================================================================
# API Integration & Evidence Integrity Tests
# =========================================================================


def test_api_analyze_evidence_valid(client: TestClient, sample_case_id: str, valid_wav_bytes: bytes):
    """Verifies end-to-end signal analysis execution via POST /api/v1/evidence/{evidence_id}/analyze."""
    upload_res = client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("test_signal.wav", valid_wav_bytes, "audio/wav")},
    )
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    analyze_res = client.post(f"/api/v1/evidence/{evidence_id}/analyze", json={})
    assert analyze_res.status_code == 200

    data = analyze_res.json()
    assert data["evidence_id"] == evidence_id
    assert data["execution_status"] == "completed"
    assert "summary" in data
    assert data["summary"]["total_findings"] >= 0
    assert data["summary"]["execution_time_ms"] >= 0.0
    assert isinstance(data["findings"], list)


def test_api_analyze_evidence_selective_detectors(
    client: TestClient, sample_case_id: str, silent_wav_bytes: bytes
):
    """Verifies that analysis respects detector selection flags."""
    upload_res = client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("silent.wav", silent_wav_bytes, "audio/wav")},
    )
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    # Run ONLY silence detector
    request_payload = {
        "enable_silence": True,
        "enable_transitions": False,
        "enable_spectral_flux": False,
        "silence_params": {
            "rms_threshold": 0.05,
            "min_silence_duration_seconds": 0.2,
        },
    }
    analyze_res = client.post(f"/api/v1/evidence/{evidence_id}/analyze", json=request_payload)
    assert analyze_res.status_code == 200

    data = analyze_res.json()
    assert data["summary"]["total_findings"] >= 1
    # All findings must be of category 'silence'
    for f in data["findings"]:
        assert f["category"] == "silence"


def test_api_analyze_missing_evidence(client: TestClient):
    """Verifies that analyzing a non-existent evidence ID returns HTTP 404."""
    res = client.post("/api/v1/evidence/EVD-NONEXISTENT-9999/analyze", json={})
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "EVIDENCE_NOT_FOUND"


def test_api_analyze_tampered_evidence_fails_precheck(
    client: TestClient, sample_case_id: str, valid_wav_bytes: bytes
):
    """Verifies that altering stored evidence on disk triggers SHA-256 pre-check failure (HTTP 409)."""
    upload_res = client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("to_tamper.wav", valid_wav_bytes, "audio/wav")},
    )
    assert upload_res.status_code == 201
    ev_data = upload_res.json()
    evidence_id = ev_data["id"]

    # Tamper with the physical file on disk
    evidence_dir = settings.resolved_evidence_dir
    stored = list(evidence_dir.glob(f"{evidence_id}.*"))[0]
    with open(stored, "ab") as f:
        f.write(b"CORRUPTED_BYTES")

    # Analysis must reject tampered evidence to preserve forensic chain-of-custody
    analyze_res = client.post(f"/api/v1/evidence/{evidence_id}/analyze", json={})
    assert analyze_res.status_code == 400
    err = analyze_res.json()["error"]
    assert err["code"] == "INTEGRITY_MISMATCH"


def test_api_analyze_invalid_parameters_rejected(
    client: TestClient, sample_case_id: str, valid_wav_bytes: bytes
):
    """Verifies that out-of-range or invalid parameters fail validation with HTTP 422."""
    upload_res = client.post(
        f"/api/v1/cases/{sample_case_id}/evidence",
        files={"file": ("param_check.wav", valid_wav_bytes, "audio/wav")},
    )
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    # Negative threshold should be rejected by Pydantic validation
    invalid_payload = {
        "silence_params": {
            "rms_threshold": -0.5,
        }
    }
    analyze_res = client.post(f"/api/v1/evidence/{evidence_id}/analyze", json=invalid_payload)
    assert analyze_res.status_code == 422
