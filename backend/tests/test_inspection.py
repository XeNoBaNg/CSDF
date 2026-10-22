"""Automated test suite for Audio Metadata and Signal Visualizations (Phase 3)."""

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.app.core.config import settings


@pytest.fixture
def wav_evidence_id(client: TestClient, sample_case_id: str, valid_wav_bytes: bytes) -> str:
    """Uploads a valid WAV file and returns its evidence ID."""
    files = {"file": ("inspection_test.wav", io.BytesIO(valid_wav_bytes), "audio/wav")}
    res = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)
    assert res.status_code == 201
    return res.json()["id"]


def test_wav_metadata_extraction(client: TestClient, wav_evidence_id: str):
    """Test 1 & 4: Valid WAV metadata extraction returns accurate container and acoustic properties."""
    res = client.get(f"/api/v1/evidence/{wav_evidence_id}/metadata")
    assert res.status_code == 200
    data = res.json()

    assert data["evidence_id"] == wav_evidence_id
    assert data["integrity_verified"] is True

    # Encoded container properties
    enc = data["encoded_properties"]
    assert enc["format"] == "wav"
    assert enc["file_size_bytes"] > 0
    assert len(enc["sha256_hash"]) == 64

    # Decoded acoustic properties
    dec = data["decoded_properties"]
    assert dec["sample_rate_hz"] == 44100
    assert dec["channels"] == 1
    assert abs(dec["duration_seconds"] - 0.5) < 0.05
    assert dec["total_samples"] == 22050
    assert dec["bit_depth"] == 16


def test_mp3_metadata_extraction(client: TestClient, sample_case_id: str, valid_mp3_bytes: bytes):
    """Test 2: MP3 metadata extraction returns format, duration, and bitrate."""
    files = {"file": ("recording.mp3", io.BytesIO(valid_mp3_bytes), "audio/mpeg")}
    upload_res = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    res = client.get(f"/api/v1/evidence/{evidence_id}/metadata")
    assert res.status_code == 200
    data = res.json()

    assert data["encoded_properties"]["format"] == "mp3"
    assert data["decoded_properties"]["sample_rate_hz"] == 44100
    assert data["decoded_properties"]["channels"] == 2
    assert data["decoded_properties"]["duration_seconds"] > 0


def test_flac_metadata_extraction(client: TestClient, sample_case_id: str, valid_flac_bytes: bytes):
    """Test 3: FLAC metadata extraction returns format and decoded properties."""
    files = {"file": ("lossless.flac", io.BytesIO(valid_flac_bytes), "audio/flac")}
    upload_res = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    res = client.get(f"/api/v1/evidence/{evidence_id}/metadata")
    assert res.status_code == 200
    data = res.json()

    assert data["encoded_properties"]["format"] == "flac"
    assert data["decoded_properties"]["sample_rate_hz"] == 44100
    assert data["decoded_properties"]["channels"] == 1
    assert abs(data["decoded_properties"]["duration_seconds"] - 0.5) < 0.05


def test_waveform_consistency_and_envelope(client: TestClient, wav_evidence_id: str):
    """Test 5: Waveform values and timestamps are mathematically consistent and finite."""
    res = client.get(f"/api/v1/evidence/{wav_evidence_id}/waveform?point_budget=500")
    assert res.status_code == 200
    data = res.json()

    assert data["evidence_id"] == wav_evidence_id
    assert len(data["time_axis"]) <= 500
    assert len(data["channels"]) == 1

    ch = data["channels"][0]
    assert len(ch["min_amplitudes"]) == len(data["time_axis"])
    assert len(ch["max_amplitudes"]) == len(data["time_axis"])

    # Ensure min <= max across every window
    for min_val, max_val in zip(ch["min_amplitudes"], ch["max_amplitudes"]):
        assert min_val <= max_val + 1e-4

    # Peak amplitude and RMS must be bounded
    assert 0.0 <= data["peak_amplitude"] <= 1.0
    assert 0.0 <= data["rms_energy"] <= 1.0


def test_waveform_point_budget_enforcement(client: TestClient, wav_evidence_id: str):
    """Test 6: Requested point budget is strictly enforced."""
    for budget in [50, 100, 250]:
        res = client.get(f"/api/v1/evidence/{wav_evidence_id}/waveform?point_budget={budget}")
        assert res.status_code == 200
        data = res.json()
        assert len(data["time_axis"]) <= budget


def test_spectrogram_axes_and_finite_values(client: TestClient, wav_evidence_id: str):
    """Test 7: Spectrogram returns matching time and frequency axes and strictly finite dB values."""
    res = client.get(
        f"/api/v1/evidence/{wav_evidence_id}/spectrogram?n_fft=1024&hop_length=512&max_time_frames=100&max_freq_bins=64"
    )
    assert res.status_code == 200
    data = res.json()

    assert data["evidence_id"] == wav_evidence_id
    assert data["unit"] == "dB"
    assert len(data["freq_axis"]) <= 64
    assert len(data["time_axis"]) <= 100

    matrix = data["magnitudes_db"]
    assert len(matrix) == len(data["freq_axis"])
    assert len(matrix[0]) == len(data["time_axis"])

    # Verify all matrix values are finite numbers
    for row in matrix:
        for val in row:
            assert isinstance(val, (int, float))
            assert val <= data["max_db"] + 1e-4
            assert val >= data["min_db"] - 1e-4


def test_frequency_spectrum_axes_and_nyquist(client: TestClient, wav_evidence_id: str):
    """Test 8: Frequency spectrum respects Nyquist bound and strictly increasing frequency axis."""
    res = client.get(f"/api/v1/evidence/{wav_evidence_id}/spectrum?max_bins=128")
    assert res.status_code == 200
    data = res.json()

    assert data["sample_rate_hz"] == 44100
    assert data["nyquist_hz"] == 22050.0
    assert len(data["frequencies_hz"]) <= 128
    assert len(data["frequencies_hz"]) == len(data["magnitudes_db"])

    # Frequencies must be increasing and <= Nyquist
    freqs = data["frequencies_hz"]
    for i in range(len(freqs) - 1):
        assert freqs[i] < freqs[i + 1]
        assert freqs[i] <= data["nyquist_hz"]


def test_silent_audio_finite_handling(client: TestClient, sample_case_id: str, silent_wav_bytes: bytes):
    """Test 9: Digital silence does not produce NaN or infinite values in spectrogram or spectrum."""
    files = {"file": ("silence.wav", io.BytesIO(silent_wav_bytes), "audio/wav")}
    upload_res = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    # Spectrogram of silence
    spec_res = client.get(f"/api/v1/evidence/{evidence_id}/spectrogram")
    assert spec_res.status_code == 200
    matrix = spec_res.json()["magnitudes_db"]
    for row in matrix:
        for val in row:
            assert isinstance(val, (int, float))
            assert val != float("inf") and val != float("-inf")

    # Spectrum of silence
    spectrum_res = client.get(f"/api/v1/evidence/{evidence_id}/spectrum")
    assert spectrum_res.status_code == 200
    mags = spectrum_res.json()["magnitudes_db"]
    for m in mags:
        assert isinstance(m, (int, float))
        assert m != float("inf") and m != float("-inf")


def test_very_short_audio_handling(client: TestClient, sample_case_id: str, very_short_wav_bytes: bytes):
    """Test 10: Signal shorter than n_fft window is zero-padded safely without crash."""
    files = {"file": ("short.wav", io.BytesIO(very_short_wav_bytes), "audio/wav")}
    upload_res = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    # Waveform
    wave_res = client.get(f"/api/v1/evidence/{evidence_id}/waveform")
    assert wave_res.status_code == 200

    # Spectrogram
    spec_res = client.get(f"/api/v1/evidence/{evidence_id}/spectrogram")
    assert spec_res.status_code == 200

    # Spectrum
    spectrum_res = client.get(f"/api/v1/evidence/{evidence_id}/spectrum")
    assert spectrum_res.status_code == 200


def test_multichannel_audio_handling(client: TestClient, sample_case_id: str, stereo_wav_bytes: bytes):
    """Test 11: Stereo audio returns 2 waveform channels and cleanly mixes down for STFT."""
    files = {"file": ("stereo.wav", io.BytesIO(stereo_wav_bytes), "audio/wav")}
    upload_res = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    # Waveform has 2 channels
    wave_res = client.get(f"/api/v1/evidence/{evidence_id}/waveform")
    assert wave_res.status_code == 200
    assert len(wave_res.json()["channels"]) == 2

    # Spectrogram processes mixed stereo cleanly
    spec_res = client.get(f"/api/v1/evidence/{evidence_id}/spectrogram")
    assert spec_res.status_code == 200


def test_missing_evidence_rejected(client: TestClient):
    """Test 13: Requesting non-existent evidence ID returns HTTP 404."""
    fake_id = "EVD-20999999-0000-deadbeef"
    for endpoint in ["metadata", "waveform", "spectrogram", "spectrum", "audio"]:
        res = client.get(f"/api/v1/evidence/{fake_id}/{endpoint}")
        assert res.status_code == 404
        assert res.json()["error"]["code"] == "EVIDENCE_NOT_FOUND"


def test_integrity_mismatch_prevents_inspection(
    client: TestClient, sample_case_id: str, valid_wav_bytes: bytes
):
    """Test 14: Tampered evidence bytes trigger integrity failure and refuse inspection."""
    files = {"file": ("tamper_check.wav", io.BytesIO(valid_wav_bytes), "audio/wav")}
    upload_res = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    # Find file and corrupt physical bytes on disk
    evidence_dir = settings.resolved_evidence_dir
    stored = list(evidence_dir.glob(f"{evidence_id}.*"))[0]
    with open(stored, "ab") as f:
        f.write(b"CORRUPT_BYTES")

    # All inspection endpoints must reject tampered evidence with HTTP 400 INTEGRITY_MISMATCH
    for endpoint in ["metadata", "waveform", "spectrogram", "spectrum"]:
        res = client.get(f"/api/v1/evidence/{evidence_id}/{endpoint}")
        assert res.status_code == 400
        data = res.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INTEGRITY_MISMATCH"


def test_resource_limit_enforcement(client: TestClient, wav_evidence_id: str, monkeypatch):
    """Test 15: Audio exceeding configured maximum decoded duration is rejected with 413."""
    # Temporarily set max duration to 0.1s (wav_evidence_id is 0.5s)
    monkeypatch.setattr(settings, "MAX_DECODED_DURATION_SECONDS", 0.1)

    res = client.get(f"/api/v1/evidence/{wav_evidence_id}/metadata")
    assert res.status_code == 413
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "RESOURCE_LIMIT_EXCEEDED"


def test_audio_playback_streaming(client: TestClient, wav_evidence_id: str):
    """Test 17: Audio streaming endpoint streams the evidence file for playback."""
    res = client.get(f"/api/v1/evidence/{wav_evidence_id}/audio")
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/wav"
    assert len(res.content) > 0


def test_dominant_sine_frequency_accuracy(
    client: TestClient, sample_case_id: str, sine_440hz_wav_bytes: bytes
):
    """Test 18: Synthetic 440 Hz sine wave reports dominant peak frequency within 5 Hz tolerance."""
    files = {"file": ("sine_440.wav", io.BytesIO(sine_440hz_wav_bytes), "audio/wav")}
    upload_res = client.post(f"/api/v1/cases/{sample_case_id}/evidence", files=files)
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    res = client.get(f"/api/v1/evidence/{evidence_id}/spectrum?max_bins=1024")
    assert res.status_code == 200
    data = res.json()

    dominant_freq = data["dominant_frequency_hz"]
    assert dominant_freq is not None
    # Verify reported dominant frequency is within 5 Hz of 440 Hz
    assert abs(dominant_freq - 440.0) <= 5.0, f"Expected ~440 Hz, got {dominant_freq} Hz"
