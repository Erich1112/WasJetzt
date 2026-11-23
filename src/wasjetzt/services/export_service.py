"""Export sigur în Markdown: fișier temporar + redenumire atomică, fără duplicate sau pierderi."""
from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from wasjetzt import LEGACY_QUESTION
from wasjetzt.database.db import AnswerRecord, Database
from wasjetzt.i18n import tr
from wasjetzt.timeutil import now_local, offset_label


@dataclass
class ExportResult:
    status: str  # "ok" | "nothing" | "error"
    path: Path | None = None
    count: int = 0
    error: str = ""


def check_directory_writable(directory: str | Path) -> str | None:
    """Returnează None dacă directorul există și poate fi scris, altfel un mesaj de eroare."""
    if not str(directory).strip():
        return tr("dir.not_set")
    path = Path(directory)
    if not path.exists():
        return tr("dir.missing")
    if not path.is_dir():
        return tr("dir.not_a_dir")
    probe = path / f".wasjetzt-write-test-{os.getpid()}"
    try:
        with open(probe, "wb") as handle:
            handle.write(b"ok")
        probe.unlink()
    except OSError as exc:
        return tr("dir.not_writable", error=exc.strerror or str(exc))
    return None


def _quote(text: str) -> list[str]:
    """Citează fiecare linie, ca textul utilizatorului să nu poată crea titluri în structura exportului."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return [f"> {line}" if line else ">" for line in lines]


def render_markdown(rows: list[AnswerRecord], exported_at: datetime) -> str:
    out = ["# Răspunsuri – WasJetzt", "", f"Exportat la: {exported_at.isoformat(timespec='seconds')}", ""]
    current_date = None
    for row in sorted(rows, key=lambda r: (r.created_at_utc, r.id)):
        local = datetime.fromisoformat(row.created_at_local)
        day = local.date().isoformat()
        if day != current_date:
            out += [f"## {day}", ""]
            current_date = day
        label = row.timezone or offset_label(local)
        out += [f"### {local:%H:%M:%S} ({label})", ""]
        q_text = row.question_text if row.question_text else LEGACY_QUESTION
        out += [f"**Întrebare:** {q_text}", ""]
        out += _quote(row.answer)
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


class ExportService:
    def __init__(self, db: Database, directory_getter: Callable[[], str],
                 clock: Callable[[], datetime] = now_local):
        self._db = db
        self._directory = directory_getter
        self._clock = clock
        self._lock = threading.Lock()

    def export(self) -> ExportResult:
        with self._lock:
            rows = self._db.unexported_answers()
            if not rows:
                return ExportResult("nothing")
            directory = Path(self._directory() or "")
            problem = check_directory_writable(directory)
            if problem:
                return ExportResult("error", error=problem)
            now = self._clock()
            content = render_markdown(rows, now).encode("utf-8")
            final = self._unique_path(directory, now)
            tmp = directory / f".{final.name}.tmp"
            try:
                with open(tmp, "wb") as handle:
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(tmp, final)
                if final.read_bytes() != content:
                    raise OSError("verificarea fișierului scris a eșuat")
            except OSError as exc:
                self._cleanup(tmp)
                return ExportResult("error", error=exc.strerror or str(exc))
            try:
                self._db.mark_exported([r.id for r in rows], str(final), now.isoformat(timespec="seconds"))
            except Exception as exc:  # fișierul există, dar baza de date nu a fost actualizată
                return ExportResult("error", path=final, error=tr("db.error", error=exc))
            return ExportResult("ok", path=final, count=len(rows))

    @staticmethod
    def _unique_path(directory: Path, now: datetime) -> Path:
        base = f"raspunsuri_{now:%Y-%m-%d_%H%M%S}"
        candidate = directory / f"{base}.md"
        counter = 2
        while candidate.exists():
            candidate = directory / f"{base}_{counter}.md"
            counter += 1
        return candidate

    @staticmethod
    def _cleanup(tmp: Path) -> None:
        try:
            tmp.unlink()
        except OSError:
            pass
