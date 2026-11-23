# Instrucțiuni pentru agentul Antigravity — construiește executabilul și instalatorul WasJetzt

## Context
Workspace-ul conține proiectul complet **WasJetzt** (Python 3.12 + PySide6): o aplicație desktop Windows care afișează
periodic, în dreapta-jos, întrebarea „Was machst du jetzt?”, salvează răspunsurile în SQLite și le exportă în Markdown
la ieșire. Codul, testele, pictograma, scriptul de build și configurația instalatorului sunt deja scrise.

**Sarcina ta:** construiește executabilul `.exe` și instalatorul pentru Windows, verifică-le și raportează rezultatele reale.
Nu rescrie aplicația și nu adăuga funcționalități noi. Corectează doar ce împiedică build-ul sau testele.

Lucrează pe Windows 10/11 pe 64 de biți, direct în workspace. Nu cere informații utilizatorului: folosește valorile implicite de mai jos.

## Reguli
- Nu inventa rezultate. Rulează fiecare comandă și raportează ieșirea reală (trecut/eșuat, mesaje de eroare).
- Nu șterge și nu modifica codul fără motiv. Dacă o corecție este necesară, fă-o minimală și explic-o la final.
- Nu atinge datele reale ale utilizatorului (`%APPDATA%\WasJetzt`, `%LOCALAPPDATA%\WasJetzt`). Pentru orice rulare de test setează
  `WASJETZT_HOME` către un folder temporar.
- Nu instala nimic în afară de: Python 3.12, Inno Setup 6 (dacă lipsesc) și dependențele din `requirements-dev.txt`.
- Nu pretinde că ai verificat lucruri vizuale (poziția ferestrei, tray, comportament pe mai multe monitoare). Acelea rămân în
  `docs\MANUAL_TESTS.md`, pentru utilizator.

## Pași (execută în ordine; după fiecare pas verifică rezultatul înainte de următorul)

### 1. Inspectează workspace-ul
- Confirmă prezența: `src\wasjetzt\`, `tests\`, `scripts\build.py`, `scripts\package_windows.bat`,
  `installer\windows_installer.iss`, `src\wasjetzt\resources\app.ico`, `requirements.txt`, `requirements-dev.txt`.
- Dacă lipsește ceva, spune exact ce și oprește-te.

### 2. Verifică instrumentele
- `python --version` trebuie să arate 3.12.x pe 64 de biți. Dacă lipsește: `winget install -e --id Python.Python.3.12`, apoi deschide un terminal nou.
- Inno Setup 6: caută `ISCC.exe` în `%ProgramFiles(x86)%\Inno Setup 6\`, `%ProgramFiles%\Inno Setup 6\`, `%LocalAppData%\Programs\Inno Setup 6\`.
  Dacă lipsește: `winget install -e --id JRSoftware.InnoSetup`.

### 3. Mediu virtual și dependențe
```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

### 4. Rulează testele
```bat
python -m pytest -q
```
- Toate testele trebuie să treacă. Dacă unele eșuează, citește eroarea, corectează cauza reală (nu șterge/slăbi testul),
  rulează din nou. Raportează ce ai schimbat.

### 5. Construiește executabilul
```bat
python scripts\build.py
```
- Rezultat așteptat: `dist\WasJetzt\WasJetzt.exe` (împreună cu restul folderului `dist\WasJetzt\`).
- La erori PyInstaller de tip „module not found”, adaugă modulul ca `--hidden-import` în `scripts\build.py` și reia.

### 6. Verificare rapidă a executabilului (smoke test, cu date izolate)
```bat
set WASJETZT_HOME=%TEMP%\wasjetzt_smoke
start "" dist\WasJetzt\WasJetzt.exe
```
- Așteaptă ~10 secunde. Procesul `WasJetzt.exe` trebuie să fie încă rulând (wizard-ul de configurare este deschis).
- Verifică `%TEMP%\wasjetzt_smoke\data\logs\wasjetzt.log` (nu trebuie să conțină excepții).
- Oprește procesul (`taskkill /IM WasJetzt.exe /F`) și șterge `%TEMP%\wasjetzt_smoke`.

### 7. Construiește instalatorul
```bat
"<calea către>\ISCC.exe" installer\windows_installer.iss
```
(sau rulează `scripts\package_windows.bat`, care face pașii 3–7 automat).
- Rezultat așteptat: `installer\Output\WasJetzt_Setup.exe`.

### 8. Verifică instalarea și dezinstalarea (într-un director temporar, cu pornire automată activată)
```bat
installer\Output\WasJetzt_Setup.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /DIR="%TEMP%\WasJetzt_install_test" /TASKS="desktopicon,startup" /LOG="%TEMP%\wasjetzt_install.log"
```
Verifică și notează:
- există `%TEMP%\WasJetzt_install_test\WasJetzt.exe`;
- există shortcut `WasJetzt.lnk` pe Desktop și în meniul Start;
- `reg query HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v WasJetzt` returnează valoarea cu `--background`.

Apoi dezinstalează:
```bat
"%TEMP%\WasJetzt_install_test\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```
Verifică și notează:
- shortcut-urile de pe Desktop și din Start au dispărut;
- `reg query ... /v WasJetzt` nu mai găsește valoarea;
- folderul de instalare a dispărut;
- datele (`%APPDATA%\WasJetzt`, `%LOCALAPPDATA%\WasJetzt`) nu au fost șterse (dacă există).
Dacă aplicația rulează în timpul dezinstalării, închide-o mai întâi.

### 9. Raport final (obligatoriu)
Prezintă utilizatorului, în română:
1. Rezultatul real al testelor (câte au trecut / au eșuat).
2. Calea completă către `WasJetzt.exe` și către `WasJetzt_Setup.exe`.
3. Rezultatul fiecărei verificări din pașii 6 și 8 (da/nu, cu detalii).
4. Orice fișier pe care l-ai modificat și de ce.
5. Limitări rămase: executabilul nu este semnat digital (SmartScreen poate avertiza: „Mai multe informații → Rulează oricum”);
   verificările vizuale din `docs\MANUAL_TESTS.md` (fereastra în dreapta-jos, mai multe monitoare, sleep/hibernate,
   restart cu pornire automată) trebuie făcute de utilizator după instalare.
6. Instrucțiunea finală pentru utilizator: rulează `installer\Output\WasJetzt_Setup.exe`, apoi pornește WasJetzt de pe Desktop;
   la prima pornire se deschide configurarea inițială (director de export, interval, pornire automată).
