"""Controller-ul aplicației: leagă setările, baza de date, programarea, exportul și interfața."""
from __future__ import annotations

import logging
import threading
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from wasjetzt import paths
from wasjetzt.config.settings import Settings, SettingsError, SettingsManager
from wasjetzt.database.db import Database
from wasjetzt.i18n import prompt_tr, set_language, tr
from wasjetzt.questions import Question, QuestionPicker, normalize_language, text_for
from wasjetzt.services.answer_service import AnswerService, EmptyAnswerError
from wasjetzt.services.export_service import ExportResult, ExportService
from wasjetzt.services.scheduler import TICK_SECONDS, SchedulerCore
from wasjetzt.services.startup_service import StartupError, get_startup_service
from wasjetzt.timeutil import now_local
from wasjetzt.ui.first_run_wizard import FirstRunWizard
from wasjetzt.ui.main_window import MainWindow
from wasjetzt.ui.prompt_window import PromptWindow
from wasjetzt.ui.settings_window import SettingsWindow
from wasjetzt.ui.tray import TrayController

log = logging.getLogger("wasjetzt")


class AppController(QObject):
    _export_done = Signal(object, str)  # (ExportResult, context) — emis din thread-ul de export

    def __init__(self, qapp: QApplication, background: bool):
        super().__init__()
        self.qapp = qapp
        self.background = background
        self.manager = SettingsManager(paths.settings_file())
        self.settings = self.manager.load()
        set_language(self.settings.language)
        self.db = Database(paths.database_file(), paths.backups_dir())
        self.picker = QuestionPicker(last_id=self.db.last_question_id())
        self._current_question: Question | None = None
        self._current_lang: str = normalize_language(self.settings.question_language)

        self.answers = AnswerService(self.db)
        self.exporter = ExportService(self.db, lambda: self.settings.export_directory)
        self.startup = get_startup_service()
        self.core = SchedulerCore(self.settings.interval_minutes, self.settings.on_dismiss,
                                  self.settings.retry_minutes)
        self.icon = QIcon(str(paths.resource_path("app.png")))
        self.qapp.setWindowIcon(self.icon)

        self.prompt = PromptWindow()
        self.prompt.submitted.connect(self._on_submitted)
        self.prompt.dismissed.connect(self._on_dismissed)
        self.main = MainWindow(self.icon, self._main_info)
        self.main.settings_requested.connect(self.open_settings)
        self.main.export_requested.connect(self.export_now)
        self.main.prompt_requested.connect(lambda: self.show_prompt("manual"))
        self.main.pause_toggled.connect(self._toggle_pause)
        self.main.quit_requested.connect(self.quit_safely)
        self.settings_window = SettingsWindow()
        self.settings_window.settings_saved.connect(self._apply_settings)

        self.tray = TrayController(self.icon)
        self.tray.open_app.connect(self.open_main)
        self.tray.open_settings.connect(self.open_settings)
        self.tray.language_selected.connect(self.set_question_language)
        self.tray.show_prompt.connect(lambda: self.show_prompt("manual"))
        self.tray.export_now.connect(self.export_now)
        self.tray.open_export_dir.connect(self.open_export_dir)
        self.tray.quit_requested.connect(self.quit_safely)
        self.tray_available = TrayController.is_available()
        self.main.tray_available = self.tray_available
        if self.tray_available:
            self.tray.set_language_checked(self._current_lang)

        self.timer = QTimer(self)
        self.timer.setInterval(TICK_SECONDS * 1000)
        self.timer.timeout.connect(self._on_tick)
        self._export_done.connect(self._on_export_done)
        self._export_running = False
        self._quitting = False
        self._exit_pending = False
        self._wizard_done = False
        self._shown_at = None
        if hasattr(self.qapp, "commitDataRequest"):
            self.qapp.commitDataRequest.connect(self._on_session_end)

    # ---------- pornire ----------
    def start(self) -> bool:
        """False dacă aplicația trebuie să se închidă (wizard anulat)."""
        if not self.settings.configured or self.manager.first_run or self.manager.load_error:
            if not self._run_wizard():
                self.db.close()
                return False
        else:
            self._sync_startup_entry()
        if self.tray_available:
            self.tray.show()
        else:
            log.warning("System tray indisponibil; fereastra principală rămâne vizibilă.")
        self.timer.start()
        self._recover_unexported()
        first_run_just_finished = self._wizard_done
        if not self.tray_available or (not self.background and not first_run_just_finished) \
                or not self.settings.start_minimized:
            self.open_main()
        elif first_run_just_finished and self.tray_available:
            self.tray.notify(tr("tray.running_background"))
        return True

    def _run_wizard(self) -> bool:
        wizard = FirstRunWizard(self.settings, self.startup.is_supported())
        wizard.setWindowIcon(self.icon)
        if not wizard.exec():
            return False  # neconfigurat: wizard-ul reapare la următoarea pornire
        chosen = wizard.result_settings()
        try:
            self.manager.save(chosen)
        except (SettingsError, OSError) as exc:
            QMessageBox.critical(None, tr("settings.title"), tr("settings.save_failed", error=exc))
            return False
        self.settings = chosen
        self._current_lang = normalize_language(chosen.question_language)
        if self.tray_available:
            self.tray.set_language_checked(self._current_lang)
        self._apply_startup(chosen.start_with_system)
        self.core.set_interval(chosen.interval_minutes)
        self._wizard_done = True
        return True

    # ---------- întrebarea ----------
    def _on_tick(self) -> None:
        if self.core.tick():
            self._present_prompt()

    def show_prompt(self, source: str = "manual") -> None:
        if self.prompt.isVisible():
            self.prompt.raise_()
            self.prompt.activateWindow()
            return
        if self.core.begin_prompt(source):
            self._present_prompt()

    def _present_prompt(self) -> None:
        self._shown_at = now_local()
        self._current_question = self.picker.next()
        self._current_lang = normalize_language(self.settings.question_language)
        q_text = text_for(self._current_question, self._current_lang)
        self.prompt.show_prompt(q_text, self._current_lang)

    def _on_submitted(self, text: str) -> None:
        scheduled = None
        if self.core.scheduled_for:
            scheduled = datetime.fromtimestamp(self.core.scheduled_for).astimezone()
        q_id = self._current_question.id if self._current_question else None
        q_text = text_for(self._current_question, self._current_lang) if self._current_question else None
        q_lang = self._current_lang
        try:
            self.answers.save(
                text,
                prompt_shown_at=self._shown_at,
                scheduled_for=scheduled,
                source=self.core.prompt_source or "manual",
                question_id=q_id,
                question_text=q_text,
                question_language=q_lang,
            )
        except EmptyAnswerError:
            self.prompt.show_error(prompt_tr(self._current_lang, "empty"))
            return
        except Exception as exc:  # baza de date indisponibilă: fereastra rămâne deschisă, textul nu se pierde
            log.exception("Salvarea răspunsului a eșuat")
            self.prompt.show_error(tr("prompt.save_error", error=exc))
            return
        self.core.end_prompt(answered=True)
        self.prompt.accept_saved()
        if self.settings.show_confirmation_notifications and self.tray_available:
            self.tray.notify(tr("prompt.saved"))
        self.main.refresh()

    def _on_dismissed(self) -> None:
        self.core.end_prompt(answered=False)  # nicio înregistrare goală

    # ---------- ferestre ----------
    def open_main(self) -> None:
        self.main.show_and_raise()

    def open_settings(self) -> None:
        self.settings_window.load_from(self.settings, self.startup.is_enabled())
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def open_export_dir(self) -> None:
        directory = self.settings.export_directory
        if directory and Path(directory).is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(directory))
        else:
            QMessageBox.warning(None, tr("settings.title"), tr("dir.missing"))

    def _toggle_pause(self) -> None:
        self.core.resume() if self.core.paused else self.core.pause()
        self.main.refresh()

    def _main_info(self) -> dict:
        latest = [(r.created_at_local[:19].replace("T", " "), r.answer) for r in self.db.list_answers(10)]
        return {"paused": self.core.paused, "next_due": self.core.next_due, "total": self.db.count_answers(),
                "pending": self.db.count_unexported(), "latest": latest}

    # ---------- setări ----------
    def set_question_language(self, code: str) -> None:
        from wasjetzt.questions import LANGUAGES
        if code not in LANGUAGES:
            return
        new_settings = replace(self.settings, question_language=code)
        try:
            self.manager.save(new_settings)
        except (SettingsError, OSError) as exc:
            log.warning("Nu am putut salva limba întrebărilor: %s", exc)
            return
        self.settings = new_settings
        self._current_lang = code
        if self.tray_available:
            self.tray.set_language_checked(code)
        self.settings_window.set_question_language(code)

    def _apply_settings(self, new: Settings) -> None:
        wanted_autostart = new.start_with_system
        actual = self._apply_startup(wanted_autostart)
        new = replace(new, start_with_system=actual, configured=True)
        try:
            self.manager.save(new)
        except (SettingsError, OSError) as exc:
            QMessageBox.warning(None, tr("settings.title"), tr("settings.save_failed", error=exc))
            return
        interval_changed = new.interval_minutes != self.settings.interval_minutes
        self.settings = new
        self._current_lang = normalize_language(new.question_language)
        if self.tray_available:
            self.tray.set_language_checked(self._current_lang)
        if interval_changed:
            self.core.set_interval(new.interval_minutes)
        self.core.configure_dismiss(new.on_dismiss, new.retry_minutes)
        self.main.refresh()
        if new.show_confirmation_notifications and self.tray_available:
            self.tray.notify(tr("settings.saved"))

    def _apply_startup(self, enabled: bool) -> bool:
        """Aplică pornirea automată și returnează starea REALĂ rezultată (nu pretinde succes)."""
        if not self.startup.is_supported():
            if enabled:
                log.info("Pornirea automată nu este disponibilă pe acest sistem.")
            return False
        try:
            self.startup.enable() if enabled else self.startup.disable()
        except StartupError as exc:
            QMessageBox.warning(None, tr("settings.title"), tr("settings.startup_failed", error=exc))
        return self.startup.is_enabled()

    def _sync_startup_entry(self) -> None:
        """Repară intrarea de startup dacă aplicația a fost mutată/reinstalată."""
        if not (self.settings.start_with_system and self.startup.is_supported()):
            return
        try:
            up_to_date = getattr(self.startup, "is_up_to_date", lambda: True)()
            if not up_to_date:
                self.startup.enable()
        except StartupError:
            log.warning("Nu am putut repara intrarea de startup.")

    # ---------- export ----------
    def export_now(self, context: str = "manual") -> None:
        self._start_export(context)

    def _recover_unexported(self) -> None:
        if self.db.count_unexported() and self.settings.export_directory:
            self._start_export("startup")

    def _start_export(self, context: str) -> None:
        if self._export_running:
            return
        self._export_running = True

        def work() -> None:
            try:
                result = self.exporter.export()
            except Exception as exc:  # nu lăsa thread-ul să moară fără semnal
                log.exception("Export neașteptat")
                result = ExportResult("error", error=str(exc))
            self._export_done.emit(result, context)

        threading.Thread(target=work, name="wasjetzt-export", daemon=False).start()

    def _on_export_done(self, result: ExportResult, context: str) -> None:
        self._export_running = False
        if context == "exit":
            self._finish_exit(result)
            return
        if self._exit_pending:
            self._exit_pending = False
            self._start_export("exit")
            return
        if result.status == "ok":
            key = "export.startup_recovered" if context == "startup" else "export.ok"
            if self.tray_available:
                self.tray.notify(tr(key, count=result.count, path=result.path))
        elif result.status == "nothing":
            if context == "manual" and self.tray_available:
                self.tray.notify(tr("export.nothing"))
        else:
            if self.tray_available:
                self.tray.notify(tr("export.failed", error=result.error))
            if context == "manual":
                QMessageBox.warning(None, tr("settings.title"), tr("export.failed", error=result.error))
        self.main.refresh()

    # ---------- ieșire sigură ----------
    def quit_safely(self) -> None:
        if self._quitting:
            return
        self._quitting = True
        self.timer.stop()
        self.prompt.close_silently()
        self.main.hide()
        if self.tray_available:
            self.tray.notify(tr("export.exiting"))
        if self._export_running:
            self._exit_pending = True  # pornește exportul final imediat ce se termină cel curent
        else:
            self._start_export("exit")

    def _finish_exit(self, result: ExportResult) -> None:
        if result.status in ("ok", "nothing"):
            self._shutdown()
            return
        box = QMessageBox(QMessageBox.Icon.Warning, tr("settings.title"), tr("export.failed", error=result.error))
        retry = box.addButton(tr("export.retry"), QMessageBox.ButtonRole.AcceptRole)
        other = box.addButton(tr("export.choose_other"), QMessageBox.ButtonRole.ActionRole)
        leave = box.addButton(tr("export.quit_anyway"), QMessageBox.ButtonRole.DestructiveRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is retry:
            self._start_export("exit")
        elif clicked is other:
            chosen = QFileDialog.getExistingDirectory(None, tr("settings.export_dir"),
                                                      self.settings.export_directory or str(Path.home()))
            if chosen:
                new = replace(self.settings, export_directory=chosen)
                try:
                    self.manager.save(new)
                    self.settings = new
                except (SettingsError, OSError):
                    pass
            self._start_export("exit")
        elif clicked is leave:
            self._shutdown()  # datele rămân în SQLite și se exportă la următoarea pornire

    def _on_session_end(self, manager=None) -> None:
        """Oprirea/deconectarea Windows: export sincron, best-effort, fără dialoguri."""
        if self._quitting:
            return
        self._quitting = True
        self.timer.stop()
        try:
            self.exporter.export()
        except Exception:
            log.exception("Export la închiderea sesiunii a eșuat")
        self._shutdown()

    def _shutdown(self) -> None:
        self.tray.hide()
        try:
            self.db.close()
        except Exception:
            pass
        self.qapp.quit()
