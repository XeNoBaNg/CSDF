"""Application configuration module for AudioSleuth backend."""

from pathlib import Path
from typing import List, Union
import json
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """AudioSleuth runtime settings loaded from environment or defaults."""

    # Application Metadata
    APP_NAME: str = "AudioSleuth"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    # Server binding
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Security & CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Storage & Persistence
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    EVIDENCE_STORAGE_DIR: str = "./data/evidence"
    DATABASE_URL: str = "sqlite:///./data/audiosleuth.db"
    MAX_UPLOAD_SIZE_MB: int = 100

    # Audio Inspection Resource Limits (Phase 3)
    MAX_DECODED_DURATION_SECONDS: int = 1800  # 30 minutes maximum
    MAX_WAVEFORM_POINTS: int = 10000
    DEFAULT_WAVEFORM_POINTS: int = 1000
    MAX_SPECTROGRAM_TIME_FRAMES: int = 1000
    DEFAULT_SPECTROGRAM_TIME_FRAMES: int = 250
    MAX_SPECTROGRAM_FREQ_BINS: int = 512
    DEFAULT_SPECTROGRAM_FREQ_BINS: int = 128
    MAX_SPECTRUM_BINS: int = 2048
    DEFAULT_SPECTRUM_BINS: int = 512

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @property
    def resolved_evidence_dir(self) -> Path:
        """Returns the absolute Path for safe evidence storage."""
        path = Path(self.EVIDENCE_STORAGE_DIR)
        if not path.is_absolute():
            path = (self.BASE_DIR / path).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
