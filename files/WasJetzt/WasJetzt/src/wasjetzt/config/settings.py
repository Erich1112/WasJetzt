"""Modelul, validarea și persistența setărilor (JSON). Fără dependențe de UI."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field, fields
from pathlib import Path

from wasjetzt.i18n import tr

SCHEMA_VERSION = 1
MIN_INTERVAL = 5
MAX_INTERVAL = 1440
MIN_RETRY = 5
MAX_RETRY = 120
ON_DISMISS_VALUES = ("wait_next_interval", "retry_soon")
SUPPORTED_LANGUAGES = ("ro",)


@dataclass
class Settings:
    schema_version: int = SCHEMA_VERSION
    configured: bool = False
    export_directory: str = ""
    interval_minutes: int = 60
    start_with_system: bool = True
    start_minimized: bool = True
    show_confirmation_notifications: bool = True
    on_dismiss: str = "wait_next_interval"
    retry_minutes: int = 10
    language: str = "ro"
    # Chei necunoscute (adăugate de versiuni viitoare) sunt păstrate la salvare.
    extra: dict = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict:
        data = dict(self.extra)
        for f in fields(self):
            if f.name != "extra":
                data[f.name] = getattr(self, f.name)
        return data


class SettingsError(ValueError):
    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__("; ".join(f"{k}: {v}" for k, v in errors.items()))


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate(s: Settings) -> dict[str, str]:
    """Returnează {câmp: mesaj}; dicționar gol = setări valide."""
    errors: dict[str, str] = {}
    if not _is_int(s.interval_minutes) or not MIN_INTERVAL <= s.interval_minutes <= MAX_INTERVAL:
        errors["interval_minutes"] = tr("err.interval_range", lo=MIN_INTERVAL, hi=MAX_INTERVAL)
    if not _is_int(s.retry_minutes) or not MIN_RETRY <= s.retry_minutes <= MAX_RETRY:
        errors["retry_minutes"] = tr("err.retry_range", lo=MIN_RETRY, hi=MAX_RETRY)
    if s.on_dismiss not in ON_DISMISS_VALUES:
        errors["on_dismiss"] = tr("err.on_dismiss")
    if s.language not in SUPPORTED_LANGUAGES:
        errors["language"] = tr("err.language")
    if not isinstance(s.export_directory, str):
        errors["export_directory"] = tr("err.type")
    for name in ("configured", "start_with_system", "start_minimized", "show_confirmation_notifications"):
        if not isinstance(getattr(s, name), bool):
            errors[name] = tr("err.bool")
    return errors


def from_dict(raw: dict) -> tuple[Settings, dict[str, str]]:
    """Construiește setările; câmpurile invalide revin individual la valoarea implicită."""
    defaults = Settings()
    known = {f.name for f in fields(Settings)} - {"extra"}
    s = Settings()
    for name in known:
        if name in raw:
            setattr(s, name, raw[name])
    s.extra = {k: v for k, v in raw.items() if k not in known}
    errors = validate(s)
    for name in errors:
        setattr(s, name, getattr(defaults, name))
    return s, errors


class SettingsManager:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.first_run = True
        self.load_error: str | None = None
        self.load_warnings: dict[str, str] = {}

    def load(self) -> Settings:
        self.load_error = None
        self.load_warnings = {}
        self.first_run = not self.path.exists()
        if self.first_run:
            return Settings()
        raw_text = None
        last_error: Exception | None = None
        for _ in range(3):  # erori temporare (fișier blocat de antivirus etc.)
            try:
                raw_text = self.path.read_text(encoding="utf-8")
                break
            except OSError as exc:
                last_error = exc
                time.sleep(0.15)
        if raw_text is None:
            self.load_error = str(last_error)
            return Settings()
        try:
            raw = json.loads(raw_text)
            if not isinstance(raw, dict):
                raise ValueError("rădăcina JSON nu este un obiect")
        except ValueError as exc:
            self.load_error = str(exc)
            return Settings()
        settings, self.load_warnings = from_dict(raw)
        return settings

    @property
    def is_configured_on_disk(self) -> bool:
        return not self.first_run and self.load_error is None

    def save(self, settings: Settings) -> None:
        errors = validate(settings)
        if errors:
            raise SettingsError(errors)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.load_error and self.path.exists():
            # Nu pierde un fișier pe care nu l-am putut citi: păstrează o copie.
            backup = self.path.with_name(f"{self.path.name}.bak-{time.strftime('%Y%m%d-%H%M%S')}")
            try:
                shutil.copy2(self.path, backup)
            except OSError:
                pass
        settings.schema_version = SCHEMA_VERSION
        payload = json.dumps(settings.to_dict(), ensure_ascii=False, indent=2)
        fd, tmp_name = tempfile.mkstemp(dir=self.path.parent, prefix=".settings-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
        except OSError:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        self.first_run = False
        self.load_error = None
