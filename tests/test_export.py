from datetime import datetime, timedelta, timezone
from unittest import mock

from wasjetzt import LEGACY_QUESTION
from wasjetzt.database.db import Database
from wasjetzt.services.answer_service import AnswerService
from wasjetzt.services.export_service import ExportService, check_directory_writable, render_markdown

TZ = timezone(timedelta(hours=2))


def setup(tmp_path, export_dir=None):
    db = Database(tmp_path / "t.db")
    out = export_dir if export_dir is not None else tmp_path / "out"
    if export_dir is None:
        out.mkdir()
    state = {"now": datetime(2026, 11, 12, 14, 5, 23, tzinfo=TZ)}
    answers = AnswerService(db, clock=lambda: state["now"], tz_name=lambda m: "Europe/Bucharest")
    exporter = ExportService(db, lambda: str(out), clock=lambda: state["now"])
    return db, answers, exporter, out, state


def test_export_creates_utf8_markdown_with_timestamped_name(tmp_path):
    db, answers, exporter, out, state = setup(tmp_path)
    answers.save("Größe testen — ăâîșț")
    result = exporter.export()
    assert result.status == "ok" and result.count == 1
    assert result.path.name == "raspunsuri_2026-11-12_140523.md"
    text = result.path.read_text(encoding="utf-8")
    assert "Größe testen — ăâîșț" in text
    assert "## 2026-11-12" in text and "### 14:05:23 (Europe/Bucharest)" in text
    assert text.startswith("# Răspunsuri – WasJetzt")
    assert f"**Întrebare:** {LEGACY_QUESTION}" in text
    assert db.count_unexported() == 0 and len(db.list_exports()) == 1


def test_only_unexported_and_no_duplicates(tmp_path):
    db, answers, exporter, out, state = setup(tmp_path)
    answers.save("unu")
    first = exporter.export()
    assert exporter.export().status == "nothing"  # nu se creează fișier gol/duplicat
    assert len(list(out.glob("*.md"))) == 1
    state["now"] += timedelta(minutes=30)
    answers.save("doi")
    second = exporter.export()
    assert second.status == "ok" and second.count == 1
    t2 = second.path.read_text("utf-8")
    assert "doi" in t2 and "unu" not in t2
    assert first.path != second.path


def test_same_second_does_not_overwrite_existing_file(tmp_path):
    db, answers, exporter, out, state = setup(tmp_path)
    answers.save("a")
    p1 = exporter.export().path
    answers.save("b")
    p2 = exporter.export().path
    assert p1 != p2 and p1.exists() and p2.exists()


def test_write_error_keeps_records_unexported(tmp_path):
    db, answers, exporter, out, state = setup(tmp_path)
    answers.save("important")
    with mock.patch("wasjetzt.services.export_service.os.replace", side_effect=OSError(5, "I/O error")):
        result = exporter.export()
    assert result.status == "error"
    assert db.count_unexported() == 1 and db.list_exports() == []
    assert not list(out.glob("*.md")) and not list(out.glob(".*.tmp"))
    assert exporter.export().status == "ok"  # reîncercarea reușește, fără pierderi


def test_missing_or_invalid_directory(tmp_path):
    db, answers, exporter, out, state = setup(tmp_path, export_dir=tmp_path / "nu_exista")
    answers.save("x")
    assert exporter.export().status == "error" and db.count_unexported() == 1
    afile = tmp_path / "fisier.txt"
    afile.write_text("x")
    assert check_directory_writable(afile) is not None
    assert check_directory_writable("") is not None
    assert check_directory_writable(tmp_path) is None


def test_markdown_in_answers_cannot_break_structure(tmp_path):
    db, answers, exporter, out, state = setup(tmp_path)
    nasty = "# Titlu fals\n## 2099-01-01\n### 00:00:00 (Fals)\n```\ncod\n---\r\n* lista"
    answers.save(nasty)
    text = exporter.export().path.read_text("utf-8")
    structural = [l for l in text.splitlines() if l.startswith("#")]
    assert structural == ["# Răspunsuri – WasJetzt", "## 2026-11-12", "### 14:05:23 (Europe/Bucharest)"]
    assert "> # Titlu fals" in text and "> ```" in text


def test_render_groups_by_day_and_sorts():
    from wasjetzt.database.db import AnswerRecord

    def rec(i, local, utc):
        return AnswerRecord(i, f"r{i}", local, utc, None, None, None, "scheduled", None)

    rows = [rec(2, "2026-11-13T09:00:00.000+02:00", "2026-11-13T07:00:00.000+00:00"),
            rec(1, "2026-11-12T23:00:00.000+02:00", "2026-11-12T21:00:00.000+00:00")]
    text = render_markdown(rows, datetime(2026, 11, 13, 10, 0, tzinfo=TZ))
    assert text.index("## 2026-11-12") < text.index("## 2026-11-13")
    assert "### 23:00:00 (UTC+02:00)" in text  # fără nume IANA: afișează offset-ul


def test_export_includes_displayed_question_and_legacy_fallback(tmp_path):
    db, answers, exporter, out, state = setup(tmp_path)
    # Răspuns vechi (fără întrebare)
    answers.save("răspuns vechi")
    # Răspuns nou cu întrebare
    answers.save("răspuns nou", question_id="q02", question_text="Was ist heute deine wichtigste Aufgabe?", question_language="de")

    result = exporter.export()
    assert result.status == "ok" and result.count == 2
    text = result.path.read_text("utf-8")
    assert f"**Întrebare:** {LEGACY_QUESTION}" in text
    assert "**Întrebare:** Was ist heute deine wichtigste Aufgabe?" in text
    assert "răspuns vechi" in text
    assert "răspuns nou" in text
