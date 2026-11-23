import random
from wasjetzt.questions import (
    DEFAULT_LANGUAGE,
    LANGUAGES,
    QUESTIONS,
    QuestionPicker,
    normalize_language,
    text_for,
)


def test_ten_questions_unique_ids_and_non_empty_texts():
    assert len(QUESTIONS) == 10
    ids = [q.id for q in QUESTIONS]
    assert len(set(ids)) == 10
    for q in QUESTIONS:
        assert "de" in q.text and q.text["de"].strip()
        assert "es" in q.text and q.text["es"].strip()


def test_ten_consecutive_picks_contain_all_without_duplicates():
    picker = QuestionPicker()
    picked = [picker.next().id for _ in range(10)]
    assert len(set(picked)) == 10
    assert set(picked) == {q.id for q in QUESTIONS}


def test_no_consecutive_duplicates_across_two_hundred_picks():
    # Testează și cu last_id la pornire
    for initial_last in (None, "q01", "q05", "q10"):
        picker = QuestionPicker(rng=random.Random(42), last_id=initial_last)
        last_id = initial_last
        for _ in range(200):
            q = picker.next()
            assert q.id != last_id
            last_id = q.id


def test_normalize_language():
    assert normalize_language("de") == "de"
    assert normalize_language("es") == "es"
    assert normalize_language("fr") == "de"
    assert normalize_language(None) == "de"
    assert normalize_language("") == "de"


def test_text_for_languages():
    q = QUESTIONS[0]
    assert text_for(q, "de") == q.text["de"]
    assert text_for(q, "es") == q.text["es"]
    assert text_for(q, "unknown") == q.text["de"]

