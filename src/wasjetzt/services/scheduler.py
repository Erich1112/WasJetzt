"""Logica de programare, independentă de Qt (testabilă cu un ceas fals).

Aplicația apelează tick() periodic (ex. la 10 s). Nu se recuperează întrebările ratate:
dacă între două tick-uri a trecut mult timp (sleep/hibernate/schimbare de ceas),
următoarea întrebare se reprogramează la un interval întreg și nu apare nicio rafală.
"""
from __future__ import annotations

import time
from typing import Callable

from wasjetzt.config.settings import MAX_INTERVAL, MIN_INTERVAL

TICK_SECONDS = 10
RESUME_GAP_SECONDS = 60  # un tick întârziat cu mai mult de atât = repaus / salt de ceas


class SchedulerCore:
    def __init__(self, interval_minutes: int = 60, on_dismiss: str = "wait_next_interval",
                 retry_minutes: int = 10, max_retries: int = 3,
                 now: Callable[[], float] = time.time):
        self._now = now
        self.interval_minutes = self._check_interval(interval_minutes)
        self.on_dismiss = on_dismiss
        self.retry_minutes = retry_minutes
        self.max_retries = max_retries
        self.paused = False
        self.prompt_open = False
        self.prompt_source: str | None = None
        self.scheduled_for: float | None = None
        self.shown_at: float | None = None
        self.resume_events = 0
        self._retries = 0
        self._last_tick = now()
        self.next_due = now() + self.interval_minutes * 60

    @staticmethod
    def _check_interval(minutes: int) -> int:
        if not MIN_INTERVAL <= minutes <= MAX_INTERVAL:
            raise ValueError(f"interval în afara limitelor: {minutes}")
        return minutes

    def _reschedule(self, minutes: float) -> None:
        self.next_due = self._now() + minutes * 60

    def set_interval(self, minutes: int) -> None:
        self.interval_minutes = self._check_interval(minutes)
        self._retries = 0
        self._reschedule(minutes)

    def configure_dismiss(self, on_dismiss: str, retry_minutes: int) -> None:
        self.on_dismiss = on_dismiss
        self.retry_minutes = retry_minutes

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False
        self._reschedule(self.interval_minutes)

    def tick(self) -> bool:
        """True dacă tocmai a început o întrebare programată (prompt_open devine True)."""
        now = self._now()
        gap = now - self._last_tick
        self._last_tick = now
        if gap < 0 or gap > RESUME_GAP_SECONDS:
            self.resume_events += 1
            self._reschedule(self.interval_minutes)
            return False
        if self.paused or self.prompt_open:
            return False
        if now >= self.next_due:
            return self.begin_prompt("scheduled")
        return False

    def begin_prompt(self, source: str = "scheduled") -> bool:
        """Marchează o fereastră ca deschisă. False dacă una este deja deschisă."""
        if self.prompt_open:
            return False
        self.prompt_open = True
        self.prompt_source = source
        self.shown_at = self._now()
        self.scheduled_for = self.next_due if source == "scheduled" else None
        return True

    def end_prompt(self, answered: bool) -> None:
        if not self.prompt_open:
            return
        source = self.prompt_source
        self.prompt_open = False
        self.prompt_source = None
        now = self._now()
        if source != "scheduled":
            if self.next_due <= now:  # întrebarea manuală nu mută programarea normală
                self._reschedule(self.interval_minutes)
            return
        if answered:
            self._retries = 0
            self._reschedule(self.interval_minutes)
        elif self.on_dismiss == "retry_soon" and self._retries < self.max_retries:
            self._retries += 1
            self._reschedule(min(self.retry_minutes, self.interval_minutes))
        else:
            self._retries = 0
            self._reschedule(self.interval_minutes)
