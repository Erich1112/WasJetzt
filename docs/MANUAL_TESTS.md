# Teste manuale (comportament nativ Windows / UI)

Testele unitare nu pot verifica ferestre, tray, registru real și instalatorul. Rulează lista asta pe un Windows 10/11
curat sau într-o mașină virtuală, după `scripts\package_windows.bat`. Bifează și notează rezultatul real.

## Instalare
- [ ] `WasJetzt_Setup.exe` rulează fără cerere de administrator.
- [ ] Apare pictograma WasJetzt pe Desktop (task bifat) și intrarea în meniul Start.
- [ ] Bifa „Pornește automat” creează valoarea `WasJetzt` în `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.

## Prima pornire
- [ ] Dublu-click pe pictograma din Desktop deschide wizard-ul (bun venit → limba întrebărilor → director + interval → pornire automată).
- [ ] Wizard-ul oferă alegerea limbii întrebărilor (Deutsch / Español).
- [ ] Închiderea wizard-ului cu „Anulare” închide aplicația; la următoarea pornire wizard-ul apare din nou.
- [ ] Un director inexistent cere confirmare și se creează; un director fără drept de scriere este respins.
- [ ] După „Finalizează”: aplicația trece în fundal (pictogramă în tray + notificare), fără fereastră mare.

## Fereastra cu întrebarea
- [ ] Meniu tray → „Afișează întrebarea acum”: fereastra apare în dreapta-jos, ~20 px de marginile zonei de lucru
      (deasupra barei de activități).
- [ ] Întrebări diferite la apariții succesive: deschide „Afișează întrebarea acum” de ~15 ori (toate cele 10 apar fără duplicate într-un ciclu complet, iar trecerea la următorul ciclu nu repetă întrebarea anterioară).
- [ ] O întrebare lungă (q03 / q05, în ambele limbi) se încadrează, textul se rupe pe rânduri (word wrap) și fereastra rămâne în colțul din dreapta-jos.
- [ ] Schimbarea limbii din tray („Limba întrebărilor” → Deutsch / Español) și din Setări se aplică la următoarea apariție a ferestrei (text întrebare, buton Speichern/Guardar, placeholder).
- [ ] Monitor secundar: mută fereastra principală pe alt monitor, schimbă monitorul principal / scalarea DPI —
      fereastra rămâne în colțul monitorului principal.
- [ ] Răspuns gol / doar spații: mesaj de validare în limba selectată („Bitte schreib zuerst etwas.” / „Escribe algo antes de guardar.”), nu se salvează nimic.
- [ ] Enter salvează, Shift+Enter adaugă o linie, butonul salvează; apare confirmarea discretă.
- [ ] Închiderea cu X sau Esc fără răspuns: nicio înregistrare; următoarea apariție după intervalul configurat.
- [ ] Două apeluri succesive („Afișează întrebarea acum” de 2 ori): o singură fereastră.
- [ ] Interval 5 minute în Setări: fereastra apare după ~5 minute.

## Repaus, restart, erori
- [ ] Sleep/hibernate mai mult decât intervalul, apoi trezire: cel mult o fereastră, nu o rafală.
- [ ] Restart Windows cu pornire automată activă: aplicația pornește în fundal (tray), fără fereastră mare.
- [ ] Ieșire din tray: se creează `raspunsuri_AAAA-LL-ZZ_HHMMSS.md` (UTF-8, conține întrebarea pentru fiecare răspuns: `**Întrebare:** ...`); reieșire fără răspunsuri noi nu creează fișier.
- [ ] Director de export indisponibil (șterge-l / folosește un USB scos): la ieșire apare dialogul cu
      Reîncearcă / Alege alt director / Ieși fără export; răspunsurile nu se pierd.
- [ ] Închide forțat procesul din Task Manager după un răspuns, repornește: răspunsul există și este exportat la pornire.
- [ ] Deconectare/oprire Windows cu răspunsuri neexportate: la următoarea pornire sunt exportate.

## Setări
- [ ] Schimbarea directorului, intervalului, limbii întrebărilor, comutatoarelor se păstrează după repornire.
- [ ] Comutatorul „Pornește odată cu sistemul” reflectă starea reală din registru (verifică cu regedit).
- [ ] A doua pornire a aplicației (dublu-click din nou pe Desktop) nu creează o a doua instanță, ci arată fereastra principală.

## Dezinstalare
- [ ] Dezinstalarea elimină shortcut-urile și valoarea `WasJetzt` din `Run`.
- [ ] `%LOCALAPPDATA%\WasJetzt` (baza de date), `%APPDATA%\WasJetzt` (setări) și exporturile rămân.
- [ ] Dezinstalarea cât timp aplicația rulează cere închiderea ei.
