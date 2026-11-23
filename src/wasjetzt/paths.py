"""Locații pentru date, configurare și resurse. Nu scrie niciodată lângă executabil."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from wasjetzt import APP_NAME


def _override() -> Path | None:
    value = os.environ.get("WASJETZT_HOME")
    return Path(value) if value else None


def config_dir() -> Path:
    override = _override()
    if override:
        return override / "config"
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_NAME


def data_dir() -> Path:
    override = _override()
    if override:
        return override / "data"
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP_NAME


def settings_file() -> Path:
    return config_dir() / "settings.json"


def database_file() -> Path:
    return data_dir() / "wasjetzt.db"


def backups_dir() -> Path:
    return data_dir() / "backups"


def logs_dir() -> Path:
    return data_dir() / "logs"


def default_export_dir() -> Path:
    return Path.home() / "Documents" / APP_NAME


def resource_path(name: str) -> Path:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / "wasjetzt" / "resources" / name
    return Path(__file__).resolve().parent / "resources" / name
