"""Mutex Windows folosit de instalator (AppMutex) ca să detecteze o instanță în execuție."""
from __future__ import annotations

import sys

MUTEX_NAME = "WasJetzt_SingleInstance_Mutex"
_handle = None


def create_app_mutex() -> None:
    global _handle
    if sys.platform != "win32":
        return
    try:
        import ctypes

        _handle = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    except Exception:  # nu este critic; single-instance real este asigurat de QLocalServer
        _handle = None
