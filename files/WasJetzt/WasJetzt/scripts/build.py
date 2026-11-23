"""Construiește executabilul Windows cu PyInstaller: dist/WasJetzt/WasJetzt.exe

Rulare (din rădăcina proiectului, în mediul virtual): python scripts/build.py
"""
import os
import sys
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
RES = SRC / "wasjetzt" / "resources"


def main() -> int:
    if not (RES / "app.ico").exists():
        print("Lipsește app.ico. Rulează: python scripts/make_icon.py")
        return 1
    sep = os.pathsep  # ';' pe Windows
    PyInstaller.__main__.run([
        str(ROOT / "run_wasjetzt.py"),
        "--name", "WasJetzt",
        "--noconfirm", "--clean",
        "--windowed",
        "--icon", str(RES / "app.ico"),
        "--paths", str(SRC),
        "--add-data", f"{RES}{sep}wasjetzt/resources",
        "--hidden-import", "wasjetzt.os_integration.windows_startup",
        "--hidden-import", "wasjetzt.os_integration.windows_mutex",
        "--collect-data", "tzdata",
        "--collect-submodules", "tzlocal",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
    ])
    exe = ROOT / "dist" / "WasJetzt" / "WasJetzt.exe"
    if not exe.exists():
        print("Build eșuat: nu s-a creat", exe)
        return 1
    print("\nExecutabil creat:", exe)
    return 0


if __name__ == "__main__":
    sys.exit(main())
