import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from wasjetzt.database import migrations
from wasjetzt.database.db import Database
from wasjetzt.services.answer_service import AnswerService, EmptyAnswerError

TZ = timezone(timedelta(hours=2))


def make_service(db, moment):
    return AnswerService(db, clock=lambda: moment, tz_name=lambda m: "Europe/Bucharest")


def test_valid_answer_saved_and_stripped(tmp_path):
    db = Database(tmp_path / "t.db")
    svc = make_service(db, datetime(2026, 11, 12, 14, 5, 23, 123000, tzinfo=TZ))
    rid = svc.save("  scriu cod  ")
    rec = db.get_answer(rid)
    assert rec.answer == "scriu cod" and rec.source == "scheduled" and rec.exported_at is None
    assert rec.question_id is None and rec.question_text is None and rec.question_language is None


def test_timestamp_has_timezone_and_matches_utc(tmp_path):
    db = Database(tmp_path / "t.db")
    moment = datetime(2026, 11, 12, 14, 5, 23, 123000, tzinfo=TZ)
    rec = db.get_answer(make_service(db, moment).save("x"))
    local = datetime.fromisoformat(rec.created_at_local)
    utc = datetime.fromisoformat(rec.created_at_utc)
    assert local.utcoffset() == timedelta(hours=2) and rec.created_at_local.endswith("+02:00")
    assert utc.utcoffset() == timedelta(0) and local == utc == moment
    assert rec.timezone == "Europe/Bucharest"


def test_timestamp_is_save_time_not_prompt_time(tmp_path):
    db = Database(tmp_path / "t.db")
    shown = datetime(2026, 11, 12, 14, 0, 0, tzinfo=TZ)
    saved = datetime(2026, 11, 12, 14, 7, 30, tzinfo=TZ)
    rec = db.get_answer(make_service(db, saved).save("x", prompt_shown_at=shown))
    assert datetime.fromisoformat(rec.created_at_local) == saved
    assert datetime.fromisoformat(rec.prompt_shown_at) == shown


@pytest.mark.parametrize("text", ["", "   ", "\n\t  \n", None])
def test_empty_answers_rejected(tmp_path, text):
    db = Database(tmp_path / "t.db")
    with pytest.raises(EmptyAnswerError):
        make_service(db, datetime.now(TZ)).save(text)
    assert db.count_answers() == 0


def test_answers_never_overwritten(tmp_path):
    db = Database(tmp_path / "t.db")
    svc = make_service(db, datetime(2026, 1, 1, 10, 0, tzinfo=TZ))
    a = svc.save("primul")
    b = svc.save("al doilea")
    assert a != b and db.count_answers() == 2
    conn = sqlite3.connect(db.path)
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("UPDATE answers SET answer = 'modificat' WHERE id = ?", (a,))
    conn.close()
    assert db.get_answer(a).answer == "primul"


def test_unicode_and_german_chars_preserved(tmp_path):
    db = Database(tmp_path / "t.db")
    text = "Ich mache Übungen: Größe, Straße, äöüß — și ăâîșț, 日本語 😀"
    rec = db.get_answer(make_service(db, datetime.now(TZ)).save(text))
    assert rec.answer == text


def test_reopen_keeps_records(tmp_path):
    path = tmp_path / "t.db"
    db = Database(path)
    make_service(db, datetime.now(TZ)).save("rămâne")
    db.close()
    db2 = Database(path)
    assert [r.answer for r in db2.list_answers()] == ["rămâne"]
    assert db2.schema_version() == migrations.LATEST_VERSION


def test_migration_creates_backup_of_existing_db(tmp_path):
    path = tmp_path / "t.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE legacy (x)")
    conn.execute("PRAGMA user_version = 0")
    conn.commit()
    conn.close()
    Database(path)  # versiunea 0 -> nu e nevoie de backup (nu există schemă aplicată)

    new_ver = max(migrations.MIGRATIONS) + 1
    migrations.MIGRATIONS[new_ver] = "ALTER TABLE exports ADD COLUMN note TEXT;"
    try:
        db = Database(path)
        assert db.schema_version() == new_ver
        assert list((tmp_path / "backups").glob(f"wasjetzt-v{migrations.LATEST_VERSION}-*.db"))
    finally:
        del migrations.MIGRATIONS[new_ver]


def test_migration_v1_to_v2_preserves_rows_with_null_question_fields(tmp_path):
    path = tmp_path / "v1.db"
    conn = sqlite3.connect(str(path))
    # Aplică migrarea v1 manual
    conn.executescript(f"BEGIN;\n{migrations.MIGRATIONS[1]}\nPRAGMA user_version = 1;\nCOMMIT;")
    conn.execute(
        "INSERT INTO answers (answer, created_at_local, created_at_utc, timezone, source) "
        "VALUES ('raspuns vechi', '2026-11-12T10:00:00', '2026-11-12T08:00:00', 'UTC', 'scheduled')"
    )
    conn.commit()
    conn.close()

    db = Database(path, backups_dir=tmp_path / "backups")
    assert db.schema_version() == migrations.LATEST_VERSION
    row = db.get_answer(1)
    assert row is not None
    assert row.answer == "raspunsvechi" or row.answer == "raspuns vechi"
    assert row.question_id is None
    assert row.question_text is None
    assert row.question_language is None


def test_answer_with_question_persists_and_last_question_id(tmp_path):
    db = Database(tmp_path / "q.db")
    svc = make_service(db, datetime.now(TZ))
    assert db.last_question_id() is None

    rid1 = svc.save("Antwort 1", question_id="q01", question_text="Wie geht's?", question_language="de")
    rec1 = db.get_answer(rid1)
    assert rec1.question_id == "q01"
    assert rec1.question_text == "Wie geht's?"
    assert rec1.question_language == "de"
    assert db.last_question_id() == "q01"

    # Salvare răspuns fără question_id (de exemplu din sistem vechi)
    svc.save("Antwort 2")
    # last_question_id ignoră intrările cu NULL
    assert db.last_question_id() == "q01"

    svc.save("Antwort 3", question_id="q07", question_text="Mit wem?", question_language="de")
    assert db.last_question_id() == "q07"
