"""Texte de interfață. Doar româna în v1; adaugă o limbă nouă ca dicționar nou în _CATALOGS."""
from __future__ import annotations

_RO = {
    "app.name": "WasJetzt",
    "prompt.title": "WasJetzt",
    "prompt.save": "Speichern",
    "prompt.placeholder": "Scrie aici răspunsul…",
    "prompt.empty": "Scrie ceva înainte de a salva.",
    "prompt.saved": "Răspuns salvat.",
    "prompt.save_error": "Răspunsul nu a putut fi salvat: {error}",
    "tray.open": "Deschide aplicația",
    "tray.settings": "Setări",
    "tray.language": "Limba întrebărilor",
    "tray.prompt_now": "Afișează întrebarea acum",
    "tray.export_now": "Exportă acum",
    "tray.open_export_dir": "Deschide directorul de export",
    "tray.quit": "Ieșire",
    "tray.running_background": "WasJetzt rulează în fundal.",
    "tray.unavailable": "Zona de notificări nu este disponibilă; fereastra principală rămâne deschisă.",
    "main.title": "WasJetzt",
    "main.status": "Stare",
    "main.status_running": "Rulează",
    "main.status_paused": "În pauză",
    "main.next": "Următoarea întrebare",
    "main.next_none": "—",
    "main.total": "Total răspunsuri",
    "main.pending_export": "Neexportate",
    "main.latest": "Ultimele răspunsuri",
    "main.pause": "Pauză",
    "main.resume": "Reia",
    "main.settings": "Setări",
    "main.export": "Exportă acum",
    "main.prompt_now": "Întreabă acum",
    "main.quit": "Ieșire",
    "settings.title": "Setări WasJetzt",
    "settings.tab_general": "General",
    "settings.tab_prompts": "Întrebări",
    "settings.tab_interface": "Interfață",
    "settings.export_dir": "Directorul de export",
    "settings.choose_dir": "Alege directorul…",
    "settings.interval": "Interval între întrebări",
    "settings.minutes_suffix": " min",
    "settings.autostart": "Pornește odată cu sistemul",
    "settings.start_minimized": "Pornire în fundal (fără fereastră mare)",
    "settings.notifications": "Arată notificări de confirmare",
    "settings.on_dismiss": "Dacă închizi întrebarea fără răspuns",
    "settings.on_dismiss_wait": "Așteaptă următorul interval",
    "settings.on_dismiss_retry": "Întreabă din nou după un interval scurt",
    "settings.retry_minutes": "Interval scurt de reîncercare",
    "settings.question_language": "Limba întrebărilor",
    "settings.language": "Limba interfeței",
    "settings.language_note": "Interfața de setări este în română. Limba întrebărilor se alege în tabul „Întrebări”.",
    "settings.save": "Salvează",
    "settings.cancel": "Anulare",
    "settings.dir_required": "Alege un director de export.",
    "settings.dir_create_q": "Directorul nu există:\n{path}\n\nVrei să fie creat?",
    "settings.dir_error": "Directorul nu poate fi folosit: {error}",
    "settings.invalid": "Setări invalide: {error}",
    "settings.save_failed": "Setările nu au putut fi salvate: {error}",
    "settings.saved": "Setările au fost salvate.",
    "settings.startup_failed": "Pornirea automată nu a putut fi modificată: {error}",
    "dir.not_set": "Directorul de export nu este setat.",
    "dir.missing": "Directorul nu există.",
    "dir.not_a_dir": "Calea nu este un director.",
    "dir.not_writable": "Nu se poate scrie în director ({error}).",
    "err.interval_range": "Intervalul trebuie să fie între {lo} și {hi} minute.",
    "err.retry_range": "Intervalul de reîncercare trebuie să fie între {lo} și {hi} minute.",
    "err.on_dismiss": "Valoare necunoscută pentru comportamentul la închidere.",
    "err.language": "Limbă neacceptată.",
    "err.question_language": "Limbă neacceptată pentru întrebări.",
    "err.bool": "Valoarea trebuie să fie da/nu.",
    "err.type": "Valoare de tip greșit.",
    "wizard.title": "Configurare WasJetzt",
    "wizard.next": "Înainte",
    "wizard.back": "Înapoi",
    "wizard.finish": "Finalizează",
    "wizard.cancel": "Anulare",
    "wizard.welcome_title": "Bine ai venit la WasJetzt",
    "wizard.welcome_text": (
        "WasJetzt rulează discret în fundal și te întreabă periodic, într-o fereastră mică "
        "din colțul din dreapta-jos, câte o întrebare despre ziua ta, în germană sau spaniolă.\n\n"
        "Răspunsurile tale sunt salvate local, pe acest calculator, cu ora exactă. "
        "Nu se trimite nimic prin rețea."
    ),
    "wizard.language_title": "În ce limbă vrei întrebările?",
    "wizard.language_text": "Poți alege germana sau spaniola. Schimbi oricând din Setări sau din meniul din zona de notificări.",
    "wizard.folder_title": "Unde se salvează răspunsurile?",
    "wizard.folder_text": (
        "La ieșirea din aplicație, răspunsurile noi sunt exportate într-un fișier Markdown "
        "în directorul ales mai jos."
    ),
    "wizard.interval_label": "Cât de des să te întrebe:",
    "wizard.finish_title": "Aproape gata",
    "wizard.finish_text": (
        "Vrei ca WasJetzt să pornească automat când pornești calculatorul? "
        "Poți schimba oricând aceste opțiuni din Setări."
    ),
    "wizard.autostart": "Pornește WasJetzt odată cu sistemul",
    "export.ok": "Am exportat {count} răspunsuri în {path}.",
    "export.nothing": "Nu există răspunsuri noi de exportat.",
    "export.failed": "Exportul a eșuat: {error}\n\nRăspunsurile sunt păstrate în siguranță în baza de date.",
    "export.retry": "Reîncearcă",
    "export.choose_other": "Alege alt director…",
    "export.quit_anyway": "Ieși fără export",
    "export.exiting": "Se exportă răspunsurile…",
    "export.startup_recovered": "Am exportat răspunsurile rămase de la ultima rulare ({count}).",
    "db.error": "Eroare la baza de date: {error}",
    "startup.unsupported": "Pornirea automată nu este disponibilă pe acest sistem de operare.",
}

_CATALOGS = {"ro": _RO}
_current = "ro"

_PROMPT_TEXTS = {
    "de": {
        "save": "Speichern",
        "placeholder": "Schreib deine Antwort hier…",
        "empty": "Bitte schreib zuerst etwas.",
    },
    "es": {
        "save": "Guardar",
        "placeholder": "Escribe tu respuesta aquí…",
        "empty": "Escribe algo antes de guardar.",
    },
}


def set_language(code: str) -> None:
    global _current
    _current = code if code in _CATALOGS else "ro"


def tr(key: str, **kwargs) -> str:
    text = _CATALOGS[_current].get(key) or _RO.get(key, key)
    return text.format(**kwargs) if kwargs else text


def prompt_tr(language: str | None, key: str) -> str:
    lang_dict = _PROMPT_TEXTS.get(language or "de") or _PROMPT_TEXTS["de"]
    return lang_dict.get(key) or _PROMPT_TEXTS["de"].get(key, key)
