"""SQLite database connection and schema initialization for AudioSleuth."""

import contextlib
import logging
from pathlib import Path
import sqlite3
from typing import Generator, Optional
from backend.app.core.config import settings

logger = logging.getLogger("audiosleuth.database")


def get_db_path(override_path: Optional[str] = None) -> Path:
    """Resolves the SQLite database file path."""
    if override_path:
        db_path = Path(override_path)
    else:
        # Extract relative path from sqlite:/// URI
        uri = settings.DATABASE_URL
        if uri.startswith("sqlite:///"):
            raw_path = uri.replace("sqlite:///", "")
        else:
            raw_path = "./data/audiosleuth.db"
        db_path = Path(raw_path)
        if not db_path.is_absolute():
            db_path = (settings.BASE_DIR / db_path).resolve()

    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def init_db(override_path: Optional[str] = None) -> None:
    """Initializes tables and indices in the SQLite database."""
    db_path = get_db_path(override_path)
    logger.info("Initializing AudioSleuth SQLite database at: %s", db_path)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()

        # 1. Cases Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                investigator_name TEXT NOT NULL,
                notes TEXT,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)

        # Migration: ensure status and description columns exist if cases table was pre-existing
        cursor.execute("PRAGMA table_info(cases);")
        existing_case_cols = [row[1] for row in cursor.fetchall()]
        if "description" not in existing_case_cols:
            cursor.execute("ALTER TABLE cases ADD COLUMN description TEXT;")
            cursor.execute("UPDATE cases SET description = notes WHERE description IS NULL AND notes IS NOT NULL;")
        if "status" not in existing_case_cols:
            cursor.execute("ALTER TABLE cases ADD COLUMN status TEXT NOT NULL DEFAULT 'active';")

        # 2. Evidence Items Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence_items (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL,
                sha256_hash TEXT NOT NULL,
                format TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                ingested_at TEXT NOT NULL,
                integrity_status TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
            );
        """)

        # 3. Durable Audit Events Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                outcome TEXT NOT NULL,
                case_id TEXT,
                evidence_id TEXT,
                details TEXT,
                FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE SET NULL,
                FOREIGN KEY (evidence_id) REFERENCES evidence_items (id) ON DELETE SET NULL
            );
        """)

        # 4. Cross-Recording Forensic Comparisons Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comparisons (
                id TEXT PRIMARY KEY,
                evidence_id_a TEXT NOT NULL,
                evidence_id_b TEXT NOT NULL,
                case_id_a TEXT,
                case_id_b TEXT,
                hash_a TEXT NOT NULL,
                hash_b TEXT NOT NULL,
                metrics_summary TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (evidence_id_a) REFERENCES evidence_items (id) ON DELETE CASCADE,
                FOREIGN KEY (evidence_id_b) REFERENCES evidence_items (id) ON DELETE CASCADE
            );
        """)

        # 5. Create indices for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cases_status ON cases (status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_case_id ON evidence_items (case_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_hash ON evidence_items (sha256_hash);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_case_id ON audit_events (case_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_evidence_id ON audit_events (evidence_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events (timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_events (action);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comparisons_a ON comparisons (evidence_id_a);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comparisons_b ON comparisons (evidence_id_b);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comparisons_created ON comparisons (created_at);")
        conn.commit()
    logger.info("Database schema initialized successfully.")


@contextlib.contextmanager
def get_db_connection(override_path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager providing a configured SQLite connection."""
    db_path = get_db_path(override_path)
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()
