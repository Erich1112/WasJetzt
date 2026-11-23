# WasJetzt

Aplicație desktop discretă care rulează în fundal și, la un interval configurabil (implicit 60 de minute),
afișează în colțul din dreapta-jos al ecranului o fereastră mică cu o întrebare despre ziua ta,
aleasă aleatoriu din 10 întrebări, în germană sau spaniolă.
Fiecare răspuns este salvat local (SQLite) cu data și ora exactă, împreună cu întrebarea la care s-a răspuns,
iar la ieșire răspunsurile noi sunt exportate într-un fișier Markdown, într-un director ales de tine. Nimic nu se trimite prin rețea.

**Țintă v1:** Windows 10/11 pe 64 de biți · interfață în română · limba întrebărilor configurabilă (Deutsch / Español).

## Limba întrebărilor și banca de întrebări
- Aplicația oferă o bancă de 10 întrebări despre ziua ta, selectate printr-un mecanism de tip „shuffle bag”: nicio întrebare nu se repetă până când nu au fost afișate toate cele 10, iar prima întrebare dintr-o serie nouă nu este niciodată identică cu ultima afișată (inclusiv la repornirea aplicației).
- **Limbi acceptate:** Deutsch (`de`, implicit) și Español (`es`).
- Limba întrebărilor poate fi aleasă în asistentul de configurare inițială (wizard), din Setări (tabul „Întrebări”) sau direct din submeniul „Limba întrebărilor” din tray. Schimbarea se aplică de la următoarea fereastră.
- **Cum adaugi o întrebare nouă:** adaugă un nou element `Question("q...", {"de": "...", "es": "..."})` în tuplul `QUESTIONS` din `src/wasjetzt/questions.py`.
- **Cum adaugi o limbă nouă:** adaugă codul și denumirea în dicționarul `LANGUAGES` din `src/wasjetzt/questions.py`, completează textul în `QUESTIONS` pentru fiecare întrebare și adaugă traducerile controalelor (`save`, `placeholder`, `empty`) în `_PROMPT_TEXTS` din `src/wasjetzt/i18n.py`.

## Cerințe
- Python 3.12 (64-bit), cu „Add python.exe to PATH”
- Pentru instalator: [Inno Setup 6](https://jrsoftware.org/isinfo.php) (`winget install JRSoftware.InnoSetup`)

## Mediu de dezvoltare și rulare din surse
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
python run_wasjetzt.py
```
La prima rulare se deschide wizard-ul de configurare. Argument opțional: `--background` (pornire în fundal, fără fereastră principală).

## Rularea testelor
```bat
python -m pytest -q
```
Testele automate acoperă logica (setări, întrebări și shuffle bag, bază de date și migrarea v2, export, programare, startup cu registru simulat, poziționare).
Comportamentul vizual nativ Windows se verifică manual: vezi `docs/MANUAL_TESTS.md`.

## Construirea executabilului
```bat
python scripts\build.py
```
Rezultat: `dist\WasJetzt\WasJetzt.exe` (are nevoie de tot folderul `dist\WasJetzt`).

## Construirea instalatorului
Tot procesul (venv, dependențe, teste, .exe, instalator), dintr-un singur pas:
```bat
scripts\package_windows.bat
```
Rezultat: `installer\Output\WasJetzt_Setup.exe` — instalare per utilizator (fără administrator), pictogramă pe Desktop,
intrare în meniul Start, opțiune de pornire automată, dezinstalare curată.
Manual: `python scripts\build.py`, apoi deschide `installer\windows_installer.iss` în Inno Setup și apasă Compile.

> Executabilul nu este semnat digital: Windows SmartScreen poate afișa „aplicație necunoscută”
> (Mai multe informații → Rulează oricum). Unele antivirusuri dau fals pozitiv pe executabile PyInstaller.

## Unde sunt datele
| Ce | Unde (Windows) |
|---|---|
| Setări (JSON) | `%APPDATA%\WasJetzt\settings.json` |
| Baza de date SQLite | `%LOCALAPPDATA%\WasJetzt\wasjetzt.db` |
| Copii de siguranță la migrări | `%LOCALAPPDATA%\WasJetzt\backups\` |
| Loguri tehnice (fără textul răspunsurilor) | `%LOCALAPPDATA%\WasJetzt\logs\` |
| Exporturi `.md` | directorul ales în setări |

Variabila `WASJETZT_HOME` mută datele și setările într-un alt folder (util pentru teste).

## Backup și recuperare
- **Backup:** copiază `wasjetzt.db` (și `settings.json`) când aplicația este închisă.
- **Recuperare:** închide aplicația, pune `wasjetzt.db` înapoi în `%LOCALAPPDATA%\WasJetzt\`, pornește aplicația.
- Răspunsurile se scriu în SQLite imediat la salvare („Speichern” / „Guardar”); chiar la o pană de curent nu se pierd. Răspunsurile neexportate
  sunt exportate la următoarea pornire.

## Comportament important
- Dacă închizi fereastra cu întrebarea fără să răspunzi, nu se creează nicio înregistrare; următoarea întrebare vine
  după intervalul configurat (sau, opțional, după un interval scurt, de maximum 3 ori consecutiv).
- După repaus/hibernare nu apare o rafală de ferestre: întrebarea se reprogramează la un interval întreg.
- Pornirea de pe Desktop/Start arată fereastra principală; pornirea automată (`--background`) rămâne în fundal
  (dacă „Pornire în fundal” este activată). A doua pornire a aplicației doar trezește prima instanță.
- Enter trimite răspunsul, Shift+Enter adaugă o linie nouă. Enter apăsat în prima 0,8 secunde după apariție este ignorat,
  ca să nu trimiți din greșeală ce tastai în altă aplicație.
- În exportul Markdown, fiecare răspuns menționează întrebarea pusă (`**Întrebare:** ...`), iar răspunsurile utilizatorului sunt citate (`> ...`), astfel încât conținutul nu poate altera structura documentului.
- Dacă zona de notificări nu este disponibilă, fereastra principală rămâne accesibilă (se minimizează, nu se ascunde).

## Dezinstalare fără ștergerea datelor
Setări → Aplicații → WasJetzt → Dezinstalează (sau din meniul Start). Se elimină programul, shortcut-urile și intrarea de
startup. **Baza de date, setările și exporturile rămân** pe disc; le poți șterge manual din locațiile de mai sus.

## Structura proiectului
```
src/wasjetzt/
  main.py, app.py, single_instance.py, paths.py, i18n.py, timeutil.py, questions.py
  config/settings.py              setări JSON (validare, migrații, scriere atomică)
  database/db.py, migrations.py   SQLite + migrații versionate
  services/                       scheduler (logică pură), answer_service, export_service, startup_service
  os_integration/                 windows_startup.py (HKCU Run), windows_mutex.py
  ui/                             prompt_window, settings_window, main_window, first_run_wizard, tray, geometry
tests/  installer/  scripts/  docs/
```

## Cum adaugi o setare nouă
1. Câmp nou în `Settings` (`config/settings.py`) + regulă în `validate()`.
2. Control nou în `ui/settings_window.py` (adaugă un tab dacă e nevoie) și mapare în `load_from()` / `_save()`.
3. Texte noi în `i18n.py`. 4. Test în `tests/test_settings.py`.
Setările necunoscute din fișier sunt păstrate la salvare.
