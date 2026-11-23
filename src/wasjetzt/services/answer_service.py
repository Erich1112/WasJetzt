"""Validarea și salvarea răspunsurilor. Timestamp-ul este cel al momentului salvării."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from wasjetzt.database.db import Database
from wasjetzt.timeutil import now_local, timezone_name


class EmptyAnswerError(ValueError):
    """Răspuns gol sau format doar din spații."""


class AnswerService:
    def __init__(self, db: Database, clock: Callable[[], datetime] = now_local,
                 tz_name: Callable[[datetime], str] = timezone_name):
        self._db = db
        self._clock = clock
        self._tz_name = tz_name

    def save(self, text: str, prompt_shown_at: datetime | None = None,
             scheduled_for: datetime | None = None, source: str = "scheduled",
             question_id: str | None = None, question_text: str | None = None,
             question_language: str | None = None) -> int:
        cleaned = (text or "").strip()
        if not cleaned:
            raise EmptyAnswerError("empty answer")
        now = self._clock()
        if now.tzinfo is None:
            now = now.astimezone()
        return self._db.add_answer(
            answer=cleaned,
            created_at_local=now.isoformat(timespec="milliseconds"),
            created_at_utc=now.astimezone(timezone.utc).isoformat(timespec="milliseconds"),
            timezone=self._tz_name(now),
            prompt_shown_at=prompt_shown_at.isoformat(timespec="milliseconds") if prompt_shown_at else None,
            scheduled_for=scheduled_for.isoformat(timespec="milliseconds") if scheduled_for else None,
            source=source,
            question_id=question_id,
            question_text=question_text,
            question_language=question_language,
        )
