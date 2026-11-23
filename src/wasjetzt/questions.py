"""Banca de întrebări (DE/ES) și alegerea aleatorie fără repetări."""
from __future__ import annotations

import random
from dataclasses import dataclass

LANGUAGES = {"de": "Deutsch", "es": "Español"}  # nume native, afișate în meniuri
DEFAULT_LANGUAGE = "de"


@dataclass(frozen=True)
class Question:
    id: str
    text: dict  # {"de": "...", "es": "..."}


QUESTIONS = (
    Question("q01", {"de": "Wie fühlst du dich heute genau und warum?",
                     "es": "¿Cómo te sientes hoy exactamente y por qué?"}),
    Question("q02", {"de": "Was ist heute deine wichtigste Aufgabe oder dein Hauptziel?",
                     "es": "¿Cuál es tu tarea más importante o tu objetivo principal hoy?"}),
    Question("q03", {"de": "Was ist dir heute auf der Straße, bei der Arbeit oder zu Hause besonders aufgefallen?",
                     "es": "¿Qué te ha llamado especialmente la atención hoy en la calle, en el trabajo o en casa?"}),
    Question("q04", {"de": "Was hast du heute gegessen (oder möchtest du essen) und wie hat es geschmeckt?",
                     "es": "¿Qué has comido hoy (o qué te gustaría comer) y qué tal sabía?"}),
    Question("q05", {"de": "Gab es heute ein kleines Problem oder eine Schwierigkeit? Wie hast du darauf reagiert?",
                     "es": "¿Hubo algún pequeño problema o dificultad hoy? ¿Cómo reaccionaste?"}),
    Question("q06", {"de": "Worüber hast du dich heute gefreut oder wofür bist du dankbar?",
                     "es": "¿De qué te has alegrado hoy o por qué estás agradecido?"}),
    Question("q07", {"de": "Mit wem hast du heute gesprochen und worum ging es in dem Gespräch?",
                     "es": "¿Con quién has hablado hoy y de qué trató la conversación?"}),
    Question("q08", {"de": "Wie ist das Wetter heute und wie beeinflusst es deine Laune?",
                     "es": "¿Qué tiempo hace hoy y cómo influye en tu estado de ánimo?"}),
    Question("q09", {"de": "Was machst du heute, um dich zu entspannen oder Spaß zu haben?",
                     "es": "¿Qué vas a hacer hoy para relajarte o divertirte?"}),
    Question("q10", {"de": "Was möchtest du morgen anders oder besser machen als heute?",
                     "es": "¿Qué te gustaría hacer mañana de forma diferente o mejor que hoy?"}),
)


def normalize_language(code: str | None) -> str:
    return code if code in LANGUAGES else DEFAULT_LANGUAGE


def text_for(question: Question, language: str) -> str:
    return question.text.get(language) or question.text[DEFAULT_LANGUAGE]


class QuestionPicker:
    """Shuffle bag: toate cele 10 apar o dată înainte să se repete vreuna."""

    def __init__(self, rng: random.Random | None = None, last_id: str | None = None):
        self._rng = rng or random.Random()
        self._last_id = last_id
        self._bag: list[Question] = []

    def next(self) -> Question:
        if not self._bag:
            self._bag = list(QUESTIONS)
            self._rng.shuffle(self._bag)
            if len(self._bag) > 1 and self._bag[-1].id == self._last_id:
                self._bag[0], self._bag[-1] = self._bag[-1], self._bag[0]  # pop() ia ultimul element
        question = self._bag.pop()
        self._last_id = question.id
        return question

