"""O singură instanță: a doua pornire trezește prima (arată fereastra principală) și iese."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class SingleInstance(QObject):
    activated = Signal()

    def __init__(self, key: str = "WasJetzt-single-instance-v1", parent=None):
        super().__init__(parent)
        self._key = key
        self._server: QLocalServer | None = None

    def acquire(self) -> bool:
        """True dacă aceasta este prima instanță; False dacă una rulează deja (a fost anunțată)."""
        probe = QLocalSocket()
        probe.connectToServer(self._key)
        if probe.waitForConnected(400):
            probe.write(b"show")
            probe.flush()
            probe.waitForBytesWritten(400)
            probe.disconnectFromServer()
            return False
        QLocalServer.removeServer(self._key)  # elimină un socket rămas de la o închidere forțată
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_connection)
        return self._server.listen(self._key)

    def _on_connection(self) -> None:
        while self._server and self._server.hasPendingConnections():
            connection = self._server.nextPendingConnection()
            connection.disconnected.connect(connection.deleteLater)
            connection.disconnectFromServer()
            self.activated.emit()
