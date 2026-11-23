@echo off
setlocal enableextensions
REM Construiește tot: venv -> dependențe -> teste -> .exe -> instalator.
REM Rulează din orice loc: scriptul se mută în rădăcina proiectului.
cd /d "%~dp0\.."

where python >nul 2>nul
if errorlevel 1 (
  echo [EROARE] Python nu este in PATH. Instaleaza Python 3.12 ^(64-bit^) cu "Add python.exe to PATH".
  exit /b 1
)

if not exist .venv (
  echo [1/5] Creez mediul virtual...
  python -m venv .venv || exit /b 1
)
call .venv\Scripts\activate.bat || exit /b 1

echo [2/5] Instalez dependentele...
python -m pip install --upgrade pip || exit /b 1
pip install -r requirements-dev.txt || exit /b 1

echo [3/5] Rulez testele...
python -m pytest -q || (echo [EROARE] Testele au esuat. Build oprit. & exit /b 1)

echo [4/5] Construiesc executabilul cu PyInstaller...
python scripts\build.py || exit /b 1

echo [5/5] Construiesc instalatorul cu Inno Setup...
set "ISCC="
for %%P in ("%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" "%ProgramFiles%\Inno Setup 6\ISCC.exe" "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe") do (
  if exist %%P set "ISCC=%%~P"
)
if not defined ISCC (
  echo [EROARE] Inno Setup 6 nu a fost gasit. Instaleaza-l: winget install JRSoftware.InnoSetup
  echo Executabilul este totusi gata in dist\WasJetzt\WasJetzt.exe
  exit /b 1
)
"%ISCC%" installer\windows_installer.iss || exit /b 1

echo.
echo GATA. Instalator: %CD%\installer\Output\WasJetzt_Setup.exe
endlocal
