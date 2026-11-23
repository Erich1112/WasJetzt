"""Pictograma din zona de notificări și meniul ei."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from wasjetzt.i18n import tr


class TrayController(QObject):
    open_app = Signal()
    open_settings = Signal()
    show_prompt = Signal()
    export_now = Signal()
    open_export_dir = Signal()
    quit_requested = Signal()
    language_selected = Signal(str)

    def __init__(self, icon: QIcon, parent=None):
        super().__init__(parent)
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip(tr("app.name"))
        self.menu = QMenu()

        open_act = QAction(tr("tray.open"), self.menu)
        open_act.triggered.connect(lambda _checked=False: self.open_app.emit())
        self.menu.addAction(open_act)

        settings_act = QAction(tr("tray.settings"), self.menu)
        settings_act.triggered.connect(lambda _checked=False: self.open_settings.emit())
        self.menu.addAction(settings_act)

        self.lang_menu = QMenu(tr("tray.language"), self.menu)
        self.lang_group = QActionGroup(self)
        self.lang_group.setExclusive(True)
        self._lang_actions: dict[str, QAction] = {}
        for code, name in (("de", "Deutsch"), ("es", "Español")):
            act = QAction(name, self.lang_menu)
            act.setCheckable(True)
            self.lang_group.addAction(act)
            self.lang_menu.addAction(act)
            self._lang_actions[code] = act
            act.triggered.connect(lambda _checked=False, c=code: self.language_selected.emit(c))
        self.menu.addMenu(self.lang_menu)

        prompt_act = QAction(tr("tray.prompt_now"), self.menu)
        prompt_act.triggered.connect(lambda _checked=False: self.show_prompt.emit())
        self.menu.addAction(prompt_act)

        export_act = QAction(tr("tray.export_now"), self.menu)
        export_act.triggered.connect(lambda _checked=False: self.export_now.emit())
        self.menu.addAction(export_act)

        open_export_act = QAction(tr("tray.open_export_dir"), self.menu)
        open_export_act.triggered.connect(lambda _checked=False: self.open_export_dir.emit())
        self.menu.addAction(open_export_act)

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

    def set_language_checked(self, code: str) -> None:
        act = self._lang_actions.get(code)
        if act:
            act.setChecked(True)

    def notify(self, message: str, title: str = "WasJetzt") -> None:
        self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 4000)

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_app.emit()
