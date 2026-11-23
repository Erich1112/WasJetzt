"""Fereastra de setări (tab-uri, ca să poți adăuga ușor opțiuni noi)."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
                               QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox,
                               QTabWidget, QVBoxLayout, QWidget)

from wasjetzt.config.settings import (MAX_INTERVAL, MAX_RETRY, MIN_INTERVAL, MIN_RETRY, Settings, validate)
from wasjetzt.i18n import tr
from wasjetzt.services.export_service import check_directory_writable


def ask_and_prepare_directory(parent: QWidget, directory: str) -> bool:
    """Verifică directorul; dacă lipsește, cere confirmarea și îl creează. True dacă e utilizabil."""
    if not directory.strip():
        QMessageBox.warning(parent, tr("settings.title"), tr("settings.dir_required"))
        return False
    path = Path(directory)
    if not path.exists():
        answer = QMessageBox.question(parent, tr("settings.title"), tr("settings.dir_create_q", path=directory))
        if answer != QMessageBox.StandardButton.Yes:
            return False
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.warning(parent, tr("settings.title"),
                                tr("settings.dir_error", error=exc.strerror or str(exc)))
            return False
    problem = check_directory_writable(path)
    if problem:
        QMessageBox.warning(parent, tr("settings.title"), tr("settings.dir_error", error=problem))
        return False
    return True


class SettingsWindow(QDialog):
    settings_saved = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("settings.title"))
        self.setMinimumWidth(480)
        self._current = Settings()

        self.dir_edit = QLineEdit()
        self.dir_edit.setAccessibleName(tr("settings.export_dir"))
        browse = QPushButton(tr("settings.choose_dir"))
        browse.clicked.connect(self._browse)
        dir_row = QHBoxLayout()
        dir_row.addWidget(self.dir_edit, 1)
        dir_row.addWidget(browse)

        self.interval = QSpinBox()
        self.interval.setRange(MIN_INTERVAL, MAX_INTERVAL)
        self.interval.setSuffix(tr("settings.minutes_suffix"))
        self.interval.setAccessibleName(tr("settings.interval"))
        self.autostart = QCheckBox(tr("settings.autostart"))
        self.minimized = QCheckBox(tr("settings.start_minimized"))
        self.notifications = QCheckBox(tr("settings.notifications"))

        general = QWidget()
        form = QFormLayout(general)
        form.addRow(tr("settings.export_dir"), dir_row)
        form.addRow(tr("settings.interval"), self.interval)
        form.addRow(self.autostart)
        form.addRow(self.minimized)
        form.addRow(self.notifications)

        self.question_language = QComboBox()
        self.question_language.addItem("Deutsch", "de")
        self.question_language.addItem("Español", "es")
        self.question_language.setAccessibleName(tr("settings.question_language"))

        self.on_dismiss = QComboBox()
        self.on_dismiss.addItem(tr("settings.on_dismiss_wait"), "wait_next_interval")
        self.on_dismiss.addItem(tr("settings.on_dismiss_retry"), "retry_soon")
        self.on_dismiss.setAccessibleName(tr("settings.on_dismiss"))
        self.retry = QSpinBox()
        self.retry.setRange(MIN_RETRY, MAX_RETRY)
        self.retry.setSuffix(tr("settings.minutes_suffix"))
        self.on_dismiss.currentIndexChanged.connect(self._sync_retry_enabled)
        prompts = QWidget()
        pform = QFormLayout(prompts)
        pform.addRow(tr("settings.question_language"), self.question_language)
        pform.addRow(tr("settings.on_dismiss"), self.on_dismiss)
        pform.addRow(tr("settings.retry_minutes"), self.retry)

        self.language = QComboBox()
        self.language.addItem("Română", "ro")
        interface = QWidget()
        iform = QFormLayout(interface)
        iform.addRow(tr("settings.language"), self.language)
        iform.addRow(QLabel(tr("settings.language_note")))

        tabs = QTabWidget()
        tabs.addTab(general, tr("settings.tab_general"))
        tabs.addTab(prompts, tr("settings.tab_prompts"))
        tabs.addTab(interface, tr("settings.tab_interface"))

        buttons = QDialogButtonBox()
        save = buttons.addButton(tr("settings.save"), QDialogButtonBox.ButtonRole.AcceptRole)
        save.setDefault(True)
        buttons.addButton(tr("settings.cancel"), QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

    def load_from(self, settings: Settings, autostart_actual: bool) -> None:
        self._current = settings
        self.dir_edit.setText(settings.export_directory)
        self.interval.setValue(settings.interval_minutes)
        self.autostart.setChecked(autostart_actual)  # starea reală din sistem, nu doar din JSON
        self.minimized.setChecked(settings.start_minimized)
        self.notifications.setChecked(settings.show_confirmation_notifications)
        self.question_language.setCurrentIndex(max(0, self.question_language.findData(settings.question_language)))
        self.on_dismiss.setCurrentIndex(max(0, self.on_dismiss.findData(settings.on_dismiss)))
        self.retry.setValue(settings.retry_minutes)
        self._sync_retry_enabled()

    def set_question_language(self, code: str) -> None:
        idx = self.question_language.findData(code)
        if idx >= 0:
            self.question_language.setCurrentIndex(idx)

    def _sync_retry_enabled(self) -> None:
        self.retry.setEnabled(self.on_dismiss.currentData() == "retry_soon")

    def _browse(self) -> None:
        start = self.dir_edit.text() or str(Path.home())
        chosen = QFileDialog.getExistingDirectory(self, tr("settings.export_dir"), start)
        if chosen:
            self.dir_edit.setText(chosen)

    def _save(self) -> None:
        candidate = replace(
            self._current,
            export_directory=self.dir_edit.text().strip(),
            interval_minutes=self.interval.value(),
            start_with_system=self.autostart.isChecked(),
            start_minimized=self.minimized.isChecked(),
            show_confirmation_notifications=self.notifications.isChecked(),
            question_language=self.question_language.currentData(),
            on_dismiss=self.on_dismiss.currentData(),
            retry_minutes=self.retry.value(),
            language=self.language.currentData(),
        )
        errors = validate(candidate)
        if errors:
            QMessageBox.warning(self, tr("settings.title"),
                                tr("settings.invalid", error="; ".join(errors.values())))
            return
        if not ask_and_prepare_directory(self, candidate.export_directory):
            return
        self.settings_saved.emit(candidate)
        self.accept()
