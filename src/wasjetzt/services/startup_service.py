"""Interfață independentă de platformă pentru pornirea automată."""
from __future__ import annotations

import sys
from abc import ABC, abstractmethod


class StartupError(RuntimeError):
    pass


class StartupService(ABC):
    @abstractmethod
    def is_supported(self) -> bool: ...

    @abstractmethod
    def is_enabled(self) -> bool: ...

    @abstractmethod
    def enable(self) -> None:
        """Activează sau repară intrarea de startup. Ridică StartupError la eșec."""

    @abstractmethod
    def disable(self) -> None:
        """Elimină doar intrarea creată de aplicație. Ridică StartupError la eșec."""


class UnsupportedStartupService(StartupService):
    def is_supported(self) -> bool:
        return False

    def is_enabled(self) -> bool:
        return False

    def enable(self) -> None:
        raise StartupError("Pornirea automată nu este implementată pe acest sistem de operare.")

    def disable(self) -> None:
        return None


def get_startup_service() -> StartupService:
    if sys.platform == "win32":
        from wasjetzt.os_integration.windows_startup import WindowsStartupService

        return WindowsStartupService()
    return UnsupportedStartupService()
