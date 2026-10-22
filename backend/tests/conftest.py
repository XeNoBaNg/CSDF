"""Pytest test configuration, fixtures, and deterministic audio test vectors."""

import io
from pathlib import Path
import shutil
import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient
from backend.app.core.config import settings
from backend.app.main import create_app
from backend.app.repositories.database import init_db


@pytest.fixture(scope="session")
def test_dirs():
    """Sets up isolated test evidence directory and test database."""
    test_storage = settings.BASE_DIR / "data" / "test_evidence"
    test_db = settings.BASE_DIR / "data" / "test_audiosleuth.db"

    # Clean existing test artifacts if any
    if test_storage.exists():
        shutil.rmtree(test_storage, ignore_errors=True)
    test_storage.mkdir(parents=True, exist_ok=True)

    if test_db.exists():
        try:
            test_db.unlink(missing_ok=True)
        except OSError:
            pass

    settings.EVIDENCE_STORAGE_DIR = str(test_storage)
    settings.DATABASE_URL = f"sqlite:///{test_db.as_posix()}"

    # Initialize schema
    init_db(override_path=str(test_db))

    yield {
        "storage": test_storage,
        "db": test_db,
    }

    # Teardown
    try:
        if test_storage.exists():
            shutil.rmtree(test_storage, ignore_errors=True)
    except OSError:
        pass

    try:
        if test_db.exists():
            test_db.unlink(missing_ok=True)
    except OSError:
        pass


@pytest.fixture(scope="session")
def app(test_dirs):
    """Application fixture configured for testing."""
    test_app = create_app()
    return test_app


@pytest.fixture(scope="function")
def client(app):
    """Synchronous test client fixture."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_case_id(client: TestClient) -> str:
    """Creates a registered test case and returns its ID."""
    response = client.post(
        "/api/v1/cases",
        json={
            "title": "Unit Test Forensic Investigation",
            "investigator_name": "Test Forensic Examiner",
            "notes": "Automated test case",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture
def valid_wav_bytes() -> bytes:
    """Generates a canonical, deterministic 0.5s PCM 16-bit 44100Hz WAV binary file."""
    sr = 44100
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    samples = (0.5 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, samples, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


@pytest.fixture
def valid_mp3_bytes() -> bytes:
    """Generates a canonical, deterministic 20-frame MPEG-1 Layer 3 audio stream (128kbps, 44100Hz)."""
    frame_len = 417
    # 0xFFFB = sync (11 bits) + MPEG1 + Layer3 + no CRC; 0x90 = 128kbps, 44.1kHz; 0x64 = stereo
    frame = b"\xff\xfb\x90\x64" + (b"\x00" * (frame_len - 4))
    return frame * 20


@pytest.fixture
def valid_flac_bytes() -> bytes:
    """Generates a canonical, deterministic 0.5s FLAC stream."""
    sr = 44100
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    samples = (0.5 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, samples, sr, format="FLAC")
    return buf.getvalue()


@pytest.fixture
def sine_440hz_wav_bytes() -> bytes:
    """Generates 1.0s of pure 440 Hz sine wave audio at 44100 Hz mono PCM 16-bit."""
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    samples = (0.7 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, samples, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


@pytest.fixture
def stereo_wav_bytes() -> bytes:
    """Generates 0.5s of 2-channel stereo WAV audio (440Hz Left, 880Hz Right)."""
    sr = 44100
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    left = (0.5 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)
    right = (0.5 * np.sin(2 * np.pi * 880.0 * t)).astype(np.float32)
    stereo = np.column_stack((left, right))
    buf = io.BytesIO()
    sf.write(buf, stereo, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


@pytest.fixture
def silent_wav_bytes() -> bytes:
    """Generates 0.5s of digital zero silence WAV audio."""
    sr = 44100
    samples = np.zeros(int(sr * 0.5), dtype=np.float32)
    buf = io.BytesIO()
    sf.write(buf, samples, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


@pytest.fixture
def very_short_wav_bytes() -> bytes:
    """Generates 64 samples of WAV audio (shorter than standard FFT window size 1024)."""
    samples = (0.5 * np.sin(np.linspace(0, 2 * np.pi, 64))).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, samples, 44100, format="WAV", subtype="PCM_16")
    return buf.getvalue()
