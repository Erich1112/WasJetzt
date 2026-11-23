"""Pictograma din zona de notificări și meniul ei."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from wasjetzt.i18n import tr


class TrayController(QObject):
    open_app = Signal()
    open_settings = Signal()
    show_prompt = Signal()
    export_now = Signal()
    open_export_dir = Signal()
    quit_requested = Signal()

    def __init__(self, icon: QIcon, parent=None):
        super().__init__(parent)
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip(tr("app.name"))
        self.menu = QMenu()
        for key, signal in (
            ("tray.open", self.open_app),
            ("tray.settings", self.open_settings),
            ("tray.prompt_now", self.show_prompt),
            ("tray.export_now", self.export_now),
            ("tray.open_export_dir", self.open_export_dir),
        ):
            action = QAction(tr(key), self.menu)
            action.triggered.connect(lambda _checked=False, s=signal: s.emit())
            self.menu.addAction(action)
        self.menu.addSeparator()
        quit_action = QAction(tr("tray.quit"), self.menu)
        quit_action.triggered.connect(lambda _checked=False: self.quit_requested.emit())
        self.menu.addAction(quit_action)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_activated)

    @staticmethod
    def is_available() -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    def show(self) -> None:
        self.tray.show()

    def hide(self) -> None:
        self.tray.hide()

    def notify(self, message: str, title: str = "WasJetzt") -> None:
        self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 4000)

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_app.emit()
