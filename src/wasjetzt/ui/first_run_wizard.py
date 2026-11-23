"""Wizard-ul primei porniri. Dacă este închis înainte de „Finalizează”, aplicația rămâne neconfigurată."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtWidgets import (QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QRadioButton, QSpinBox, QVBoxLayout, QWizard, QWizardPage)

from wasjetzt.config.settings import MAX_INTERVAL, MIN_INTERVAL, Settings
from wasjetzt.i18n import tr
from wasjetzt.paths import default_export_dir
from wasjetzt.ui.settings_window import ask_and_prepare_directory


def _label(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    return label


class _WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle(tr("wizard.welcome_title"))
        layout = QVBoxLayout(self)
        layout.addWidget(_label(tr("wizard.welcome_text")))


class _LanguagePage(QWizardPage):
    def __init__(self, initial_lang: str = "de"):
        super().__init__()
        self.setTitle(tr("wizard.language_title"))
        layout = QVBoxLayout(self)
        layout.addWidget(_label(tr("wizard.language_text")))
        self.radio_de = QRadioButton("Deutsch")
        self.radio_es = QRadioButton("Español")
        if initial_lang == "es":
            self.radio_es.setChecked(True)
        else:
            self.radio_de.setChecked(True)
        layout.addWidget(self.radio_de)
        layout.addWidget(self.radio_es)

    def selected_language(self) -> str:
        return "es" if self.radio_es.isChecked() else "de"


class _FolderPage(QWizardPage):
    def __init__(self, initial_dir: str, initial_interval: int):
        super().__init__()
        self.setTitle(tr("wizard.folder_title"))
        self.dir_edit = QLineEdit(initial_dir)
        self.dir_edit.setAccessibleName(tr("settings.export_dir"))
        browse = QPushButton(tr("settings.choose_dir"))
        browse.clicked.connect(self._browse)
        row = QHBoxLayout()
        row.addWidget(self.dir_edit, 1)
        row.addWidget(browse)
        self.interval = QSpinBox()
        self.interval.setRange(MIN_INTERVAL, MAX_INTERVAL)
        self.interval.setValue(initial_interval)
        self.interval.setSuffix(tr("settings.minutes_suffix"))
        self.interval.setAccessibleName(tr("wizard.interval_label"))
        layout = QVBoxLayout(self)
        layout.addWidget(_label(tr("wizard.folder_text")))
        layout.addLayout(row)
        layout.addWidget(_label(tr("wizard.interval_label")))
        layout.addWidget(self.interval)

    def _browse(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, tr("settings.export_dir"),
                                                  self.dir_edit.text() or str(Path.home()))
        if chosen:
            self.dir_edit.setText(chosen)

    def validatePage(self) -> bool:
        return ask_and_prepare_directory(self, self.dir_edit.text().strip())


class _FinishPage(QWizardPage):
    def __init__(self, autostart_supported: bool):
        super().__init__()
        self.setTitle(tr("wizard.finish_title"))
        self.autostart = QCheckBox(tr("wizard.autostart"))
        self.autostart.setChecked(autostart_supported)
        self.autostart.setEnabled(autostart_supported)
        layout = QVBoxLayout(self)
        layout.addWidget(_label(tr("wizard.finish_text")))
        layout.addWidget(self.autostart)


class FirstRunWizard(QWizard):
    def __init__(self, base: Settings, autostart_supported: bool, parent=None):
        super().__init__(parent)
        self._base = base
        self.setWindowTitle(tr("wizard.title"))
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        initial_dir = base.export_directory or str(default_export_dir())
        self._lang_page = _LanguagePage(base.question_language)
        self._folder = _FolderPage(initial_dir, base.interval_minutes)
        self._finish = _FinishPage(autostart_supported)
        self.addPage(_WelcomePage())
        self.addPage(self._lang_page)
        self.addPage(self._folder)
        self.addPage(self._finish)
        self.setButtonText(QWizard.WizardButton.NextButton, tr("wizard.next"))
        self.setButtonText(QWizard.WizardButton.BackButton, tr("wizard.back"))
        self.setButtonText(QWizard.WizardButton.FinishButton, tr("wizard.finish"))
        self.setButtonText(QWizard.WizardButton.CancelButton, tr("wizard.cancel"))

    def result_settings(self) -> Settings:
        return replace(
            self._base,
            configured=True,
            question_language=self._lang_page.selected_language(),
            export_directory=self._folder.dir_edit.text().strip(),
            interval_minutes=self._folder.interval.value(),
            start_with_system=self._finish.autostart.isChecked(),
        )
