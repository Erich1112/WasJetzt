"""Fereastra principală: stare, următoarea întrebare, statistici, ultimele răspunsuri."""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (QFormLayout, QHBoxLayout, QLabel, QListWidget, QMainWindow, QPushButton,
                               QVBoxLayout, QWidget)

from wasjetzt.i18n import tr


class MainWindow(QMainWindow):
    settings_requested = Signal()
    export_requested = Signal()
    prompt_requested = Signal()
    pause_toggled = Signal()
    quit_requested = Signal()

    def __init__(self, icon, provider):
        """provider() -> dict(paused, next_due(float|None), total, pending, latest[list[(str,str)]])."""
        super().__init__()
        self._provider = provider
        self.tray_available = True
        self.setWindowTitle(tr("main.title"))
        self.setWindowIcon(icon)
        self.setMinimumSize(460, 380)

        self.status = QLabel()
        self.next_due = QLabel()
        self.total = QLabel()
        self.pending = QLabel()
        form = QFormLayout()
        form.addRow(tr("main.status"), self.status)
        form.addRow(tr("main.next"), self.next_due)
        form.addRow(tr("main.total"), self.total)
        form.addRow(tr("main.pending_export"), self.pending)

        self.latest = QListWidget()
        self.latest.setAccessibleName(tr("main.latest"))

        self.pause_button = QPushButton()
        row = QHBoxLayout()
        buttons = [
            (self.pause_button, self.pause_toggled),
            (QPushButton(tr("main.prompt_now")), self.prompt_requested),
            (QPushButton(tr("main.settings")), self.settings_requested),
            (QPushButton(tr("main.export")), self.export_requested),
            (QPushButton(tr("main.quit")), self.quit_requested),
        ]
        for button, signal in buttons:
            button.clicked.connect(lambda _c=False, s=signal: s.emit())
            row.addWidget(button)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.addLayout(form)
        layout.addWidget(QLabel(tr("main.latest")))
        layout.addWidget(self.latest, 1)
        layout.addLayout(row)
        self.setCentralWidget(root)

        self._timer = QTimer(self)
        self._timer.setInterval(5000)
        self._timer.timeout.connect(self.refresh)

    def refresh(self) -> None:
        info = self._provider()
        self.status.setText(tr("main.status_paused") if info["paused"] else tr("main.status_running"))
        self.pause_button.setText(tr("main.resume") if info["paused"] else tr("main.pause"))
        due = info["next_due"]
        self.next_due.setText(datetime.fromtimestamp(due).strftime("%Y-%m-%d %H:%M:%S")
                              if due and not info["paused"] else tr("main.next_none"))
        self.total.setText(str(info["total"]))
        self.pending.setText(str(info["pending"]))
        self.latest.clear()
        for stamp, text in info["latest"]:
            self.latest.addItem(f"{stamp}  —  {text.splitlines()[0] if text else ''}")

    def show_and_raise(self) -> None:
        self.refresh()
        self._timer.start()
        self.show()
        self.raise_()
        self.activateWindow()

    def hideEvent(self, event) -> None:
        self._timer.stop()
        super().hideEvent(event)

    def closeEvent(self, event) -> None:
        # „X” ascunde fereastra în fundal; ieșirea reală se face din „Ieșire”.
        # Fără system tray fereastra nu se ascunde (ar deveni inaccesibilă), ci se minimizează.
        event.ignore()
        if self.tray_available:
            self.hide()
        else:
            self.showMinimized()
