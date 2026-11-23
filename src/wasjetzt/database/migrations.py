"""Migrații de schemă SQLite, versionate prin PRAGMA user_version."""
from __future__ import annotations

import sqlite3

MIGRATIONS: dict[int, str] = {
    1: """
    CREATE TABLE answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        answer TEXT NOT NULL CHECK (length(trim(answer)) > 0),
        created_at_local TEXT NOT NULL,
        created_at_utc TEXT NOT NULL,
        timezone TEXT,
        prompt_shown_at TEXT,
        scheduled_for TEXT,
        source TEXT NOT NULL DEFAULT 'scheduled',
        exported_at TEXT,
        export_file TEXT
    );
    CREATE INDEX idx_answers_utc ON answers (created_at_utc);
    CREATE INDEX idx_answers_exported ON answers (exported_at);
    CREATE TABLE exports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exported_at TEXT NOT NULL,
        file_path TEXT NOT NULL,
        answer_count INTEGER NOT NULL
    );
    -- Un răspuns existent nu poate fi suprascris.
    CREATE TRIGGER answers_text_immutable BEFORE UPDATE OF answer ON answers
    BEGIN
        SELECT RAISE(ABORT, 'answers are immutable');
    END;
    """,
    2: """
    ALTER TABLE answers ADD COLUMN question_id TEXT;
    ALTER TABLE answers ADD COLUMN question_text TEXT;
    ALTER TABLE answers ADD COLUMN question_language TEXT;
    """,
}

LATEST_VERSION = max(MIGRATIONS)


def current_version(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def pending_versions(conn: sqlite3.Connection) -> list[int]:
    current = current_version(conn)
    return [v for v in sorted(MIGRATIONS) if v > current]


def migrate(conn: sqlite3.Connection) -> None:
    for version in pending_versions(conn):
        conn.executescript(f"BEGIN;\n{MIGRATIONS[version]}\nPRAGMA user_version = {int(version)};\nCOMMIT;")
