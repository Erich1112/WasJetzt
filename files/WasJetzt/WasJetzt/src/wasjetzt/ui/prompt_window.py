"""Fereastra mică din dreapta-jos cu întrebarea „Was machst du jetzt?”."""
from __future__ import annotations

import time

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from wasjetzt import QUESTION
from wasjetzt.i18n import tr
from wasjetzt.ui.geometry import bottom_right_position

MARGIN = 20
ENTER_GUARD_SECONDS = 0.8  # Enter apăsat chiar la apariție (din altă aplicație) nu trimite nimic


class AnswerEdit(QPlainTextEdit):
    submit_requested = Signal()

    def keyPressEvent(self, event) -> None:
        enter = event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
        if enter and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.submit_requested.emit()
            return
        super().keyPressEvent(event)


class PromptWindow(QWidget):
    submitted = Signal(str)
    dismissed = Signal()

    def __init__(self) -> None:
        flags = (Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint
                 | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)
        super().__init__(None, flags)
        self.setWindowTitle(tr("prompt.title"))
        self.setMinimumSize(320, 170)
        self.resize(360, 180)
        self._handled = True
        self._shown_at = 0.0
        self._watched_screen = None

        self.question = QLabel(QUESTION)
        font = self.question.font()
        font.setPointSize(font.pointSize() + 3)
        font.setBold(True)
        self.question.setFont(font)
        self.question.setAccessibleName(QUESTION)

        self.edit = AnswerEdit()
        self.edit.setPlaceholderText(tr("prompt.placeholder"))
        self.edit.setAccessibleName(tr("prompt.placeholder"))
        self.edit.setTabChangesFocus(True)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #b00020;")
        self.error_label.setAccessibleName("validation")

        self.save_button = QPushButton(tr("prompt.save"))
        self.save_button.setDefault(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.question)
        layout.addWidget(self.edit, 1)
        layout.addWidget(self.error_label)
        layout.addWidget(self.save_button)
        self.setTabOrder(self.edit, self.save_button)

        self.save_button.clicked.connect(self._submit)
        self.edit.submit_requested.connect(self._on_enter)
        self.edit.textChanged.connect(lambda: self.error_label.setText(""))

        app = QGuiApplication.instance()
        app.primaryScreenChanged.connect(lambda *_: self._on_screen_change())
        app.screenAdded.connect(lambda *_: self._on_screen_change())
        app.screenRemoved.connect(lambda *_: self._on_screen_change())

    # --- API folosit de controller ---
    def show_prompt(self) -> None:
        self.edit.clear()
        self.error_label.setText("")
        self._handled = False
        self._shown_at = time.monotonic()
        self._on_screen_change()
        self.reposition()
        self.show()
        self.reposition()
        QTimer.singleShot(0, self.reposition)
        self.raise_()
        self.activateWindow()
        self.edit.setFocus()

    def accept_saved(self) -> None:
        """Salvarea a reușit: închide fereastra fără a o trata drept „ignorată”."""
        self._handled = True
        self.close()

    def close_silently(self) -> None:
        self._handled = True
        self.close()

    def show_error(self, message: str) -> None:
        self.error_label.setText(message)

    # --- interne ---
    def _on_enter(self) -> None:
        if time.monotonic() - self._shown_at >= ENTER_GUARD_SECONDS:
            self._submit()

    def _submit(self) -> None:
        text = self.edit.toPlainText().strip()
        if not text:
            self.error_label.setText(tr("prompt.empty"))
            self.edit.setFocus()
            return
        self.submitted.emit(text)

    def closeEvent(self, event) -> None:
        if not self._handled:
            self._handled = True
            self.dismissed.emit()
        event.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def reposition(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        avail = screen.availableGeometry()
        size = self.frameGeometry().size() if self.isVisible() else self.sizeHint().expandedTo(self.size())
        x, y = bottom_right_position(avail.x(), avail.y(), avail.width(), avail.height(),
                                     size.width(), size.height(), MARGIN)
        self.move(x, y)

    def _on_screen_change(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if self._watched_screen is not None:
            try:
                self._watched_screen.availableGeometryChanged.disconnect(self._reposition_if_visible)
            except (RuntimeError, TypeError):
                pass
        self._watched_screen = screen
        if screen is not None:
            screen.availableGeometryChanged.connect(self._reposition_if_visible)
        self._reposition_if_visible()

    def _reposition_if_visible(self, *_args) -> None:
        if self.isVisible():
            self.reposition()
