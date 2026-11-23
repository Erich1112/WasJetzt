"""Conexiunea SQLite și operațiile de persistență. Sursa principală de adevăr."""
from __future__ import annotations

import shutil
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from wasjetzt.database import migrations


@dataclass(frozen=True)
class AnswerRecord:
    id: int
    answer: str
    created_at_local: str
    created_at_utc: str
    timezone: str | None
    prompt_shown_at: str | None
    scheduled_for: str | None
    source: str
    exported_at: str | None
    question_id: str | None = None
    question_text: str | None = None
    question_language: str | None = None


_COLUMNS = (
    "id, answer, created_at_local, created_at_utc, timezone, "
    "prompt_shown_at, scheduled_for, source, exported_at, "
    "question_id, question_text, question_language"
)


def _row(row) -> AnswerRecord:
    return AnswerRecord(*row)


class Database:
    def __init__(self, path: Path, backups_dir: Path | None = None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._backups_dir = Path(backups_dir) if backups_dir else self.path.parent / "backups"
        self._lock = threading.RLock()
        existed = self.path.exists() and self.path.stat().st_size > 0
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False, timeout=10)
        self._conn.execute("PRAGMA synchronous = FULL")
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._migrate_with_backup(existed)

    def _migrate_with_backup(self, existed: bool) -> None:
        with self._lock:
            pending = migrations.pending_versions(self._conn)
            if not pending:
                return
            old_version = migrations.current_version(self._conn)
            if existed and old_version > 0:
                self._backups_dir.mkdir(parents=True, exist_ok=True)
                target = self._backups_dir / f"wasjetzt-v{old_version}-{time.strftime('%Y%m%d-%H%M%S')}.db"
                shutil.copy2(self.path, target)
            migrations.migrate(self._conn)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def schema_version(self) -> int:
        with self._lock:
            return migrations.current_version(self._conn)

    def add_answer(
        self,
        answer: str,
        created_at_local: str,
        created_at_utc: str,
        timezone: str | None,
        prompt_shown_at: str | None,
        scheduled_for: str | None,
        source: str,
        question_id: str | None = None,
        question_text: str | None = None,
        question_language: str | None = None,
    ) -> int:
        with self._lock, self._conn:
            cursor = self._conn.execute(
                "INSERT INTO answers (answer, created_at_local, created_at_utc, timezone, "
                "prompt_shown_at, scheduled_for, source, question_id, question_text, question_language) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (answer, created_at_local, created_at_utc, timezone, prompt_shown_at, scheduled_for, source,
                 question_id, question_text, question_language),
            )
            return int(cursor.lastrowid)

    def last_question_id(self) -> str | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT question_id FROM answers WHERE question_id IS NOT NULL ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return row[0] if row else None

    def get_answer(self, answer_id: int) -> AnswerRecord | None:
        with self._lock:
            row = self._conn.execute(f"SELECT {_COLUMNS} FROM answers WHERE id = ?", (answer_id,)).fetchone()
        return _row(row) if row else None

    def list_answers(self, limit: int = 50, offset: int = 0) -> list[AnswerRecord]:
        with self._lock:
            rows = self._conn.execute(
                f"SELECT {_COLUMNS} FROM answers ORDER BY created_at_utc DESC, id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [_row(r) for r in rows]

    def count_answers(self) -> int:
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) FROM answers").fetchone()[0]

    def count_unexported(self) -> int:
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) FROM answers WHERE exported_at IS NULL").fetchone()[0]

    def unexported_answers(self) -> list[AnswerRecord]:
        with self._lock:
            rows = self._conn.execute(
                f"SELECT {_COLUMNS} FROM answers WHERE exported_at IS NULL ORDER BY created_at_utc, id"
            ).fetchall()
        return [_row(r) for r in rows]

    def mark_exported(self, ids: list[int], file_path: str, exported_at: str) -> None:
        """Marchează răspunsurile ca exportate și înregistrează exportul, într-o singură tranzacție."""
        with self._lock, self._conn:
            for start in range(0, len(ids), 500):
                chunk = ids[start : start + 500]
                marks = ",".join("?" * len(chunk))
                self._conn.execute(
                    f"UPDATE answers SET exported_at = ?, export_file = ? "
                    f"WHERE id IN ({marks}) AND exported_at IS NULL",
                    [exported_at, file_path, *chunk],
                )
            self._conn.execute(
                "INSERT INTO exports (exported_at, file_path, answer_count) VALUES (?, ?, ?)",
                (exported_at, file_path, len(ids)),
            )

    def list_exports(self) -> list[tuple[str, str, int]]:
        with self._lock:
            return self._conn.execute(
                "SELECT exported_at, file_path, answer_count FROM exports ORDER BY id"
            ).fetchall()
