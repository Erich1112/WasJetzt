# Instrucțiuni pentru Antigravity — meniu de limbă (germană/spaniolă) și 10 întrebări aleatorii

## Context
Proiectul **WasJetzt** există deja în workspace (Python 3.12 + PySide6, structura este descrisă în `README.md`).
Până acum fereastra din colțul din dreapta-jos punea mereu „Was machst du jetzt?”. Schimbarea cerută:

1. Utilizatorul alege **limba** dintr-un meniu: acum doar **Deutsch** și **Español**.
2. De fiecare dată când se deschide fereastra, apare **una din 10 întrebări**, aleasă aleatoriu, în limba aleasă.
3. Fiecare răspuns salvează și **întrebarea la care a răspuns**.

## Decizii deja luate (nu le pune în discuție)
- „Limba” din meniu = limba **ferestrei cu întrebarea**: textul întrebării, butonul, placeholder-ul și mesajul „răspuns gol”.
  Interfața de setări, tray-ul și wizard-ul rămân în română. Mesajele tehnice de eroare rămân în română.
- Limbi acceptate: `de` (implicit) și `es`. O limbă nouă ulterior = o intrare nouă în dicționare, fără schimbări de logică.
- Cele 10 întrebări **înlocuiesc** întrebarea unică. Numele aplicației rămâne WasJetzt.
- Alegerea aleatorie este de tip „shuffle bag”: nicio întrebare nu se repetă până nu au apărut toate 10. Prima întrebare dintr-o
  nouă serie nu este niciodată aceeași cu ultima pusă, nici după repornirea aplicației.
- Schimbarea limbii se aplică de la **următoarea** fereastră; o fereastră deja deschisă nu se modifică.
- Nu adăuga dependențe noi.

## Reguli de lucru
- Nu inventa rezultate: rulează comenzile și raportează ieșirea reală.
- Fă modificări minimale, în stilul codului existent. Nu rescrie ce nu e menționat aici.
- Nu șterge teste. Actualizează doar testele pe care noul comportament le invalidează (sunt enumerate la pasul 10).
- Pentru orice rulare de test a aplicației setează `WASJETZT_HOME` către un folder temporar (nu atinge datele reale).

## Pași (în ordine; după fiecare pas rulează `python -m pytest -q`)

### 1. Inspectează
Citește: `src/wasjetzt/__init__.py`, `i18n.py`, `config/settings.py`, `database/db.py`, `database/migrations.py`,
`services/answer_service.py`, `services/export_service.py`, `ui/prompt_window.py`, `ui/settings_window.py`,
`ui/first_run_wizard.py`, `ui/tray.py`, `app.py`, `tests/`.

### 2. Banca de întrebări — fișier nou `src/wasjetzt/questions.py`
Conținut (textele exact așa):

```python
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
```

Textele din fereastra cu întrebarea, pe limbă (adaugă în `i18n.py` o funcție `prompt_tr(language, key)` care le citește și
cade pe `de` dacă limba sau cheia lipsesc):

| cheie | de | es |
|---|---|---|
| `save` | Speichern | Guardar |
| `placeholder` | Schreib deine Antwort hier… | Escribe tu respuesta aquí… |
| `empty` | Bitte schreib zuerst etwas. | Escribe algo antes de guardar. |

### 3. Setări — `config/settings.py`
- Câmp nou în `Settings`: `question_language: str = "de"` (nu modifica `language`, care rămâne limba interfeței = `ro`).
- În `validate()`: valoarea trebuie să fie în `questions.LANGUAGES`, altfel eroare pe câmpul `question_language`
  (mesaj nou în `i18n.py`: „Limbă neacceptată pentru întrebări.”).
- Nu schimba `SCHEMA_VERSION`: un `settings.json` vechi, fără câmpul nou, trebuie să se încarce cu `de`.

### 4. Baza de date — migrarea v2
- `database/migrations.py`: adaugă `MIGRATIONS[2]`:
  ```sql
  ALTER TABLE answers ADD COLUMN question_id TEXT;
  ALTER TABLE answers ADD COLUMN question_text TEXT;
  ALTER TABLE answers ADD COLUMN question_language TEXT;
  ```
  (copia de siguranță din `backups/` se face deja automat înainte de migrare; răspunsurile vechi rămân neatinse,
  cu coloanele noi `NULL` = întrebarea veche „Was machst du jetzt?”).
- `database/db.py`: adaugă la **sfârșitul** lui `AnswerRecord` câmpurile `question_id`, `question_text`, `question_language`
  (toate cu valoare implicită `None`, ca construcțiile pozitive existente să rămână valide), actualizează `_COLUMNS`,
  `add_answer(...)` (parametri noi opționali) și adaugă `last_question_id() -> str | None`
  (`SELECT question_id FROM answers WHERE question_id IS NOT NULL ORDER BY id DESC LIMIT 1`).

### 5. `services/answer_service.py`
`AnswerService.save(...)` primește și `question_id`, `question_text`, `question_language` (opționale) și le trimite la `add_answer`.
Validarea răspunsului gol și logica timestamp-ului rămân neschimbate.

### 6. `ui/prompt_window.py`
- Constanta `QUESTION` nu mai este afișată. Elimină importul ei de aici; păstreaz-o în `__init__.py` redenumită/aliasată ca
  `LEGACY_QUESTION` (folosită doar pentru înregistrările vechi, fără `question_text`).
- `show_prompt(question_text: str, language: str)`: setează textul întrebării, `accessibleName`, textul butonului, placeholder-ul
  și mesajul „gol” din `prompt_tr(language, ...)`.
- Întrebările sunt lungi (până la ~95 de caractere): `self.question.setWordWrap(True)`, fontul `+2` (nu `+3`), lățime minimă 380 px.
  După ce setezi textul, calculează înălțimea din `sizeHint()` și redimensionează înainte de `reposition()`, ca fereastra să rămână
  ancorată în colțul din dreapta-jos și complet în zona de lucru (comportamentul existent de poziționare nu se schimbă).

### 7. `app.py` (AppController)
- Creează `self.picker = QuestionPicker(last_id=self.db.last_question_id())`.
- În `_present_prompt()`: `self._current_question = self.picker.next()`, `lang = normalize_language(self.settings.question_language)`,
  apoi `self.prompt.show_prompt(text_for(q, lang), lang)`. Păstrează `question` și `lang` pentru salvare. Se aplică și întrebărilor
  manuale („Afișează întrebarea acum”).
- În `_on_submitted()`: trimite la `answers.save(...)` valorile `question_id`, `question_text` (textul **exact afișat**) și
  `question_language`.
- Metodă nouă `set_question_language(code)`: validează, `replace(self.settings, question_language=code)`, `self.manager.save(...)`,
  actualizează bifa din tray și valoarea din fereastra de setări. Nu reaplică pornirea automată.
- În `_apply_settings()` păstrează comportamentul existent; `question_language` vine din noul control din fereastra de setări.

### 8. Meniuri de alegere a limbii
- **Setări** (`ui/settings_window.py`): în tabul „Întrebări” adaugă un `QComboBox` „Limba întrebărilor” cu `Deutsch` / `Español`
  (valorile `de` / `es`), încărcat în `load_from()` și citit în `_save()`. În tabul „Interfață” lasă limba interfeței (Română) și
  actualizează nota: „Interfața de setări este în română. Limba întrebărilor se alege în tabul „Întrebări”.”
- **Tray** (`ui/tray.py`): submeniu „Limba întrebărilor” cu două acțiuni bifabile, exclusive (`QActionGroup`): Deutsch, Español.
  Semnal nou `language_selected(str)`, conectat la `AppController.set_question_language`. Metodă `set_language_checked(code)`.
- **Wizard** (`ui/first_run_wizard.py`): pagină nouă între „bun venit” și „director”, cu alegerea limbii (două butoane radio),
  implicit Deutsch; `result_settings()` include `question_language`.
- Texte noi/actualizate în `i18n.py`:
  - `settings.question_language` = „Limba întrebărilor”
  - `tray.language` = „Limba întrebărilor”
  - `wizard.language_title` = „În ce limbă vrei întrebările?”
  - `wizard.language_text` = „Poți alege germana sau spaniola. Schimbi oricând din Setări sau din meniul din zona de notificări.”
  - `wizard.welcome_text` actualizat: aplicația te întreabă periodic, într-o fereastră mică din dreapta-jos, câte o întrebare
    despre ziua ta, în germană sau spaniolă (fără a mai cita „Was machst du jetzt?”).
  - `settings.language_note` actualizat conform pasului de mai sus.

### 9. Export
Include întrebarea la fiecare răspuns, **în formatul de export curent** (vezi și `INSTRUCTIUNI_ANTIGRAVITY_FORMAT_EXPORT.md`
dacă a fost aplicat):
- Markdown (dacă exportul este încă `.md`): sub fiecare titlu de oră adaugă linia `**Întrebare:** <question_text>`
  (citată/escape-uită ca să nu strice structura) înainte de răspuns. Titlul fișierului devine `# Răspunsuri – WasJetzt`.
- CSV/TXT (dacă formatul a fost deja schimbat): coloana/linia „Întrebare” și „Limba”.
- Pentru înregistrări fără `question_text` (cele vechi), folosește `LEGACY_QUESTION` și limba `de`.

### 10. Teste
**Actualizează** (ar eșua după schimbare):
- `tests/test_database.py::test_reopen_keeps_records`: `schema_version()` nu mai e `1`; compară cu `migrations.LATEST_VERSION`.
- `tests/test_database.py::test_migration_creates_backup_of_existing_db`: folosește acum versiunea `max(MIGRATIONS) + 1`
  (nu `2`), ca să nu suprascrie și apoi să șteargă migrarea reală; verifică backup-ul `wasjetzt-v{versiunea_anterioară}-*.db`.
- `tests/test_export.py`: asertările care conțin „Was machst du jetzt?” în antetul exportului (titlul nou, conform pasului 9).

**Adaugă:**
- `tests/test_questions.py`: exact 10 întrebări cu id-uri unice și text nevid în `de` și `es`; 10 extrageri consecutive = toate cele
  10, fără duplicate; pe 200 de extrageri, niciodată două identice consecutiv (inclusiv la granița dintre serii și când
  `last_id` este dat la pornire); `normalize_language("fr") == "de"`; `text_for(...)` pentru `de` și `es`.
- `tests/test_settings.py`: implicit `question_language == "de"`; `"fr"` este respins/revine individual la `de`; un `settings.json`
  vechi fără câmp se încarcă cu `de`; `es` se salvează și se reîncarcă.
- `tests/test_database.py`: migrarea v1 → v2 păstrează rândurile existente (cu `question_*` = `NULL`); un răspuns salvat cu
  întrebare își păstrează `question_id`/`question_text`/`question_language`; `last_question_id()` returnează ultimul id folosit.
- `tests/test_export.py`: exportul conține întrebarea afișată și, pentru un răspuns vechi (fără întrebare), `Was machst du jetzt?`.

### 11. Documentație
- `README.md`: elimină afirmația „întrebarea rămâne mereu în germană”; descrie limba întrebărilor (Deutsch/Español), cele 10
  întrebări aleatorii și cum adaugi o întrebare sau o limbă (un element nou în `QUESTIONS`, respectiv o cheie nouă în
  `LANGUAGES` și în dicționarul din `prompt_tr`).
- `docs/MANUAL_TESTS.md`: adaugă bife pentru: întrebări diferite la apariții succesive (deschide „Afișează întrebarea acum”
  de ~15 ori); o întrebare lungă (q03 / q05, în ambele limbi) se încadrează, textul se rupe pe rânduri și fereastra rămâne în
  colțul din dreapta-jos; schimbarea limbii din tray și din Setări se vede la următoarea fereastră; wizard-ul oferă alegerea limbii.

### 12. Reconstruiește și verifică
Rulează testele, apoi repetă pașii 5–8 din `INSTRUCTIUNI_ANTIGRAVITY.md` (executabil, smoke test, instalator, instalare și
dezinstalare de test). La o actualizare peste o instalare existentă, migrarea v2 creează automat o copie în
`%LOCALAPPDATA%\WasJetzt\backups\`.

### 13. Raport final (în română)
1. Rezultatul real al testelor (câte au trecut / au eșuat) și fișierele modificate/create.
2. Căile către `WasJetzt.exe` și `WasJetzt_Setup.exe` rebuild-uite.
3. Ce nu ai putut verifica vizual (fereastra cu întrebări lungi, tray, wizard) — rămâne în `docs/MANUAL_TESTS.md`.
