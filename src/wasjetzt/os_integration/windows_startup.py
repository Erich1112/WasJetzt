"""Pornire automată pe Windows prin HKCU\\...\\Run (per utilizator, fără administrator)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from wasjetzt.services.startup_service import StartupError, StartupService

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "WasJetzt"
BACKGROUND_ARG = "--background"


class WinRegistry:
    """Acces real la registru (winreg importat doar pe Windows)."""

    def get(self, key_path: str, name: str) -> str | None:
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, name)
                return str(value)
        except FileNotFoundError:
            return None

    def set(self, key_path: str, name: str, value: str) -> None:
        import winreg

        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)

    def delete(self, key_path: str, name: str) -> None:
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, name)
        except FileNotFoundError:
            pass


def build_command(frozen: bool | None = None, executable: str | None = None) -> str:
    """Comanda cu calea reală și ghilimelele corecte."""
    frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    executable = executable or sys.executable
    if frozen:
        return f'"{executable}" {BACKGROUND_ARG}'
    pythonw = Path(executable).with_name("pythonw.exe")
    interpreter = str(pythonw) if pythonw.exists() else executable
    return f'"{interpreter}" -m wasjetzt {BACKGROUND_ARG}'


class WindowsStartupService(StartupService):
    def __init__(self, registry=None, command: str | None = None):
        self._registry = registry or WinRegistry()
        self._command = command

    @property
    def command(self) -> str:
        return self._command or build_command()

    def is_supported(self) -> bool:
        return True

    def is_enabled(self) -> bool:
        try:
            return self._registry.get(RUN_KEY, VALUE_NAME) is not None
        except OSError:
            return False

    def is_up_to_date(self) -> bool:
        try:
            return self._registry.get(RUN_KEY, VALUE_NAME) == self.command
        except OSError:
            return False

    def enable(self) -> None:
        try:
            self._registry.set(RUN_KEY, VALUE_NAME, self.command)
        except OSError as exc:
            raise StartupError(str(exc)) from exc
        if not self.is_enabled():
            raise StartupError("Intrarea de startup nu a putut fi verificată după scriere.")

    def disable(self) -> None:
        try:
            self._registry.delete(RUN_KEY, VALUE_NAME)
        except OSError as exc:
            raise StartupError(str(exc)) from exc
        if self.is_enabled():
            raise StartupError("Intrarea de startup nu a putut fi eliminată.")
